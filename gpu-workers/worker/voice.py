"""
Voice GPU Worker

Handles text-to-speech, voice cloning, and speech-to-text.
Models: Coqui XTTS, Tortoise TTS, Bark, Whisper
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch

from worker.base import BaseWorker, Job, WorkerConfig

logger = logging.getLogger(__name__)


class VoiceWorker(BaseWorker):
    """
    GPU worker for voice synthesis and processing.

    Supported job types:
    - tts: Text-to-speech synthesis
    - voice_clone: Clone a voice from samples
    - stt: Speech-to-text transcription
    - voice_enhance: Enhance audio quality
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)

        # Models
        self._xtts = None
        self._tortoise = None
        self._bark = None
        self._whisper = None

        # Voice embeddings cache
        self._voice_embeddings: dict[str, Any] = {}

    @property
    def worker_type(self) -> str:
        return "voice"

    def get_supported_job_types(self) -> list[str]:
        return [
            "tts",
            "tts_stream",
            "voice_clone",
            "stt",
            "voice_enhance",
            "voice_convert",
        ]

    async def load_models(self) -> None:
        """Load voice models."""
        device = self.config.device

        await self.update_progress(0.0, "Loading Coqui XTTS...")
        self._xtts = await self._load_xtts(device)

        await self.update_progress(0.4, "Loading Whisper...")
        self._whisper = await self._load_whisper(device)

        # Tortoise and Bark are loaded on-demand due to memory constraints
        await self.update_progress(1.0, "Voice models loaded")

    async def _load_xtts(self, device: str) -> Any:
        """Load Coqui XTTS model."""
        try:
            from TTS.api import TTS

            # XTTS v2 multilingual model
            model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            model.to(device)
            return model
        except ImportError:
            logger.warning("Coqui TTS not available")
            return None

    async def _load_tortoise(self, device: str) -> Any:
        """Load Tortoise TTS model (on-demand)."""
        try:
            from tortoise.api import TextToSpeech

            model = TextToSpeech()
            return model
        except ImportError:
            logger.warning("Tortoise TTS not available")
            return None

    async def _load_bark(self, device: str) -> Any:
        """Load Bark TTS model (on-demand)."""
        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models

            preload_models()
            return {"generate": generate_audio, "sample_rate": SAMPLE_RATE}
        except ImportError:
            logger.warning("Bark not available")
            return None

    async def _load_whisper(self, device: str) -> Any:
        """Load Whisper for speech-to-text."""
        try:
            import whisper

            model = whisper.load_model("large-v3", device=device)
            return model
        except ImportError:
            logger.warning("Whisper not available")
            return None

    async def process_job(self, job: Job) -> dict:
        """Process voice job."""
        job_type = job.job_type

        if job_type == "tts":
            return await self._text_to_speech(job)
        elif job_type == "tts_stream":
            return await self._text_to_speech_stream(job)
        elif job_type == "voice_clone":
            return await self._clone_voice(job)
        elif job_type == "stt":
            return await self._speech_to_text(job)
        elif job_type == "voice_enhance":
            return await self._enhance_voice(job)
        elif job_type == "voice_convert":
            return await self._convert_voice(job)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def _text_to_speech(self, job: Job) -> dict:
        """
        Convert text to speech.

        Input:
            - text: Text to synthesize
            - voice_id: ID of cloned voice (optional)
            - language: Target language code
            - params:
                - model: 'xtts', 'tortoise', or 'bark'
                - speed: float (0.5-2.0)
                - emotion: str (for bark)
        """
        if not self._xtts:
            raise RuntimeError("XTTS model not loaded")

        input_data = job.input_data
        params = job.params

        text = input_data["text"]
        voice_id = input_data.get("voice_id")
        language = input_data.get("language", "en")
        model_choice = params.get("model", "xtts")

        await self.update_progress(0.1, "Preparing synthesis...")

        # Get voice reference if provided
        speaker_wav = None
        if voice_id:
            speaker_wav = await self._get_voice_reference(voice_id)

        await self.update_progress(0.3, "Synthesizing speech...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.wav")

            if model_choice == "xtts":
                result = await self._synthesize_xtts(
                    text, output_path, speaker_wav, language, params
                )
            elif model_choice == "tortoise":
                result = await self._synthesize_tortoise(
                    text, output_path, voice_id, params
                )
            elif model_choice == "bark":
                result = await self._synthesize_bark(text, output_path, params)
            else:
                raise ValueError(f"Unknown model: {model_choice}")

            await self.update_progress(0.9, "Uploading audio...")
            audio_url = await self._upload_result(output_path, "audio/wav")

        return {
            "audio_url": audio_url,
            "duration_seconds": result["duration"],
            "sample_rate": result["sample_rate"],
            "model_used": model_choice,
        }

    async def _synthesize_xtts(
        self,
        text: str,
        output_path: str,
        speaker_wav: Optional[str],
        language: str,
        params: dict,
    ) -> dict:
        """Synthesize with Coqui XTTS."""
        # Run in thread pool
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._xtts.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=speaker_wav,
                language=language,
                speed=params.get("speed", 1.0),
            ),
        )

        # Get duration
        import soundfile as sf
        data, sample_rate = sf.read(output_path)
        duration = len(data) / sample_rate

        return {"duration": duration, "sample_rate": sample_rate}

    async def _synthesize_tortoise(
        self,
        text: str,
        output_path: str,
        voice_id: Optional[str],
        params: dict,
    ) -> dict:
        """Synthesize with Tortoise TTS."""
        if not self._tortoise:
            self._tortoise = await self._load_tortoise(self.config.device)

        import torchaudio

        # Get voice conditioning
        voice_samples = None
        if voice_id:
            voice_samples = await self._get_voice_samples(voice_id)

        # Generate
        audio = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._tortoise.tts(
                text=text,
                voice_samples=voice_samples,
                preset=params.get("preset", "fast"),
            ),
        )

        # Save
        sample_rate = 24000
        torchaudio.save(output_path, audio.unsqueeze(0).cpu(), sample_rate)

        return {"duration": len(audio) / sample_rate, "sample_rate": sample_rate}

    async def _synthesize_bark(
        self,
        text: str,
        output_path: str,
        params: dict,
    ) -> dict:
        """Synthesize with Bark."""
        if not self._bark:
            self._bark = await self._load_bark(self.config.device)

        import scipy

        # Add emotion/style tags if specified
        emotion = params.get("emotion")
        if emotion:
            text = f"[{emotion}] {text}"

        # Generate
        audio = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._bark["generate"](text),
        )

        sample_rate = self._bark["sample_rate"]

        # Save
        scipy.io.wavfile.write(
            output_path,
            rate=sample_rate,
            data=(audio * 32767).astype(np.int16),
        )

        return {"duration": len(audio) / sample_rate, "sample_rate": sample_rate}

    async def _text_to_speech_stream(self, job: Job) -> dict:
        """
        Stream text-to-speech generation.

        Generates audio in chunks for lower latency.
        """
        if not self._xtts:
            raise RuntimeError("XTTS model not loaded")

        input_data = job.input_data
        params = job.params

        text = input_data["text"]
        voice_id = input_data.get("voice_id")
        language = input_data.get("language", "en")

        # Get voice reference
        speaker_wav = None
        if voice_id:
            speaker_wav = await self._get_voice_reference(voice_id)

        # Stream synthesis
        chunks = []
        chunk_idx = 0

        # Use XTTS streaming if available
        try:
            gpt_cond_latent, speaker_embedding = self._xtts.synthesizer.tts_model.get_conditioning_latents(
                audio_path=speaker_wav
            )

            for chunk in self._xtts.synthesizer.tts_model.inference_stream(
                text,
                language,
                gpt_cond_latent,
                speaker_embedding,
            ):
                # Publish chunk via Redis
                chunk_data = base64.b64encode(chunk.cpu().numpy().tobytes()).decode()
                await self._publish_audio_chunk(job.id, chunk_idx, chunk_data)
                chunks.append(chunk)
                chunk_idx += 1

                # Update progress
                await self.update_progress(
                    0.5, f"Streaming chunk {chunk_idx}..."
                )

        except Exception as e:
            logger.warning(f"Streaming failed, falling back to batch: {e}")
            return await self._text_to_speech(job)

        # Combine chunks and upload final audio
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.wav")

            combined = torch.cat(chunks, dim=0)
            import torchaudio
            torchaudio.save(output_path, combined.unsqueeze(0).cpu(), 24000)

            audio_url = await self._upload_result(output_path, "audio/wav")

        return {
            "audio_url": audio_url,
            "chunks_generated": chunk_idx,
            "streamed": True,
        }

    async def _publish_audio_chunk(
        self, job_id: str, chunk_idx: int, chunk_data: str
    ) -> None:
        """Publish audio chunk for streaming."""
        import json

        channel = f"audio_stream:{job_id}"
        await self._redis.publish(channel, json.dumps({
            "chunk_idx": chunk_idx,
            "audio_data": chunk_data,
        }))

    async def _clone_voice(self, job: Job) -> dict:
        """
        Clone a voice from audio samples.

        Input:
            - audio_samples: List of audio URLs
            - voice_name: Name for the cloned voice

        Returns:
            - voice_id: ID of the cloned voice
        """
        if not self._xtts:
            raise RuntimeError("XTTS model not loaded")

        input_data = job.input_data

        audio_samples = input_data["audio_samples"]
        voice_name = input_data.get("voice_name", "custom_voice")

        await self.update_progress(0.1, "Downloading audio samples...")

        # Download all samples
        sample_paths = []
        for i, sample_url in enumerate(audio_samples):
            path = await self._download_audio(sample_url)
            sample_paths.append(path)
            await self.update_progress(
                0.1 + 0.3 * (i + 1) / len(audio_samples),
                f"Downloaded sample {i + 1}/{len(audio_samples)}",
            )

        await self.update_progress(0.5, "Extracting voice embedding...")

        # Extract speaker embedding
        gpt_cond_latent, speaker_embedding = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._xtts.synthesizer.tts_model.get_conditioning_latents(
                audio_path=sample_paths,
            ),
        )

        # Save embedding
        voice_id = await self._save_voice_embedding(
            voice_name,
            gpt_cond_latent,
            speaker_embedding,
        )

        await self.update_progress(0.9, "Generating preview...")

        # Generate preview audio
        preview_text = "This is a preview of the cloned voice."
        with tempfile.TemporaryDirectory() as tmp_dir:
            preview_path = os.path.join(tmp_dir, "preview.wav")

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._xtts.tts_to_file(
                    text=preview_text,
                    file_path=preview_path,
                    speaker_wav=sample_paths[0],
                    language="en",
                ),
            )

            preview_url = await self._upload_result(preview_path, "audio/wav")

        # Clean up
        for path in sample_paths:
            try:
                os.unlink(path)
            except Exception:
                pass

        return {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "preview_url": preview_url,
            "samples_processed": len(audio_samples),
        }

    async def _speech_to_text(self, job: Job) -> dict:
        """
        Transcribe audio to text.

        Input:
            - audio: Audio URL or base64
            - params:
                - language: Source language (optional, auto-detect if not set)
                - task: 'transcribe' or 'translate'
                - word_timestamps: bool
        """
        if not self._whisper:
            raise RuntimeError("Whisper model not loaded")

        input_data = job.input_data
        params = job.params

        await self.update_progress(0.1, "Downloading audio...")
        audio_path = await self._download_audio(input_data["audio"])

        await self.update_progress(0.3, "Transcribing...")

        # Transcribe
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._whisper.transcribe(
                audio_path,
                language=params.get("language"),
                task=params.get("task", "transcribe"),
                word_timestamps=params.get("word_timestamps", False),
            ),
        )

        await self.update_progress(0.9, "Processing results...")

        # Format segments
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "words": seg.get("words", []),
            })

        # Clean up
        try:
            os.unlink(audio_path)
        except Exception:
            pass

        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": segments,
            "duration_seconds": segments[-1]["end"] if segments else 0,
        }

    async def _enhance_voice(self, job: Job) -> dict:
        """
        Enhance audio quality.

        Input:
            - audio: Audio URL
            - params:
                - denoise: bool
                - normalize: bool
                - remove_silence: bool
        """
        input_data = job.input_data
        params = job.params

        await self.update_progress(0.1, "Downloading audio...")
        audio_path = await self._download_audio(input_data["audio"])

        await self.update_progress(0.3, "Enhancing audio...")

        import soundfile as sf
        import scipy.signal as signal

        # Load audio
        data, sample_rate = sf.read(audio_path)

        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Denoise
        if params.get("denoise", True):
            await self.update_progress(0.4, "Removing noise...")
            data = await self._denoise_audio(data, sample_rate)

        # Normalize
        if params.get("normalize", True):
            await self.update_progress(0.6, "Normalizing...")
            data = data / np.max(np.abs(data)) * 0.95

        # Remove silence
        if params.get("remove_silence", False):
            await self.update_progress(0.7, "Removing silence...")
            data = await self._remove_silence(data, sample_rate)

        # Save enhanced audio
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "enhanced.wav")
            sf.write(output_path, data, sample_rate)

            await self.update_progress(0.9, "Uploading...")
            audio_url = await self._upload_result(output_path, "audio/wav")

        # Clean up
        try:
            os.unlink(audio_path)
        except Exception:
            pass

        return {
            "audio_url": audio_url,
            "duration_seconds": len(data) / sample_rate,
            "sample_rate": sample_rate,
        }

    async def _denoise_audio(self, data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise reduction to audio."""
        try:
            import noisereduce as nr

            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: nr.reduce_noise(y=data, sr=sample_rate),
            )
        except ImportError:
            logger.warning("noisereduce not available")
            return data

    async def _remove_silence(
        self, data: np.ndarray, sample_rate: int, threshold: float = 0.01
    ) -> np.ndarray:
        """Remove silence from audio."""
        # Simple silence removal based on amplitude threshold
        window_size = int(sample_rate * 0.02)  # 20ms windows

        # Calculate RMS energy for each window
        num_windows = len(data) // window_size
        keep_mask = np.zeros(len(data), dtype=bool)

        for i in range(num_windows):
            start = i * window_size
            end = start + window_size
            window = data[start:end]
            rms = np.sqrt(np.mean(window ** 2))

            if rms > threshold:
                # Add padding around non-silent regions
                pad_start = max(0, start - window_size)
                pad_end = min(len(data), end + window_size)
                keep_mask[pad_start:pad_end] = True

        return data[keep_mask]

    async def _convert_voice(self, job: Job) -> dict:
        """
        Convert voice from source speaker to target speaker.

        Input:
            - audio: Source audio URL
            - target_voice_id: Target voice ID
        """
        # Voice conversion would use models like so-vits-svc or RVC
        raise NotImplementedError("Voice conversion not yet implemented")

    async def _get_voice_reference(self, voice_id: str) -> Optional[str]:
        """Get voice reference audio file for voice ID."""
        # Check cache
        if voice_id in self._voice_embeddings:
            return self._voice_embeddings[voice_id].get("reference_path")

        # Fetch from backend
        try:
            url = f"{self.config.backend_url}/api/v1/voices/{voice_id}/reference"
            async with self._http_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("reference_url"):
                        return await self._download_audio(data["reference_url"])
        except Exception as e:
            logger.warning(f"Failed to get voice reference: {e}")

        return None

    async def _get_voice_samples(self, voice_id: str) -> Optional[list]:
        """Get voice samples for Tortoise TTS."""
        # Would return list of audio tensors
        return None

    async def _save_voice_embedding(
        self,
        voice_name: str,
        gpt_cond_latent: Any,
        speaker_embedding: Any,
    ) -> str:
        """Save voice embedding to storage."""
        import uuid

        voice_id = str(uuid.uuid4())

        # Save to backend
        try:
            url = f"{self.config.backend_url}/api/v1/voices"

            # Serialize embeddings
            embedding_data = {
                "gpt_cond_latent": gpt_cond_latent.cpu().numpy().tolist(),
                "speaker_embedding": speaker_embedding.cpu().numpy().tolist(),
            }

            payload = {
                "voice_id": voice_id,
                "voice_name": voice_name,
                "embedding": embedding_data,
            }

            async with self._http_session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Failed to save voice embedding: {response.status}")

        except Exception as e:
            logger.error(f"Error saving voice embedding: {e}")

        # Cache locally
        self._voice_embeddings[voice_id] = {
            "name": voice_name,
            "gpt_cond_latent": gpt_cond_latent,
            "speaker_embedding": speaker_embedding,
        }

        return voice_id

    async def _download_audio(self, url_or_data: str) -> str:
        """Download audio file or decode base64."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
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


async def main():
    """Main entry point for voice worker."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = WorkerConfig(worker_type="voice")
    worker = VoiceWorker(config)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
