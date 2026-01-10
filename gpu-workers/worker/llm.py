"""
LLM GPU Worker

Handles text generation, embeddings, and language model inference.
Models: Llama 3, Mistral, Phi-3
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Any, AsyncIterator, Optional

import torch

from worker.base import BaseWorker, Job, WorkerConfig

logger = logging.getLogger(__name__)


class LLMWorker(BaseWorker):
    """
    GPU worker for large language model inference.

    Supported job types:
    - generate: Text generation
    - generate_stream: Streaming text generation
    - embed: Generate embeddings
    - chat: Chat completion
    - summarize: Text summarization
    - classify: Text classification
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)

        # Models
        self._model = None
        self._tokenizer = None
        self._embedder = None

        # Model config
        self._model_name = os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
        self._quantization = os.getenv("LLM_QUANTIZATION", "4bit")

    @property
    def worker_type(self) -> str:
        return "llm"

    def get_supported_job_types(self) -> list[str]:
        return [
            "generate",
            "generate_stream",
            "embed",
            "chat",
            "summarize",
            "classify",
            "extract",
        ]

    async def load_models(self) -> None:
        """Load LLM model."""
        device = self.config.device

        await self.update_progress(0.0, f"Loading model: {self._model_name}...")

        # Load model with quantization
        self._model, self._tokenizer = await self._load_model(
            self._model_name,
            device,
            self._quantization,
        )

        await self.update_progress(0.8, "Loading embedding model...")
        self._embedder = await self._load_embedder(device)

        await self.update_progress(1.0, "LLM models loaded")

    async def _load_model(
        self,
        model_name: str,
        device: str,
        quantization: str,
    ) -> tuple[Any, Any]:
        """Load LLM with optional quantization."""
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        # Configure quantization
        bnb_config = None
        if quantization == "4bit":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        elif quantization == "8bit":
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
            )

        # Load tokenizer
        tokenizer = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.config.model_cache_dir,
            ),
        )

        # Ensure pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model
        model = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto" if device == "cuda" else None,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                cache_dir=self.config.model_cache_dir,
                trust_remote_code=True,
            ),
        )

        return model, tokenizer

    async def _load_embedder(self, device: str) -> Any:
        """Load embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            model = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: SentenceTransformer(
                    "BAAI/bge-large-en-v1.5",
                    device=device,
                    cache_folder=self.config.model_cache_dir,
                ),
            )
            return model
        except ImportError:
            logger.warning("sentence-transformers not available")
            return None

    async def process_job(self, job: Job) -> dict:
        """Process LLM job."""
        job_type = job.job_type

        if job_type == "generate":
            return await self._generate(job)
        elif job_type == "generate_stream":
            return await self._generate_stream(job)
        elif job_type == "embed":
            return await self._embed(job)
        elif job_type == "chat":
            return await self._chat(job)
        elif job_type == "summarize":
            return await self._summarize(job)
        elif job_type == "classify":
            return await self._classify(job)
        elif job_type == "extract":
            return await self._extract(job)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def _generate(self, job: Job) -> dict:
        """
        Generate text from prompt.

        Input:
            - prompt: Text prompt
            - params:
                - max_tokens: int (default 512)
                - temperature: float (default 0.7)
                - top_p: float (default 0.9)
                - top_k: int (default 50)
                - repetition_penalty: float (default 1.1)
                - stop_sequences: list[str]
        """
        if not self._model:
            raise RuntimeError("LLM model not loaded")

        input_data = job.input_data
        params = job.params

        prompt = input_data["prompt"]

        await self.update_progress(0.1, "Tokenizing input...")

        # Tokenize
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=4096,
        ).to(self._model.device)

        await self.update_progress(0.2, "Generating...")

        # Generation config
        gen_kwargs = {
            "max_new_tokens": params.get("max_tokens", 512),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "top_k": params.get("top_k", 50),
            "repetition_penalty": params.get("repetition_penalty", 1.1),
            "do_sample": params.get("temperature", 0.7) > 0,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        # Generate
        with torch.inference_mode():
            output_ids = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._model.generate(**inputs, **gen_kwargs),
            )

        await self.update_progress(0.9, "Decoding...")

        # Decode
        generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
        generated_text = self._tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

        # Handle stop sequences
        stop_sequences = params.get("stop_sequences", [])
        for stop_seq in stop_sequences:
            if stop_seq in generated_text:
                generated_text = generated_text.split(stop_seq)[0]

        return {
            "text": generated_text,
            "tokens_generated": len(generated_ids),
            "finish_reason": "stop" if generated_ids[-1] == self._tokenizer.eos_token_id else "length",
        }

    async def _generate_stream(self, job: Job) -> dict:
        """
        Stream text generation.

        Yields tokens as they're generated.
        """
        if not self._model:
            raise RuntimeError("LLM model not loaded")

        input_data = job.input_data
        params = job.params

        prompt = input_data["prompt"]

        # Tokenize
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=4096,
        ).to(self._model.device)

        # Use TextStreamer
        from transformers import TextIteratorStreamer

        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_special_tokens=True,
            skip_prompt=True,
        )

        # Generation config
        gen_kwargs = {
            **inputs,
            "max_new_tokens": params.get("max_tokens", 512),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "do_sample": params.get("temperature", 0.7) > 0,
            "streamer": streamer,
        }

        # Start generation in background
        generation_task = asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._model.generate(**gen_kwargs),
        )

        # Stream tokens
        generated_text = ""
        token_count = 0

        for text_chunk in streamer:
            generated_text += text_chunk
            token_count += 1

            # Publish chunk
            await self._publish_text_chunk(job.id, token_count, text_chunk)

            # Update progress periodically
            if token_count % 10 == 0:
                await self.update_progress(
                    min(0.9, 0.1 + 0.8 * token_count / params.get("max_tokens", 512)),
                    f"Generated {token_count} tokens...",
                )

        # Wait for generation to complete
        await generation_task

        return {
            "text": generated_text,
            "tokens_generated": token_count,
            "streamed": True,
        }

    async def _publish_text_chunk(
        self, job_id: str, token_idx: int, text: str
    ) -> None:
        """Publish text chunk for streaming."""
        channel = f"text_stream:{job_id}"
        await self._redis.publish(channel, json.dumps({
            "token_idx": token_idx,
            "text": text,
        }))

    async def _embed(self, job: Job) -> dict:
        """
        Generate embeddings for text.

        Input:
            - texts: List of texts to embed
            - params:
                - normalize: bool (default True)
        """
        if not self._embedder:
            raise RuntimeError("Embedding model not loaded")

        input_data = job.input_data
        params = job.params

        texts = input_data["texts"]
        if isinstance(texts, str):
            texts = [texts]

        await self.update_progress(0.2, f"Embedding {len(texts)} texts...")

        # Generate embeddings
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._embedder.encode(
                texts,
                normalize_embeddings=params.get("normalize", True),
                show_progress_bar=False,
            ),
        )

        await self.update_progress(0.9, "Formatting results...")

        return {
            "embeddings": embeddings.tolist(),
            "dimensions": embeddings.shape[1],
            "count": len(texts),
        }

    async def _chat(self, job: Job) -> dict:
        """
        Chat completion.

        Input:
            - messages: List of chat messages [{role, content}]
            - params: Generation params
        """
        if not self._model:
            raise RuntimeError("LLM model not loaded")

        input_data = job.input_data
        params = job.params

        messages = input_data["messages"]

        await self.update_progress(0.1, "Formatting chat...")

        # Format messages for the model
        formatted_prompt = self._format_chat_messages(messages)

        # Generate response
        inputs = self._tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=4096,
        ).to(self._model.device)

        await self.update_progress(0.3, "Generating response...")

        gen_kwargs = {
            "max_new_tokens": params.get("max_tokens", 512),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "do_sample": params.get("temperature", 0.7) > 0,
            "pad_token_id": self._tokenizer.pad_token_id,
        }

        with torch.inference_mode():
            output_ids = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._model.generate(**inputs, **gen_kwargs),
            )

        # Decode
        generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
        response = self._tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

        return {
            "message": {
                "role": "assistant",
                "content": response.strip(),
            },
            "tokens_generated": len(generated_ids),
        }

    def _format_chat_messages(self, messages: list[dict]) -> str:
        """Format chat messages for the model."""
        # Check if tokenizer has chat template
        if hasattr(self._tokenizer, "apply_chat_template"):
            return self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        # Fallback formatting
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                formatted += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}\n"

        formatted += "<|assistant|>\n"
        return formatted

    async def _summarize(self, job: Job) -> dict:
        """
        Summarize text.

        Input:
            - text: Text to summarize
            - params:
                - max_length: int (default 150)
                - style: 'bullet', 'paragraph', 'tldr'
        """
        input_data = job.input_data
        params = job.params

        text = input_data["text"]
        style = params.get("style", "paragraph")
        max_length = params.get("max_length", 150)

        # Build prompt based on style
        if style == "bullet":
            prompt = f"Summarize the following text as bullet points:\n\n{text}\n\nBullet points:"
        elif style == "tldr":
            prompt = f"TL;DR of the following text:\n\n{text}\n\nTL;DR:"
        else:
            prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}\n\nSummary:"

        # Generate
        job.input_data = {"prompt": prompt}
        job.params = {"max_tokens": max_length * 2, "temperature": 0.3}

        result = await self._generate(job)

        return {
            "summary": result["text"].strip(),
            "style": style,
        }

    async def _classify(self, job: Job) -> dict:
        """
        Classify text into categories.

        Input:
            - text: Text to classify
            - categories: List of possible categories
            - params:
                - multi_label: bool (default False)
        """
        input_data = job.input_data
        params = job.params

        text = input_data["text"]
        categories = input_data["categories"]
        multi_label = params.get("multi_label", False)

        # Build classification prompt
        categories_str = ", ".join(categories)

        if multi_label:
            prompt = f"""Classify the following text into one or more of these categories: {categories_str}

