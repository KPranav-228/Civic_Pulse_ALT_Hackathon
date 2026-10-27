"""Evaluation service — ROUGE computation and qualitative scoring.

Uses Google's rouge-score library for ROUGE-1, ROUGE-2, ROUGE-L.
Qualitative scores are human-assigned through the UI (stored but not auto-generated).
"""

import logging
from typing import Any

from rouge_score import rouge_scorer

from backend.schemas.models import RougeScores, EvaluationResult, QualitativeScore

logger = logging.getLogger(__name__)

# Reusable scorer instance (thread-safe for reads)
_scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)


def compute_rouge(summary: str, reference: str) -> RougeScores:
    """Compute ROUGE-1, ROUGE-2, ROUGE-L F1 scores.
    
    Args:
        summary: The generated summary text.
        reference: The reference (gold) summary text.
        
    Returns:
        RougeScores with F1 values for each metric.
        
    Raises:
        ValueError: If summary or reference is empty.
    """
    if not summary or not summary.strip():
        raise ValueError("Summary text cannot be empty for ROUGE evaluation")
    if not reference or not reference.strip():
        raise ValueError("Reference summary cannot be empty for ROUGE evaluation")

    scores = _scorer.score(reference, summary)

    return RougeScores(
        rouge_1=round(scores["rouge1"].fmeasure, 4),
        rouge_2=round(scores["rouge2"].fmeasure, 4),
        rouge_l=round(scores["rougeL"].fmeasure, 4),
    )


def evaluate_summary(
    summary: str,
    reference: str | None,
    model_name: str,
    qualitative: QualitativeScore | None = None,
) -> EvaluationResult:
    """Evaluate a single summary against an optional reference.
    
    Args:
        summary: The generated summary text.
        reference: Optional reference summary for ROUGE. If None, only qualitative scores are returned.
        model_name: Name of the model that generated the summary.
        qualitative: Optional qualitative scores (human-assigned).
        
    Returns:
        EvaluationResult with ROUGE scores (if reference provided) and qualitative scores (if provided).
    """
    rouge = None
    message = None

    if reference and reference.strip():
        try:
            rouge = compute_rouge(summary, reference)
        except Exception as e:
            logger.error(f"ROUGE computation failed for model '{model_name}': {e}")
            message = f"ROUGE computation error: {str(e)}"
    else:
        message = "ROUGE requires a reference summary for quantitative comparison."

    return EvaluationResult(
        model=model_name,
        rouge=rouge,
        qualitative=qualitative,
        message=message,
    )


def evaluate_multiple(
    summaries: dict[str, str],
    reference: str | None,
    qualitative_scores: dict[str, QualitativeScore] | None = None,
) -> list[EvaluationResult]:
    """Evaluate multiple model summaries against a reference.
    
    Args:
        summaries: Dict mapping model_name -> summary_text.
        reference: Optional reference summary.
        qualitative_scores: Optional dict mapping model_name -> QualitativeScore.
        
    Returns:
        List of EvaluationResult, one per model.
    """
    results = []
    for model_name, summary_text in summaries.items():
        qual = qualitative_scores.get(model_name) if qualitative_scores else None
        result = evaluate_summary(summary_text, reference, model_name, qualitative=qual)
        results.append(result)
    return results


def compute_comparison(
    summaries: list[dict[str, Any]],
    evaluations: list[EvaluationResult],
    article_word_count: int,
) -> dict[str, Any]:
    """Generate a comparative analysis from evaluation results.
    
    Rankings and analysis text are derived ONLY from actual measured data.
    Never invents or assumes metrics.
    
    Args:
        summaries: List of SummaryResult-like dicts with model, generation_time, word_count, etc.
        evaluations: List of EvaluationResult from evaluate_multiple().
        article_word_count: Word count of the original article (for compression ratio context).
        
    Returns:
        Dict with rankings, best_model, and analysis text.
    """
    # Build a combined view: model -> metrics
    model_metrics: dict[str, dict[str, Any]] = {}
    
    for s in summaries:
        model = s.get("model", "unknown")
        if s.get("status") != "success":
            continue
        model_metrics[model] = {
            "generation_time": s.get("generation_time_seconds"),
            "word_count": s.get("word_count"),
            "compression_ratio": s.get("compression_ratio"),
        }

    # Add ROUGE scores from evaluations
    for e in evaluations:
        if e.model in model_metrics and e.rouge:
            model_metrics[e.model]["rouge_1"] = e.rouge.rouge_1
            model_metrics[e.model]["rouge_2"] = e.rouge.rouge_2
            model_metrics[e.model]["rouge_l"] = e.rouge.rouge_l

    if not model_metrics:
        return {
            "rankings": [],
            "best_model": None,
            "analysis": "No successful summaries to compare.",
        }

    # Build rankings — sort by ROUGE-L if available, else by generation time (faster = better)
    has_rouge = any("rouge_l" in m for m in model_metrics.values())

    rankings = []
    for model, metrics in model_metrics.items():
        entry = {"model": model, **metrics}
        rankings.append(entry)

    if has_rouge:
        rankings.sort(key=lambda x: x.get("rouge_l", 0), reverse=True)
        sort_key = "ROUGE-L"
    else:
        rankings.sort(key=lambda x: x.get("generation_time", float("inf")))
        sort_key = "generation time"

    best_model = rankings[0]["model"] if rankings else None

    # Generate analysis text from real data only
    analysis_parts = []
    analysis_parts.append(f"Comparison of {len(rankings)} models, ranked by {sort_key}.")

    if has_rouge and best_model:
        best_rouge_l = model_metrics[best_model].get("rouge_l")
        if best_rouge_l is not None:
            analysis_parts.append(
                f"{best_model.upper()} achieved the highest ROUGE-L score ({best_rouge_l:.4f})."
            )

    # Fastest model
    times = {m: d.get("generation_time") for m, d in model_metrics.items() if d.get("generation_time") is not None}
    if times:
        fastest = min(times, key=times.get)  # type: ignore
        analysis_parts.append(
            f"{fastest.upper()} was the fastest ({times[fastest]:.2f}s)."
        )

    # Compression info
    ratios = {m: d.get("compression_ratio") for m, d in model_metrics.items() if d.get("compression_ratio") is not None}
    if ratios:
        most_compressed = min(ratios, key=ratios.get)  # type: ignore
        analysis_parts.append(
            f"{most_compressed.upper()} produced the most compressed summary "
            f"(ratio: {ratios[most_compressed]:.2f})."
        )

    return {
        "rankings": rankings,
        "best_model": best_model,
        "analysis": " ".join(analysis_parts),
    }
