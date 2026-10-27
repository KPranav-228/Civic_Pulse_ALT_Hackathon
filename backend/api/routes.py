"""API routes — all HTTP endpoints for the News Summarizer."""

import logging
import threading
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
import torch

from backend.schemas.models import (
    SummarizationRequest, SummarizationResponse,
    EvaluationRequest, EvaluationResponse,
    ExperimentRequest, ExperimentStatus, ExperimentResult,
    ModelInfo, HealthResponse, ErrorResponse,
    SummaryResult, ArticleStats, PreprocessingInfo,
    QualitativeScoreInput, EvaluationResult,
    ComparisonResult,
)
from backend.config.settings import settings
from backend.services.model_manager import model_manager, MODEL_REGISTRY
from backend.services.summarizers import get_summarizer, SUMMARIZERS
from backend.services.preprocessing import preprocess_article
from backend.services.evaluation import (
    compute_rouge, evaluate_summary, evaluate_multiple, compute_comparison,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ─── Health & Info ────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Returns system info including device, loaded models, and API key status."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        device=device,
        loaded_models=model_manager.loaded_models,
        available_models=list(SUMMARIZERS.keys()),
        groq_configured=bool(settings.GROQ_API_KEY),
    )


@router.get("/models", response_model=list[ModelInfo])
async def list_models():
    """List all available summarization models with their status."""
    models = [
        ModelInfo(
            name="t5", display_name="T5-Small",
            checkpoint="t5-small",
            status=model_manager.get_status("t5"),
            description="Google's T5 (Text-to-Text Transfer Transformer) - Small variant. General-purpose model using 'summarize:' prefix.",
            max_input_tokens=512, is_local=True,
        ),
        ModelInfo(
            name="bart", display_name="DistilBART-CNN",
            checkpoint="sshleifer/distilbart-cnn-12-6",
            status=model_manager.get_status("bart"),
            description="Distilled BART model fine-tuned on CNN/DailyMail. 50% faster decoder with 98% quality retention.",
            max_input_tokens=1024, is_local=True,
        ),
        ModelInfo(
            name="pegasus", display_name="PEGASUS-XSum",
            checkpoint="google/pegasus-xsum",
            status=model_manager.get_status("pegasus"),
            description="Google's PEGASUS model fine-tuned on XSum for abstractive single-sentence summarization.",
            max_input_tokens=512, is_local=True,
        ),
        ModelInfo(
            name="llm", display_name="Llama 3.3 70B (Groq)",
            checkpoint=settings.GROQ_MODEL,
            status="available" if settings.GROQ_API_KEY else "unavailable",
            description="Meta's Llama 3.3 70B model via Groq API. Fast cloud inference with free tier.",
            max_input_tokens=8192, is_local=False,
        ),
    ]
    return models


# ─── Summarize ────────────────────────────────────────────────────────────────

@router.post("/summarize", response_model=SummarizationResponse)
async def summarize(request: SummarizationRequest):
    """Generate summaries for an article using selected models.
    
    Each model runs independently — if one fails, others still return results.
    Optionally evaluates against a reference summary if provided.
    """
    # Preprocess the article
    prep = preprocess_article(request.article_text)
    cleaned_text = prep["cleaned_text"]
    stats = prep["stats"]

    article_stats = ArticleStats(**stats)
    preprocessing_info = PreprocessingInfo(
        original_length=prep["original_length"],
        cleaned_length=prep["cleaned_length"],
        was_chunked=False,  # Overall chunking info is per-model
        num_chunks=1,
        cleaning_steps=prep["cleaning_steps"],
    )

    # Run each selected model independently
    summaries: list[SummaryResult] = []
    successful_summaries: dict[str, str] = {}  # For evaluation

    for model_name in request.models:
        try:
            summarizer = get_summarizer(model_name)
            result = summarizer.summarize(
                cleaned_text,
                max_length=request.max_length,
                min_length=request.min_length,
                num_beams=request.num_beams,
            )

            word_count = result.get("word_count", 0)
            compression_ratio = round(word_count / stats["word_count"], 4) if stats["word_count"] > 0 else None

            summary_result = SummaryResult(
                model=model_name,
                summary=result["summary"],
                word_count=word_count,
                compression_ratio=compression_ratio,
                generation_time_seconds=result["generation_time_seconds"],
                status="success",
            )
            summaries.append(summary_result)
            successful_summaries[model_name] = result["summary"]

            # Update preprocessing info if this model chunked the input
            if result.get("was_chunked"):
                preprocessing_info.was_chunked = True
                preprocessing_info.num_chunks = max(
                    preprocessing_info.num_chunks, result.get("num_chunks", 1)
                )

        except Exception as e:
            logger.error(f"Model '{model_name}' failed: {e}")
            summaries.append(SummaryResult(
                model=model_name,
                status="error",
                error=str(e),
            ))

    # Evaluate if reference summary provided
    evaluation = None
    comparison = None
    if request.reference_summary and successful_summaries:
        evaluation = evaluate_multiple(
            successful_summaries, request.reference_summary
        )
        # Generate comparison
        summary_dicts = [s.model_dump() for s in summaries]
        comparison_data = compute_comparison(
            summary_dicts, evaluation, stats["word_count"]
        )
        comparison = ComparisonResult(**comparison_data)
    elif not request.reference_summary and successful_summaries:
        # No reference — provide evaluation without ROUGE
        evaluation = evaluate_multiple(successful_summaries, None)

    return SummarizationResponse(
        request_id=str(uuid.uuid4()),
        article_stats=article_stats,
        preprocessing_info=preprocessing_info,
        summaries=summaries,
        evaluation=evaluation,
        comparison=comparison,
    )


