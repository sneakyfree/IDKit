"""
Avatar GPU Worker

Handles avatar generation, lip-sync video creation, and face enhancement.
Models: SadTalker, Wav2Lip, GFPGAN
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

import torch

from worker.base import BaseWorker, Job, WorkerConfig

logger = logging.getLogger(__name__)


class AvatarWorker(BaseWorker):
    """
    GPU worker for avatar and video generation.

    Supported job types:
    - avatar_generate: Generate talking head video from image + audio
    - lip_sync: Sync lips to audio in existing video
    - face_enhance: Enhance face quality in video
    - face_swap: Swap faces between images/videos
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)

        # Models
        self._sadtalker = None
        self._wav2lip = None
        self._gfpgan = None
        self._face_detector = None

    @property
    def worker_type(self) -> str:
        return "avatar"

    def get_supported_job_types(self) -> list[str]:
        return [
            "avatar_generate",
            "lip_sync",
            "face_enhance",
            "face_swap",
            "face_detect",
        ]

    async def load_models(self) -> None:
        """Load avatar generation models."""
        device = self.config.device

        await self.update_progress(0.0, "Loading face detection model...")
        self._face_detector = await self._load_face_detector()

        await self.update_progress(0.2, "Loading SadTalker model...")
        self._sadtalker = await self._load_sadtalker(device)

        await self.update_progress(0.5, "Loading Wav2Lip model...")
        self._wav2lip = await self._load_wav2lip(device)

        await self.update_progress(0.8, "Loading GFPGAN model...")
        self._gfpgan = await self._load_gfpgan(device)

        await self.update_progress(1.0, "All models loaded")

    async def _load_face_detector(self) -> Any:
        """Load face detection model."""
        try:
            from facenet_pytorch import MTCNN

            detector = MTCNN(
                select_largest=True,
                device=self.config.device,
            )
            return detector
        except ImportError:
            logger.warning("facenet_pytorch not available, using fallback")
            return None

    async def _load_sadtalker(self, device: str) -> Any:
        """Load SadTalker model for talking head generation."""
        try:
            # SadTalker loads from HuggingFace
            from sadtalker import SadTalker

            model = SadTalker(
                checkpoint_path=os.path.join(
                    self.config.model_cache_dir, "sadtalker"
                ),
                device=device,
            )
            return model
        except ImportError:
            logger.warning("SadTalker not available")
            return None

    async def _load_wav2lip(self, device: str) -> Any:
        """Load Wav2Lip model for lip syncing."""
        try:
            # Wav2Lip model loading
            from wav2lip import Wav2Lip

            model = Wav2Lip(
                checkpoint_path=os.path.join(
                    self.config.model_cache_dir, "wav2lip"
                ),
                device=device,
            )
            return model
        except ImportError:
            logger.warning("Wav2Lip not available")
            return None

    async def _load_gfpgan(self, device: str) -> Any:
        """Load GFPGAN for face enhancement."""
        try:
            from gfpgan import GFPGANer

            model = GFPGANer(
                model_path=os.path.join(
                    self.config.model_cache_dir, "gfpgan", "GFPGANv1.4.pth"
                ),
                upscale=2,
                arch="clean",
                channel_multiplier=2,
                device=device,
            )
            return model
        except ImportError:
            logger.warning("GFPGAN not available")
            return None

    async def process_job(self, job: Job) -> dict:
        """Process avatar generation job."""
        job_type = job.job_type

        if job_type == "avatar_generate":
            return await self._generate_avatar(job)
        elif job_type == "lip_sync":
            return await self._lip_sync(job)
        elif job_type == "face_enhance":
            return await self._enhance_face(job)
        elif job_type == "face_swap":
            return await self._swap_face(job)
        elif job_type == "face_detect":
            return await self._detect_face(job)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def _generate_avatar(self, job: Job) -> dict:
        """
        Generate talking head video from image and audio.

        Input:
            - source_image: URL or base64 of source face image
            - audio: URL or base64 of audio file
            - params:
                - expression_scale: float (0.5-2.0)
                - pose_style: int (0-45)
                - enhancer: bool
        """
        if not self._sadtalker:
            raise RuntimeError("SadTalker model not loaded")

        input_data = job.input_data
        params = job.params

        await self.update_progress(0.1, "Downloading source image...")
        source_image = await self._download_media(input_data["source_image"])

        await self.update_progress(0.2, "Downloading audio...")
        audio_file = await self._download_media(input_data["audio"])

        await self.update_progress(0.3, "Detecting face...")
        face_info = await self._detect_face_in_image(source_image)

        if not face_info:
            raise ValueError("No face detected in source image")

        await self.update_progress(0.4, "Generating talking head video...")

        # Run SadTalker in thread pool (CPU-bound parts)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.mp4")

            # SadTalker inference
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._sadtalker.generate(
                    source_image=source_image,
                    driven_audio=audio_file,
                    output_path=output_path,
                    expression_scale=params.get("expression_scale", 1.0),
                    pose_style=params.get("pose_style", 0),
                    batch_size=2,
                    preprocess="crop",
                ),
            )

            await self.update_progress(0.8, "Processing complete...")

            # Apply face enhancement if requested
            if params.get("enhancer", True) and self._gfpgan:
                await self.update_progress(0.85, "Enhancing video quality...")
                output_path = await self._enhance_video(output_path, tmp_dir)

            await self.update_progress(0.95, "Uploading result...")

            # Upload result
            video_url = await self._upload_result(output_path, "video/mp4")

        return {
            "video_url": video_url,
            "duration_seconds": result.get("duration", 0),
            "resolution": result.get("resolution", "512x512"),
        }

    async def _lip_sync(self, job: Job) -> dict:
        """
        Sync lips in video to new audio.

        Input:
            - source_video: URL of source video
            - audio: URL of new audio
            - params:
                - face_detector: 'mtcnn' or 'dlib'
                - pads: list of padding values
        """
        if not self._wav2lip:
            raise RuntimeError("Wav2Lip model not loaded")

        input_data = job.input_data
        params = job.params

        await self.update_progress(0.1, "Downloading source video...")
        source_video = await self._download_media(input_data["source_video"])

        await self.update_progress(0.2, "Downloading audio...")
        audio_file = await self._download_media(input_data["audio"])

        await self.update_progress(0.3, "Processing lip sync...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.mp4")

            # Wav2Lip inference
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._wav2lip.inference(
                    face=source_video,
                    audio=audio_file,
                    outfile=output_path,
                    pads=params.get("pads", [0, 10, 0, 0]),
                    resize_factor=1,
                    nosmooth=False,
                ),
            )

            await self.update_progress(0.9, "Uploading result...")
            video_url = await self._upload_result(output_path, "video/mp4")

        return {
            "video_url": video_url,
            "frames_processed": result.get("frames", 0),
        }

    async def _enhance_face(self, job: Job) -> dict:
        """
        Enhance face quality in image or video.

        Input:
            - source: URL of image or video
            - type: 'image' or 'video'
            - params:
                - upscale: int (1-4)
                - bg_upsampler: bool
        """
        if not self._gfpgan:
            raise RuntimeError("GFPGAN model not loaded")

        input_data = job.input_data
        params = job.params
        source_type = input_data.get("type", "image")

        await self.update_progress(0.1, "Downloading source...")
        source_file = await self._download_media(input_data["source"])

        await self.update_progress(0.3, "Enhancing face...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            if source_type == "image":
                output_path = os.path.join(tmp_dir, "enhanced.png")
                result = await self._enhance_image(source_file, output_path, params)
                content_type = "image/png"
            else:
                output_path = await self._enhance_video(source_file, tmp_dir)
                result = {"frames": 0}
                content_type = "video/mp4"

            await self.update_progress(0.9, "Uploading result...")
            url = await self._upload_result(output_path, content_type)

        return {
            "url": url,
            "enhanced": True,
            **result,
        }

    async def _enhance_image(
        self, input_path: str, output_path: str, params: dict
    ) -> dict:
        """Enhance a single image."""
        import cv2

        # Read image
        img = cv2.imread(input_path, cv2.IMREAD_COLOR)

        # Run GFPGAN
        _, _, output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._gfpgan.enhance(
                img,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
                weight=0.5,
            ),
        )

        # Save
        cv2.imwrite(output_path, output)

        return {"enhanced_resolution": f"{output.shape[1]}x{output.shape[0]}"}

    async def _enhance_video(self, input_path: str, tmp_dir: str) -> str:
        """Enhance all faces in video."""
        import cv2

        output_path = os.path.join(tmp_dir, "enhanced.mp4")

        # Read video
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Output writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height * 2))

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Enhance frame
            _, _, enhanced = self._gfpgan.enhance(
                frame,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
            )

            out.write(enhanced)
            frame_idx += 1

            # Update progress periodically
            if frame_idx % 10 == 0:
                progress = 0.3 + (0.6 * frame_idx / total_frames)
                await self.update_progress(progress, f"Enhancing frame {frame_idx}/{total_frames}")

        cap.release()
        out.release()

        return output_path

    async def _swap_face(self, job: Job) -> dict:
        """
        Swap face from source to target.

        Input:
            - source_face: URL of face to use
            - target: URL of target image/video
            - type: 'image' or 'video'
        """
        # Face swap implementation would go here
        # Using libraries like insightface/roop

        raise NotImplementedError("Face swap not yet implemented")

    async def _detect_face(self, job: Job) -> dict:
        """
        Detect faces in image.

        Input:
            - image: URL of image

        Returns:
            - faces: List of detected face bounding boxes
        """
        input_data = job.input_data

        await self.update_progress(0.2, "Downloading image...")
        image_path = await self._download_media(input_data["image"])

        await self.update_progress(0.5, "Detecting faces...")
        faces = await self._detect_face_in_image(image_path)

        return {
            "faces": faces,
            "count": len(faces) if faces else 0,
        }

    async def _detect_face_in_image(self, image_path: str) -> list:
        """Detect faces in an image."""
        import cv2
        from PIL import Image

        if self._face_detector:
            # Use MTCNN
            img = Image.open(image_path).convert("RGB")
            boxes, probs = self._face_detector.detect(img)

            if boxes is None:
                return []

            faces = []
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                if prob > 0.9:  # Confidence threshold
                    x1, y1, x2, y2 = box.tolist()
                    faces.append({
                        "id": i,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": float(prob),
                    })
            return faces
        else:
            # Fallback to OpenCV Haar cascade
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            detected = face_cascade.detectMultiScale(gray, 1.1, 4)

            faces = []
            for i, (x, y, w, h) in enumerate(detected):
                faces.append({
                    "id": i,
                    "bbox": [int(x), int(y), int(x + w), int(y + h)],
                    "confidence": 0.8,
                })
            return faces

    async def _download_media(self, url_or_data: str) -> str:
        """Download media file or decode base64."""
        import base64

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            if url_or_data.startswith("data:"):
                # Base64 encoded
                _, data = url_or_data.split(",", 1)
                tmp.write(base64.b64decode(data))
            elif url_or_data.startswith("http"):
                # URL - download
                async with self._http_session.get(url_or_data) as response:
                    tmp.write(await response.read())
            else:
                # Assume it's a file path
                return url_or_data

            return tmp.name

    async def _upload_result(self, file_path: str, content_type: str) -> str:
        """Upload result file to storage."""
        try:
            url = f"{self.config.backend_url}/api/v1/storage/upload"

            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    f,
                    filename=os.path.basename(file_path),
                    content_type=content_type,
                )

                async with self._http_session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["url"]
                    else:
                        raise RuntimeError(f"Upload failed: {response.status}")
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise

    async def _cleanup_cache(self) -> None:
        """Clean up temporary files."""
        import shutil

        # Clean temp directory
        temp_dir = tempfile.gettempdir()
        for item in Path(temp_dir).glob("tmp*"):
            if item.is_file():
                try:
                    item.unlink()
                except Exception:
                    pass


async def main():
    """Main entry point for avatar worker."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = WorkerConfig(worker_type="avatar")
    worker = AvatarWorker(config)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