Text: {text}

Return the categories as a JSON list. Categories:"""
        else:
            prompt = f"""Classify the following text into exactly one of these categories: {categories_str}

Text: {text}

Category:"""

        # Generate
        job.input_data = {"prompt": prompt}
        job.params = {"max_tokens": 100, "temperature": 0.1}

        result = await self._generate(job)
        response = result["text"].strip()

        # Parse response
        if multi_label:
            try:
                # Try to parse as JSON
                labels = json.loads(response)
            except json.JSONDecodeError:
                # Extract categories mentioned
                labels = [c for c in categories if c.lower() in response.lower()]
        else:
            # Find best matching category
            labels = None
            for cat in categories:
                if cat.lower() in response.lower():
                    labels = cat
                    break

            if labels is None:
                labels = response.split()[0] if response else categories[0]

        return {
            "classification": labels,
            "multi_label": multi_label,
        }

    async def _extract(self, job: Job) -> dict:
        """
        Extract structured information from text.

        Input:
            - text: Text to extract from
            - schema: JSON schema of expected output
        """
        input_data = job.input_data

        text = input_data["text"]
        schema = input_data["schema"]

        # Build extraction prompt
        schema_str = json.dumps(schema, indent=2)
        prompt = f"""Extract information from the following text according to this JSON schema:

Schema:
{schema_str}

Text:
{text}

Return only valid JSON matching the schema:"""

        # Generate
        job.input_data = {"prompt": prompt}
        job.params = {"max_tokens": 500, "temperature": 0.1}

        result = await self._generate(job)
        response = result["text"].strip()

        # Parse JSON
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                extracted = json.loads(response[start:end])
            else:
                extracted = {"raw": response}
        except json.JSONDecodeError:
            extracted = {"raw": response}

        return {
            "extracted": extracted,
            "schema": schema,
        }

    async def _cleanup_cache(self) -> None:
        """Clean up GPU memory."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


async def main():
    """Main entry point for LLM worker."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = WorkerConfig(worker_type="llm")
    worker = LLMWorker(config)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
