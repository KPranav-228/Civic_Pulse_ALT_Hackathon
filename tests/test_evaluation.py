"""Tests for ROUGE evaluation service."""

import pytest
from backend.services.evaluation import (
    compute_rouge,
    evaluate_summary,
    evaluate_multiple,
    compute_comparison,
)
from backend.schemas.models import RougeScores, QualitativeScore


class TestComputeRouge:
    def test_valid_rouge(self, sample_summary, reference_summary):
        scores = compute_rouge(sample_summary, reference_summary)
        assert isinstance(scores, RougeScores)
        assert 0.0 <= scores.rouge_1 <= 1.0
        assert 0.0 <= scores.rouge_2 <= 1.0
        assert 0.0 <= scores.rouge_l <= 1.0

    def test_identical_texts(self):
        text = "The quick brown fox jumps over the lazy dog."
        scores = compute_rouge(text, text)
        assert scores.rouge_1 == 1.0
        assert scores.rouge_l == 1.0

    def test_completely_different(self):
        scores = compute_rouge(
            "Alpha beta gamma delta epsilon.",
            "One two three four five six seven.",
        )
        assert scores.rouge_1 < 0.5
        assert scores.rouge_2 < 0.3

    def test_empty_summary_raises(self, reference_summary):
        with pytest.raises(ValueError, match="Summary text cannot be empty"):
            compute_rouge("", reference_summary)

    def test_empty_reference_raises(self, sample_summary):
        with pytest.raises(ValueError, match="Reference summary cannot be empty"):
            compute_rouge(sample_summary, "")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            compute_rouge("   ", "Valid reference text here.")


class TestEvaluateSummary:
    def test_with_reference(self, sample_summary, reference_summary):
        result = evaluate_summary(sample_summary, reference_summary, "t5")
        assert result.model == "t5"
        assert result.rouge is not None
        assert result.message is None

    def test_without_reference(self, sample_summary):
        result = evaluate_summary(sample_summary, None, "t5")
        assert result.rouge is None
        assert "ROUGE requires a reference" in result.message

    def test_with_qualitative(self, sample_summary, reference_summary):
        qual = QualitativeScore(coherence=4, readability=5, factual_consistency=3, semantic_relevance=4)
        result = evaluate_summary(sample_summary, reference_summary, "t5", qualitative=qual)
        assert result.qualitative is not None
        assert result.qualitative.coherence == 4


class TestEvaluateMultiple:
    def test_multiple_models(self, reference_summary):
        summaries = {
            "t5": "The Fed held rates amid mixed signals.",
            "bart": "Federal Reserve maintains benchmark interest rate.",
            "pegasus": "Central bank keeps rates steady.",
        }
        results = evaluate_multiple(summaries, reference_summary)
        assert len(results) == 3
        assert all(r.rouge is not None for r in results)
        assert {r.model for r in results} == {"t5", "bart", "pegasus"}

    def test_without_reference(self):
        summaries = {"t5": "Summary one.", "bart": "Summary two."}
        results = evaluate_multiple(summaries, None)
        assert len(results) == 2
        assert all(r.rouge is None for r in results)


class TestComputeComparison:
    def test_with_rouge(self):
        summaries = [
            {"model": "t5", "status": "success", "generation_time_seconds": 2.0,
             "word_count": 20, "compression_ratio": 0.1},
            {"model": "bart", "status": "success", "generation_time_seconds": 5.0,
             "word_count": 25, "compression_ratio": 0.12},
        ]
        from backend.schemas.models import EvaluationResult, RougeScores
        evaluations = [
            EvaluationResult(model="t5", rouge=RougeScores(rouge_1=0.4, rouge_2=0.2, rouge_l=0.35)),
            EvaluationResult(model="bart", rouge=RougeScores(rouge_1=0.5, rouge_2=0.25, rouge_l=0.42)),
        ]
        result = compute_comparison(summaries, evaluations, 200)
        assert result["best_model"] == "bart"  # Higher ROUGE-L
        assert "BART" in result["analysis"]
        assert len(result["rankings"]) == 2

    def test_without_rouge(self):
        summaries = [
            {"model": "t5", "status": "success", "generation_time_seconds": 2.0,
             "word_count": 20, "compression_ratio": 0.1},
            {"model": "bart", "status": "success", "generation_time_seconds": 5.0,
             "word_count": 25, "compression_ratio": 0.12},
        ]
        result = compute_comparison(summaries, [], 200)
        assert result["best_model"] == "t5"  # Faster generation time
        assert "fastest" in result["analysis"].lower()

    def test_no_successful_summaries(self):
        summaries = [
            {"model": "t5", "status": "error", "error": "Failed"},
        ]
        result = compute_comparison(summaries, [], 200)
        assert result["best_model"] is None
        assert "No successful" in result["analysis"]
