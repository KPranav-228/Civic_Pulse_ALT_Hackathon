"""Summarizer implementations for T5, BART, Pegasus, and Groq LLM.

Each summarizer inherits from BaseSummarizer and implements the summarize() method.
Local models use the ModelManager for lazy loading and memory management.
The LLM summarizer calls the Groq API with rate limiting and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from backend.config.settings import settings
from backend.services.model_manager import model_manager, MODEL_REGISTRY
from backend.services.preprocessing import chunk_text

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """Abstract base class for all summarizers."""

    name: str
    display_name: str
    is_local: bool = True

    @abstractmethod
    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a summary of the input text.
        
        Returns a dict with:
            - summary: str
            - generation_time_seconds: float
            - was_chunked: bool
            - num_chunks: int
            - metadata: dict (model-specific info)
        """
        pass

    def _build_result(
        self,
        summary: str,
        generation_time: float,
        was_chunked: bool = False,
        num_chunks: int = 1,
        **extra,
    ) -> dict[str, Any]:
        """Helper to build a standardized result dict."""
        word_count = len(summary.split()) if summary else 0
        return {
            "summary": summary,
            "generation_time_seconds": round(generation_time, 3),
            "was_chunked": was_chunked,
            "num_chunks": num_chunks,
            "word_count": word_count,
            "metadata": extra,
        }


class LocalModelSummarizer(BaseSummarizer):
    """Base class for local transformer model summarizers (T5, BART, Pegasus).
    
    Handles model loading via ModelManager, chunking for long inputs,
    and two-pass summarization for multi-chunk inputs.
    """

    model_key: str  # Key in MODEL_REGISTRY (e.g., "t5", "bart", "pegasus")

    def _get_max_input_tokens(self) -> int:
        """Get the max input token length for this model."""
        info = MODEL_REGISTRY.get(self.model_key, {})
        return info.get("max_input_tokens", 512)

    def _prepare_input(self, text: str) -> str:
        """Optional input preprocessing (e.g., T5's 'summarize:' prefix). Override in subclass."""
        return text

    def _generate_summary(
        self,
        text: str,
        model,
        tokenizer,
        max_length: int,
        min_length: int,
        num_beams: int,
    ) -> str:
        """Generate a summary from a single text chunk using the loaded model."""
        import torch

        prepared = self._prepare_input(text)
        
        inputs = tokenizer(
            prepared,
            return_tensors="pt",
            max_length=self._get_max_input_tokens(),
            truncation=True,
        )
        inputs = {k: v.to(model_manager.device) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                early_stopping=True,
                no_repeat_ngram_size=3,
                length_penalty=2.0,
            )

        summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return summary.strip()

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a summary, handling chunking for long inputs."""
        start_time = time.time()

        # Load model (ModelManager handles caching and eviction)
        model, tokenizer = model_manager.load_model(self.model_key)

        # Check if chunking is needed
        max_tokens = self._get_max_input_tokens()
        # Reserve some tokens for special tokens
        effective_max = max_tokens - 10
        chunks = chunk_text(text, effective_max, tokenizer=tokenizer)

        if len(chunks) <= 1:
            # Single chunk — straightforward generation
            summary = self._generate_summary(
                text, model, tokenizer, max_length, min_length, num_beams
            )
            elapsed = time.time() - start_time
            return self._build_result(summary, elapsed, was_chunked=False, num_chunks=1)

        # Multi-chunk — summarize each chunk, then aggregate
        logger.info(f"{self.name}: Input split into {len(chunks)} chunks")
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"{self.name}: Summarizing chunk {i+1}/{len(chunks)}")
            chunk_summary = self._generate_summary(
                chunk, model, tokenizer, max_length, min_length, num_beams
            )
            chunk_summaries.append(chunk_summary)

        # Second pass: summarize the concatenated chunk summaries
        combined = " ".join(chunk_summaries)
        
        # Check if combined summary needs re-chunking (unlikely but handle it)
        combined_tokens = len(tokenizer.encode(combined, add_special_tokens=False))
        if combined_tokens <= effective_max:
            final_summary = self._generate_summary(
                combined, model, tokenizer, max_length, min_length, num_beams
            )
        else:
            # If combined summaries are still too long, just concatenate
            final_summary = combined

        elapsed = time.time() - start_time
        return self._build_result(
            final_summary, elapsed,
            was_chunked=True, num_chunks=len(chunks),
            chunk_summaries=chunk_summaries,
        )


class T5Summarizer(LocalModelSummarizer):
    """T5-Small summarizer. Uses 'summarize:' prefix as required by T5's multi-task format."""

    name = "t5"
    display_name = "T5-Small"
    model_key = "t5"

    def _prepare_input(self, text: str) -> str:
        return f"summarize: {text}"


