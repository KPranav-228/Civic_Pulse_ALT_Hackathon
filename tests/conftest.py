"""Test fixtures and mocks for the News Summarizer test suite.

All tests run without a live LLM API key or internet access.
Models are mocked to avoid downloading large checkpoints during testing.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def sample_article():
    """A sample news article for testing."""
    return (
        "The Federal Reserve announced Wednesday that it will maintain its benchmark "
        "interest rate at the current level, signaling a cautious approach amid mixed "
        "economic signals. Fed Chair Jerome Powell stated that while inflation has shown "
        "signs of moderating, the central bank remains committed to its 2% inflation target. "
        "The decision was widely expected by markets, with most economists predicting a hold. "
        "Powell noted that the labor market remains robust, with unemployment at historically "
        "low levels, but acknowledged concerns about potential headwinds from global trade "
        "tensions. The committee indicated it would continue to monitor incoming data before "
        "making any adjustments to monetary policy. Financial markets reacted positively to "
        "the announcement, with major indices closing higher."
    )


@pytest.fixture
def short_article():
    """An article that's too short for validation."""
    return "This is too short."


@pytest.fixture
def sample_summary():
    """A sample generated summary."""
    return (
        "The Federal Reserve held interest rates steady amid mixed economic signals. "
        "Chair Powell noted moderating inflation but commitment to 2% target."
    )


@pytest.fixture
def reference_summary():
    """A reference summary for ROUGE evaluation."""
    return (
        "The Fed maintained its benchmark rate as expected, with Chair Powell citing "
        "moderating inflation and a robust labor market while noting global trade concerns."
    )


@pytest.fixture
def mock_model_manager():
    """Mock the model manager to avoid loading real models."""
    with patch("backend.services.model_manager.model_manager") as mock_mm:
        mock_mm.loaded_models = []
        mock_mm.device = MagicMock()
        mock_mm.device.type = "cpu"
        mock_mm.device.__str__ = lambda x: "cpu"
        mock_mm.get_status.return_value = "available"
        mock_mm.is_loaded.return_value = False
        yield mock_mm


@pytest.fixture
def mock_summarizer_result():
    """Standard mock result from a summarizer."""
    return {
        "summary": "The Fed held rates steady amid mixed signals about inflation and employment.",
        "generation_time_seconds": 2.5,
        "was_chunked": False,
        "num_chunks": 1,
        "word_count": 13,
        "metadata": {},
    }


@pytest.fixture
def client():
    """FastAPI test client with mocked model dependencies."""
    # Patch heavy imports before importing the app
    with patch("backend.api.routes.model_manager") as mock_mm:
        mock_mm.loaded_models = []
        mock_mm.get_status.return_value = "available"

        from backend.main import app
        with TestClient(app) as c:
            yield c
