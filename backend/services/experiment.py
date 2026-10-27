"""Experiment service — batch evaluation of models on CNN/DailyMail and XSum datasets.

Handles dataset loading, sample selection, batch summarization, ROUGE evaluation,
and results export. Includes rate limiting for LLM calls and progress tracking.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from backend.config.settings import settings
from backend.services.summarizers import get_summarizer, SUMMARIZERS
from backend.services.evaluation import compute_rouge
from backend.schemas.models import RougeScores

logger = logging.getLogger(__name__)


def load_dataset_samples(
    dataset_name: str = "cnn_dailymail",
    num_samples: int = 5,
    split: str = "test",
) -> list[dict[str, str]]:
    """Load a small sample from a HuggingFace dataset.
    
    Args:
        dataset_name: "cnn_dailymail" or "xsum"
        num_samples: Number of samples to load
        split: Dataset split ("test", "validation", "train")
        
    Returns:
        List of dicts with "article" and "reference_summary" keys.
    """
    from datasets import load_dataset

    logger.info(f"Loading {num_samples} samples from {dataset_name} ({split} split)...")

    if dataset_name == "cnn_dailymail":
        ds = load_dataset("cnn_dailymail", "3.0.0", split=split, trust_remote_code=True)
        article_key = "article"
        summary_key = "highlights"
    elif dataset_name == "xsum":
        ds = load_dataset("xsum", split=split, trust_remote_code=True)
        article_key = "document"
        summary_key = "summary"
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Use 'cnn_dailymail' or 'xsum'.")

    # Select samples (deterministic — use first N from the split)
    samples = []
    for i in range(min(num_samples, len(ds))):
        samples.append({
            "article": ds[i][article_key],
            "reference_summary": ds[i][summary_key],
        })

    logger.info(f"Loaded {len(samples)} samples")
    return samples


class ExperimentRunner:
    """Orchestrates a dataset experiment: load data → summarize → evaluate → export."""

    def __init__(self):
        self.experiments: dict[str, dict[str, Any]] = {}

    def run_experiment(
        self,
        dataset: str = "cnn_dailymail",
        num_samples: int = 5,
        models: list[str] | None = None,
        include_llm: bool = False,
        max_length: int = 150,
        min_length: int = 30,
        on_progress: Any = None,
    ) -> dict[str, Any]:
        """Run a complete experiment.
        
        Args:
            dataset: Dataset name ("cnn_dailymail" or "xsum")
            num_samples: Number of samples
            models: List of model names to use. Defaults to all local models.
            include_llm: Whether to include the LLM model (requires API key)
            max_length: Max summary length
            min_length: Min summary length
            on_progress: Optional callback(progress: float, message: str)
            
        Returns:
            Complete experiment results dict.
        """
        experiment_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        device = "cuda" if torch.cuda.is_available() else "cpu"

        if models is None:
            models = ["t5", "bart", "pegasus"]
        if include_llm and "llm" not in models:
            models.append("llm")

        logger.info(
            f"Starting experiment {experiment_id}: "
            f"dataset={dataset}, samples={num_samples}, models={models}"
        )

        # Track progress
        self.experiments[experiment_id] = {
            "status": "running",
            "progress": 0.0,
            "current_step": "Loading dataset",
            "total_samples": num_samples,
            "completed_samples": 0,
            "errors": [],
        }

        def update_progress(progress: float, step: str):
            self.experiments[experiment_id]["progress"] = progress
            self.experiments[experiment_id]["current_step"] = step
            if on_progress:
                on_progress(progress, step)

        try:
            # Load dataset
            update_progress(0.05, "Loading dataset...")
            samples = load_dataset_samples(dataset, num_samples)

            # Run summarization for each sample × model
            results = []
            total_steps = len(samples) * len(models)
            completed_steps = 0

            for sample_idx, sample in enumerate(samples):
                article = sample["article"]
                reference = sample["reference_summary"]

                for model_name in models:
                    step_label = f"Sample {sample_idx+1}/{len(samples)}, Model: {model_name}"
                    update_progress(
                        0.1 + 0.8 * (completed_steps / total_steps),
                        step_label,
                    )

                    result_entry = {
                        "sample_index": sample_idx,
                        "model": model_name,
                        "article_words": len(article.split()),
                        "reference_words": len(reference.split()),
                    }

                    try:
                        summarizer = get_summarizer(model_name)
                        gen_result = summarizer.summarize(
                            article,
                            max_length=max_length,
                            min_length=min_length,
                            num_beams=4,
                        )

                        summary = gen_result["summary"]
                        result_entry["summary"] = summary
                        result_entry["summary_words"] = gen_result.get("word_count", len(summary.split()))
                        result_entry["generation_time"] = gen_result["generation_time_seconds"]
                        result_entry["was_chunked"] = gen_result.get("was_chunked", False)
                        result_entry["status"] = "success"

                        # Compute ROUGE
                        try:
                            rouge = compute_rouge(summary, reference)
                            result_entry["rouge_1"] = rouge.rouge_1
                            result_entry["rouge_2"] = rouge.rouge_2
                            result_entry["rouge_l"] = rouge.rouge_l
                        except Exception as e:
                            logger.warning(f"ROUGE failed for {model_name} sample {sample_idx}: {e}")
                            result_entry["rouge_1"] = None
                            result_entry["rouge_2"] = None
                            result_entry["rouge_l"] = None

                    except Exception as e:
                        logger.error(f"Model {model_name} failed on sample {sample_idx}: {e}")
                        result_entry["status"] = "error"
                        result_entry["error"] = str(e)
                        self.experiments[experiment_id]["errors"].append(
                            f"{model_name} sample {sample_idx}: {str(e)}"
                        )

                    results.append(result_entry)
                    completed_steps += 1
                    self.experiments[experiment_id]["completed_samples"] = sample_idx + 1

                    # Rate limit delay for LLM calls
                    if model_name == "llm":
                        time.sleep(settings.GROQ_RETRY_DELAY)

            # Compute aggregate scores
            update_progress(0.95, "Computing aggregate scores...")
            aggregate = self._compute_aggregates(results, models)

            execution_time = time.time() - start_time

            experiment_result = {
                "experiment_id": experiment_id,
                "dataset": dataset,
                "num_samples": len(samples),
                "models": models,
                "results": results,
                "aggregate_scores": aggregate,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time_seconds": round(execution_time, 2),
                "device": device,
                "generation_params": {
                    "max_length": max_length,
                    "min_length": min_length,
                },
            }

            # Save results
            update_progress(0.98, "Saving results...")
            output_path = self._save_results(experiment_id, experiment_result)
            experiment_result["output_path"] = str(output_path)

            # Mark complete
            self.experiments[experiment_id]["status"] = "completed"
            self.experiments[experiment_id]["progress"] = 1.0
            self.experiments[experiment_id]["current_step"] = "Completed"

            logger.info(
                f"Experiment {experiment_id} completed in {execution_time:.1f}s. "
                f"Results saved to {output_path}"
            )

            return experiment_result

        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {e}")
            self.experiments[experiment_id]["status"] = "failed"
            self.experiments[experiment_id]["current_step"] = f"Failed: {str(e)}"
            raise

    def _compute_aggregates(
        self, results: list[dict], models: list[str]
    ) -> dict[str, Any]:
        """Compute aggregate ROUGE scores and timing per model."""
        aggregate = {}

        for model_name in models:
            model_results = [
                r for r in results
                if r.get("model") == model_name and r.get("status") == "success"
            ]

            if not model_results:
                aggregate[model_name] = {"status": "no_successful_runs"}
                continue

            rouge_1_scores = [r["rouge_1"] for r in model_results if r.get("rouge_1") is not None]
            rouge_2_scores = [r["rouge_2"] for r in model_results if r.get("rouge_2") is not None]
            rouge_l_scores = [r["rouge_l"] for r in model_results if r.get("rouge_l") is not None]
            gen_times = [r["generation_time"] for r in model_results if r.get("generation_time") is not None]

            aggregate[model_name] = {
                "num_samples": len(model_results),
                "avg_rouge_1": round(sum(rouge_1_scores) / len(rouge_1_scores), 4) if rouge_1_scores else None,
                "avg_rouge_2": round(sum(rouge_2_scores) / len(rouge_2_scores), 4) if rouge_2_scores else None,
                "avg_rouge_l": round(sum(rouge_l_scores) / len(rouge_l_scores), 4) if rouge_l_scores else None,
                "avg_generation_time": round(sum(gen_times) / len(gen_times), 3) if gen_times else None,
                "total_generation_time": round(sum(gen_times), 3) if gen_times else None,
            }

        return aggregate

    def _save_results(self, experiment_id: str, results: dict) -> Path:
        """Save experiment results to JSON and CSV files."""
        output_dir = Path(settings.OUTPUT_DIR) / "experiments" / f"experiment_{experiment_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save full results as JSON
        json_path = output_dir / "results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        # Save per-sample results as CSV
        if results.get("results"):
            df = pd.DataFrame(results["results"])
            csv_path = output_dir / "results.csv"
            df.to_csv(csv_path, index=False)

            # Create summary comparison CSV
            summary_df = df[df["status"] == "success"].groupby("model").agg({
                "rouge_1": "mean",
                "rouge_2": "mean",
                "rouge_l": "mean",
                "generation_time": "mean",
                "summary_words": "mean",
            }).round(4)
            summary_csv_path = output_dir / "summary_comparison.csv"
            summary_df.to_csv(summary_csv_path)

        logger.info(f"Results saved to {output_dir}")
        return output_dir

    def get_status(self, experiment_id: str) -> dict[str, Any] | None:
        """Get the current status of an experiment."""
        return self.experiments.get(experiment_id)


# Module-level singleton
experiment_runner = ExperimentRunner()