class BARTSummarizer(LocalModelSummarizer):
    """DistilBART-CNN summarizer. Pre-finetuned on CNN/DailyMail, no prefix needed."""

    name = "bart"
    display_name = "DistilBART-CNN"
    model_key = "bart"


class PegasusSummarizer(LocalModelSummarizer):
    """PEGASUS-XSum summarizer. Pre-finetuned on XSum for abstractive summarization."""

    name = "pegasus"
    display_name = "PEGASUS-XSum"
    model_key = "pegasus"


class LLMSummarizer(BaseSummarizer):
    """Groq API-based summarizer using Llama 3.3 70B.
    
    Features:
    - System prompt designed for factual, concise summarization
    - Rate limiting with exponential backoff
    - Response validation
    - Graceful error handling
    """

    name = "llm"
    display_name = "Llama 3.3 70B (Groq)"
    is_local = False

    SYSTEM_PROMPT = (
        "You are a professional news summarizer. Given a news article, produce a concise, "
        "accurate summary that:\n"
        "- Preserves all key factual information (names, dates, numbers, locations)\n"
        "- Does NOT introduce any information not present in the original article\n"
        "- Does NOT add commentary, opinions, or analysis\n"
        "- Prioritizes the most important information\n"
        "- Maintains logical coherence and flow\n"
        "- Uses clear, professional language\n"
        "- Outputs ONLY the summary text, with no preamble or labels"
    )

    def _get_client(self):
        """Get a Groq client. Raises RuntimeError if not configured."""
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "Groq API key not configured. Set GROQ_API_KEY in your .env file. "
                "Get a free key at https://console.groq.com"
            )
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY)

    def _call_groq(
        self,
        text: str,
        max_length: int,
        min_length: int,
    ) -> str:
        """Make a single Groq API call with retry logic."""
        client = self._get_client()

        user_prompt = (
            f"Summarize the following news article in {min_length} to {max_length} words.\n\n"
            f"Article:\n{text}"
        )

        last_error = None
        for attempt in range(settings.GROQ_MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=max(max_length * 3, 512),  # Tokens ≈ 1.3× words, with margin
                )

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Empty response from Groq API")
                
                return content.strip()

            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check for rate limiting
                if "429" in error_str or "rate" in error_str.lower():
                    wait_time = settings.GROQ_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Groq rate limited (attempt {attempt+1}/{settings.GROQ_MAX_RETRIES}), "
                        f"waiting {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    continue
                
                # Non-rate-limit error — don't retry
                logger.error(f"Groq API error: {e}")
                raise RuntimeError(f"Groq API error: {e}") from e

        raise RuntimeError(
            f"Groq API failed after {settings.GROQ_MAX_RETRIES} retries: {last_error}"
        )

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        num_beams: int = 4,  # Unused for LLM, kept for interface compatibility
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a summary using the Groq API."""
        start_time = time.time()

        # For very long articles, the LLM can handle large context (128K tokens)
        # but we'll still chunk if it's extremely long to stay within practical limits
        # Groq's llama-3.3-70b has 128K context but we keep it reasonable
        max_chars = 50_000  # ~10K words ≈ ~13K tokens, well within limits
        
        if len(text) > max_chars:
            # Chunk and summarize each part, then aggregate
            chunk_size_tokens = 4000  # ~3000 words per chunk
            chunks = chunk_text(text, chunk_size_tokens)
            logger.info(f"LLM: Input split into {len(chunks)} chunks")

            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"LLM: Summarizing chunk {i+1}/{len(chunks)}")
                chunk_summary = self._call_groq(chunk, max_length, min_length)
                chunk_summaries.append(chunk_summary)
                # Rate limit delay between chunks
                if i < len(chunks) - 1:
                    time.sleep(settings.GROQ_RETRY_DELAY)

            # Second pass: summarize combined chunk summaries
            combined = " ".join(chunk_summaries)
            final_summary = self._call_groq(combined, max_length, min_length)

            elapsed = time.time() - start_time
            return self._build_result(
                final_summary, elapsed,
                was_chunked=True, num_chunks=len(chunks),
                chunk_summaries=chunk_summaries,
                model=settings.GROQ_MODEL,
            )
        else:
            summary = self._call_groq(text, max_length, min_length)
            elapsed = time.time() - start_time
            return self._build_result(
                summary, elapsed,
                was_chunked=False, num_chunks=1,
                model=settings.GROQ_MODEL,
            )


# --- Factory ---

SUMMARIZERS: dict[str, BaseSummarizer] = {
    "t5": T5Summarizer(),
    "bart": BARTSummarizer(),
    "pegasus": PegasusSummarizer(),
    "llm": LLMSummarizer(),
}


def get_summarizer(name: str) -> BaseSummarizer:
    """Get a summarizer by name. Raises ValueError if not found."""
    if name not in SUMMARIZERS:
        raise ValueError(f"Unknown summarizer: '{name}'. Available: {list(SUMMARIZERS.keys())}")
    return SUMMARIZERS[name]
