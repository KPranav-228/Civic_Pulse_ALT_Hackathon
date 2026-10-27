"""Tests for API endpoints — uses mocked models to avoid downloads."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    """Create a test client with all model dependencies mocked."""
    with patch("backend.services.model_manager.ModelManager") as MockMM:
        mock_instance = MagicMock()
        mock_instance.loaded_models = []
        mock_instance.device = MagicMock()
        mock_instance.device.type = "cpu"
        mock_instance.get_status.return_value = "available"
        mock_instance.is_loaded.return_value = False
        MockMM.return_value = mock_instance

        from backend.main import app
        with TestClient(app) as client:
            yield client


class TestHealthEndpoint:
    def test_health_returns_ok(self, api_client):
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "device" in data
        assert "version" in data
        assert "available_models" in data

    def test_health_device_field(self, api_client):
        response = api_client.get("/api/health")
        data = response.json()
        assert data["device"] in ("cpu", "cuda")


class TestModelsEndpoint:
    def test_list_models(self, api_client):
        response = api_client.get("/api/models")
        assert response.status_code == 200
        models = response.json()
        assert len(models) == 4
        names = {m["name"] for m in models}
        assert names == {"t5", "bart", "pegasus", "llm"}

    def test_model_info_fields(self, api_client):
        response = api_client.get("/api/models")
        for model in response.json():
            assert "name" in model
            assert "display_name" in model
            assert "checkpoint" in model
            assert "status" in model
            assert "is_local" in model
            assert "max_input_tokens" in model


class TestSummarizeEndpoint:
    def test_validation_article_too_short(self, api_client):
        response = api_client.post("/api/summarize", json={
            "article_text": "Too short"
        })
        assert response.status_code == 422  # Validation error

    def test_validation_invalid_model(self, api_client):
        response = api_client.post("/api/summarize", json={
            "article_text": "A" * 100,
            "models": ["nonexistent"]
        })
        assert response.status_code == 422

    def test_summarize_with_mocked_summarizer(self, api_client):
        """Test the summarize endpoint with a mocked summarizer."""
        mock_result = {
            "summary": "Test summary for the article.",
            "generation_time_seconds": 1.5,
            "was_chunked": False,
            "num_chunks": 1,
            "word_count": 5,
            "metadata": {},
        }
        
        with patch("backend.api.routes.get_summarizer") as mock_get:
            mock_summarizer = MagicMock()
            mock_summarizer.summarize.return_value = mock_result
            mock_get.return_value = mock_summarizer

            response = api_client.post("/api/summarize", json={
                "article_text": "A" * 100,
                "models": ["t5"],
            })
            assert response.status_code == 200
            data = response.json()
            assert "summaries" in data
            assert len(data["summaries"]) == 1
            assert data["summaries"][0]["status"] == "success"
            assert data["summaries"][0]["summary"] == "Test summary for the article."

    def test_model_failure_doesnt_crash(self, api_client):
        """One model failing should not break others."""
        mock_success = {
            "summary": "Working summary.",
            "generation_time_seconds": 1.0,
            "was_chunked": False,
            "num_chunks": 1,
            "word_count": 2,
            "metadata": {},
        }

        def mock_get(name):
            mock = MagicMock()
            if name == "t5":
                mock.summarize.return_value = mock_success
            else:
                mock.summarize.side_effect = RuntimeError("Model failed")
            return mock

        with patch("backend.api.routes.get_summarizer", side_effect=mock_get):
            response = api_client.post("/api/summarize", json={
                "article_text": "A" * 100,
                "models": ["t5", "bart"],
            })
            assert response.status_code == 200
            data = response.json()
            assert len(data["summaries"]) == 2
            t5_result = next(s for s in data["summaries"] if s["model"] == "t5")
            bart_result = next(s for s in data["summaries"] if s["model"] == "bart")
            assert t5_result["status"] == "success"
            assert bart_result["status"] == "error"


class TestEvaluateEndpoint:
    def test_valid_evaluation(self, api_client):
        response = api_client.post("/api/evaluate", json={
            "summary": "The Fed held rates steady.",
            "reference_summary": "Federal Reserve maintained benchmark rate.",
        })
        assert response.status_code == 200
        data = response.json()
        assert "rouge" in data
        assert "rouge_1" in data["rouge"]
        assert 0 <= data["rouge"]["rouge_1"] <= 1

    def test_empty_summary_rejected(self, api_client):
        response = api_client.post("/api/evaluate", json={
            "summary": "",
            "reference_summary": "Some reference text.",
        })
        assert response.status_code == 422


class TestRootEndpoint:
    def test_root(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
