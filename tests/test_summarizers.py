"""Tests for summarizer interface and mocked implementations."""

import pytest
from unittest.mock import patch, MagicMock
from backend.services.summarizers import (
    get_summarizer,
    T5Summarizer,
    BARTSummarizer,
    PegasusSummarizer,
    LLMSummarizer,
    SUMMARIZERS,
)


class TestSummarizerFactory:
    def test_get_valid_summarizer(self):
        for name in ["t5", "bart", "pegasus", "llm"]:
            summarizer = get_summarizer(name)
            assert summarizer is not None
            assert summarizer.name == name

    def test_get_invalid_summarizer(self):
        with pytest.raises(ValueError, match="Unknown summarizer"):
            get_summarizer("nonexistent")

    def test_all_summarizers_registered(self):
        assert set(SUMMARIZERS.keys()) == {"t5", "bart", "pegasus", "llm"}


class TestT5Summarizer:
    def test_prepare_input_adds_prefix(self):
        t5 = T5Summarizer()
        result = t5._prepare_input("Hello world")
        assert result == "summarize: Hello world"

    def test_name_and_key(self):
        t5 = T5Summarizer()
        assert t5.name == "t5"
        assert t5.model_key == "t5"
        assert t5.is_local is True


class TestBARTSummarizer:
    def test_no_prefix(self):
        bart = BARTSummarizer()
        result = bart._prepare_input("Hello world")
        assert result == "Hello world"  # No prefix for BART

    def test_name_and_key(self):
        bart = BARTSummarizer()
        assert bart.name == "bart"
        assert bart.model_key == "bart"


class TestPegasusSummarizer:
    def test_name_and_key(self):
        peg = PegasusSummarizer()
        assert peg.name == "pegasus"
        assert peg.model_key == "pegasus"


class TestLLMSummarizer:
    def test_name_and_not_local(self):
        llm = LLMSummarizer()
        assert llm.name == "llm"
        assert llm.is_local is False

    def test_no_api_key_raises(self):
        llm = LLMSummarizer()
        with patch("backend.config.settings.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = ""
            with pytest.raises(RuntimeError, match="Groq API key not configured"):
                llm._get_client()

    def test_system_prompt_exists(self):
        llm = LLMSummarizer()
        assert len(llm.SYSTEM_PROMPT) > 100
        assert "factual" in llm.SYSTEM_PROMPT.lower()
        assert "hallucination" in llm.SYSTEM_PROMPT.lower() or "not introduce" in llm.SYSTEM_PROMPT.lower()

    def test_summarize_with_mocked_groq(self):
        """Test LLM summarizer with mocked Groq client."""
        llm = LLMSummarizer()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test summary from the LLM."

        with patch("backend.config.settings.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"
            mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
            mock_settings.GROQ_MAX_RETRIES = 1
            mock_settings.GROQ_RETRY_DELAY = 0.1

            with patch("backend.services.summarizers.settings", mock_settings):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response

                with patch.object(llm, "_get_client", return_value=mock_client):
                    result = llm.summarize("This is a test article " * 20, max_length=50)
                    assert result["summary"] == "This is a test summary from the LLM."
                    assert result["generation_time_seconds"] >= 0
                    assert result["was_chunked"] is False
