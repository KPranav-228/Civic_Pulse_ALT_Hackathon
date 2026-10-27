"""Tests for Pydantic schemas — validation, constraints, edge cases."""

import pytest
from pydantic import ValidationError
from backend.schemas.models import (
    SummarizationRequest,
    ExperimentRequest,
    EvaluationRequest,
    QualitativeScoreInput,
    ArticleStats,
    SummaryResult,
    RougeScores,
    HealthResponse,
    ModelInfo,
)


class TestSummarizationRequest:
    def test_valid_request(self, sample_article):
        req = SummarizationRequest(article_text=sample_article)
        assert req.article_text == sample_article
        assert req.models == ["t5", "bart", "pegasus", "llm"]
        assert req.max_length == 150
        assert req.min_length == 30
        assert req.num_beams == 4

    def test_custom_models(self, sample_article):
        req = SummarizationRequest(article_text=sample_article, models=["t5", "bart"])
        assert req.models == ["t5", "bart"]

    def test_invalid_model_name(self, sample_article):
        with pytest.raises(ValidationError, match="Invalid model"):
            SummarizationRequest(article_text=sample_article, models=["invalid"])

    def test_empty_models_list(self, sample_article):
        with pytest.raises(ValidationError, match="At least one model"):
            SummarizationRequest(article_text=sample_article, models=[])

    def test_article_too_short(self):
        with pytest.raises(ValidationError):
            SummarizationRequest(article_text="Too short")

    def test_min_length_exceeds_max(self, sample_article):
        with pytest.raises(ValidationError, match="min_length must be less"):
            SummarizationRequest(article_text=sample_article, max_length=50, min_length=60)

    def test_num_beams_range(self, sample_article):
        with pytest.raises(ValidationError):
            SummarizationRequest(article_text=sample_article, num_beams=0)
        with pytest.raises(ValidationError):
            SummarizationRequest(article_text=sample_article, num_beams=11)

    def test_reference_summary_optional(self, sample_article, reference_summary):
        req = SummarizationRequest(article_text=sample_article, reference_summary=reference_summary)
        assert req.reference_summary == reference_summary

        req2 = SummarizationRequest(article_text=sample_article)
        assert req2.reference_summary is None


class TestExperimentRequest:
    def test_defaults(self):
        req = ExperimentRequest()
        assert req.dataset == "cnn_dailymail"
        assert req.num_samples == 5
        assert req.include_llm is False

    def test_invalid_dataset(self):
        with pytest.raises(ValidationError):
            ExperimentRequest(dataset="invalid_dataset")

    def test_sample_range(self):
        with pytest.raises(ValidationError):
            ExperimentRequest(num_samples=0)
        with pytest.raises(ValidationError):
            ExperimentRequest(num_samples=101)


class TestEvaluationRequest:
    def test_valid(self, sample_summary, reference_summary):
        req = EvaluationRequest(summary=sample_summary, reference_summary=reference_summary)
        assert req.summary == sample_summary

    def test_empty_summary(self, reference_summary):
        with pytest.raises(ValidationError):
            EvaluationRequest(summary="", reference_summary=reference_summary)


class TestQualitativeScoreInput:
    def test_valid_scores(self):
        score = QualitativeScoreInput(
            model="t5", coherence=4, readability=5,
            factual_consistency=3, semantic_relevance=4,
        )
        assert score.coherence == 4

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            QualitativeScoreInput(
                model="t5", coherence=6, readability=5,
                factual_consistency=3, semantic_relevance=4,
            )
        with pytest.raises(ValidationError):
            QualitativeScoreInput(
                model="t5", coherence=0, readability=5,
                factual_consistency=3, semantic_relevance=4,
            )


class TestResponseModels:
    def test_article_stats(self):
        stats = ArticleStats(char_count=500, word_count=100, sentence_count=5, estimated_tokens=130)
        assert stats.word_count == 100

    def test_summary_result_success(self):
        result = SummaryResult(
            model="t5", summary="Test summary", word_count=2,
            compression_ratio=0.02, generation_time_seconds=1.5, status="success",
        )
        assert result.status == "success"
        assert result.error is None

    def test_summary_result_error(self):
        result = SummaryResult(model="t5", status="error", error="Model failed to load")
        assert result.summary is None
        assert result.error == "Model failed to load"

    def test_rouge_scores(self):
        scores = RougeScores(rouge_1=0.45, rouge_2=0.22, rouge_l=0.38)
        assert scores.rouge_l == 0.38