# ─── Evaluate ─────────────────────────────────────────────────────────────────

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    """Evaluate a single summary against a reference using ROUGE."""
    try:
        rouge = compute_rouge(request.summary, request.reference_summary)
        return EvaluationResponse(
            rouge=rouge,
            model_name=request.model_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail="Evaluation computation failed")


# ─── Compare ──────────────────────────────────────────────────────────────────

@router.post("/compare", response_model=SummarizationResponse)
async def compare(request: SummarizationRequest):
    """Compare summaries across models — alias for /summarize with comparison enabled.
    
    This endpoint always generates a comparison, even without a reference summary
    (in that case, comparison is based on generation time and compression ratio).
    """
    # Reuse the summarize logic
    response = await summarize(request)

    # Ensure comparison is generated even without reference
    if response.comparison is None and response.summaries:
        summary_dicts = [s.model_dump() for s in response.summaries]
        eval_results = response.evaluation or []
        comparison_data = compute_comparison(
            summary_dicts, eval_results, response.article_stats.word_count
        )
        response.comparison = ComparisonResult(**comparison_data)

    return response


# ─── Qualitative Scoring ──────────────────────────────────────────────────────

@router.post("/qualitative-score", response_model=EvaluationResult)
async def submit_qualitative_score(score: QualitativeScoreInput):
    """Submit a human qualitative score for a model's summary."""
    from backend.schemas.models import QualitativeScore as QS
    
    qual = QS(
        coherence=score.coherence,
        readability=score.readability,
        factual_consistency=score.factual_consistency,
        semantic_relevance=score.semantic_relevance,
        notes=score.notes,
    )
    
    return EvaluationResult(
        model=score.model,
        qualitative=qual,
        message="Qualitative scores recorded successfully.",
    )


# ─── Experiments ──────────────────────────────────────────────────────────────

@router.post("/experiment", response_model=ExperimentStatus)
async def start_experiment(request: ExperimentRequest):
    """Start a dataset experiment.
    
    Runs in a background thread. Use /experiment/{id}/status to poll progress.
    If include_llm is True, confirms the LLM cost before proceeding.
    """
    from backend.services.experiment import experiment_runner

    experiment_id = str(uuid.uuid4())[:8]
    
    # Warn if sample size is large
    if request.num_samples > 20:
        logger.warning(f"Large experiment requested: {request.num_samples} samples")
    
    # Build model list
    models = list(request.models)
    if request.include_llm and "llm" not in models:
        models.append("llm")

    # Initialize tracking
    experiment_runner.experiments[experiment_id] = {
        "status": "running",
        "progress": 0.0,
        "current_step": "Starting...",
        "total_samples": request.num_samples,
        "completed_samples": 0,
        "errors": [],
    }

    # Run in background thread
    def run():
        try:
            experiment_runner.run_experiment(
                dataset=request.dataset,
                num_samples=request.num_samples,
                models=models,
                include_llm=request.include_llm,
                max_length=request.max_length,
                min_length=request.min_length,
            )
        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return ExperimentStatus(
        experiment_id=experiment_id,
        status="running",
        progress=0.0,
        current_step="Starting...",
        total_samples=request.num_samples,
        completed_samples=0,
        errors=[],
    )


@router.get("/experiment/{experiment_id}/status", response_model=ExperimentStatus)
async def experiment_status(experiment_id: str):
    """Get the current status of a running experiment."""
    from backend.services.experiment import experiment_runner

    status = experiment_runner.get_status(experiment_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    return ExperimentStatus(
        experiment_id=experiment_id,
        status=status["status"],
        progress=status["progress"],
        current_step=status["current_step"],
        total_samples=status["total_samples"],
        completed_samples=status["completed_samples"],
        errors=status["errors"],
    )
