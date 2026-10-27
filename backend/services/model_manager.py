"""Model Manager — handles lazy loading, caching, and memory management for local models."""

import gc
import logging
import time
from typing import Any

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# Model registry: maps model name -> (checkpoint, max_input_tokens)
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "t5": {
        "checkpoint": "t5-small",
        "max_input_tokens": 512,
        "display_name": "T5-Small",
    },
    "bart": {
        "checkpoint": "sshleifer/distilbart-cnn-12-6",
        "max_input_tokens": 1024,
        "display_name": "DistilBART-CNN",
    },
    "pegasus": {
        "checkpoint": "google/pegasus-xsum",
        "max_input_tokens": 512,
        "display_name": "PEGASUS-XSum",
    },
}


def get_device() -> torch.device:
    """Detect the best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class ModelManager:
    """Manages lazy loading and caching of transformer models.
    
    Only keeps MAX_LOADED_MODELS models in memory at once.
    When a new model is loaded and the limit is reached, the least-recently-used model is evicted.
    """

    def __init__(self, max_loaded: int | None = None):
        self.max_loaded = max_loaded or settings.MAX_LOADED_MODELS
        self.device = get_device()
        # Cache: model_name -> {"model": model, "tokenizer": tokenizer, "last_used": timestamp}
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_errors: dict[str, str] = {}
        logger.info(f"ModelManager initialized: device={self.device}, max_loaded={self.max_loaded}")

    @property
    def loaded_models(self) -> list[str]:
        """Return list of currently loaded model names."""
        return list(self._cache.keys())

    def get_model_info(self, name: str) -> dict[str, Any] | None:
        """Get registry info for a model by name."""
        return MODEL_REGISTRY.get(name)

    def is_loaded(self, name: str) -> bool:
        """Check if a model is currently loaded in memory."""
        return name in self._cache

    def get_status(self, name: str) -> str:
        """Get the status of a model: 'loaded', 'available', 'error', or 'unknown'."""
        if name in self._cache:
            return "loaded"
        if name in self._load_errors:
            return "error"
        if name in MODEL_REGISTRY:
            return "available"
        return "unknown"

    def get_error(self, name: str) -> str | None:
        """Get the last load error for a model, if any."""
        return self._load_errors.get(name)

    def _evict_lru(self) -> None:
        """Evict the least-recently-used model from cache to free memory."""
        if not self._cache:
            return
        
        # Find the LRU model
        lru_name = min(self._cache, key=lambda k: self._cache[k]["last_used"])
        self.unload_model(lru_name)

    def load_model(self, name: str) -> tuple[Any, Any]:
        """Load a model and tokenizer into memory.
        
        Returns (model, tokenizer) tuple.
        Raises ValueError if model name is unknown.
        Raises RuntimeError if model fails to load.
        """
        # Return cached if available
        if name in self._cache:
            self._cache[name]["last_used"] = time.time()
            logger.info(f"Model '{name}' served from cache")
            return self._cache[name]["model"], self._cache[name]["tokenizer"]

        if name not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: '{name}'. Available: {list(MODEL_REGISTRY.keys())}")

        # Evict models if at capacity
        while len(self._cache) >= self.max_loaded:
            self._evict_lru()

        checkpoint = MODEL_REGISTRY[name]["checkpoint"]
        logger.info(f"Loading model '{name}' (checkpoint: {checkpoint}) to {self.device}...")

        try:
            start = time.time()
            tokenizer = AutoTokenizer.from_pretrained(checkpoint)
            model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)
            model = model.to(self.device)
            model.eval()  # Set to evaluation mode
            elapsed = time.time() - start
            
            self._cache[name] = {
                "model": model,
                "tokenizer": tokenizer,
                "last_used": time.time(),
            }
            # Clear any previous error
            self._load_errors.pop(name, None)
            logger.info(f"Model '{name}' loaded in {elapsed:.1f}s")
            return model, tokenizer

        except Exception as e:
            error_msg = f"Failed to load model '{name}': {e}"
            logger.error(error_msg)
            self._load_errors[name] = str(e)
            raise RuntimeError(error_msg) from e

    def unload_model(self, name: str) -> None:
        """Unload a model from memory and free resources."""
        if name not in self._cache:
            return

        logger.info(f"Unloading model '{name}'...")
        entry = self._cache.pop(name)
        
        # Move model to CPU before deleting (if on GPU) to free VRAM
        if self.device.type == "cuda":
            entry["model"].cpu()
        
        del entry["model"]
        del entry["tokenizer"]
        
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info(f"Model '{name}' unloaded")

    def unload_all(self) -> None:
        """Unload all models from memory."""
        for name in list(self._cache.keys()):
            self.unload_model(name)


# Module-level singleton
model_manager = ModelManager()
