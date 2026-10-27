"""Tests for the preprocessing service — cleaning, stats, chunking."""

import pytest
from backend.services.preprocessing import (
    clean_text,
    compute_article_stats,
    chunk_text,
    preprocess_article,
)


class TestCleanText:
    def test_basic_cleaning(self, sample_article):
        cleaned, steps = clean_text(sample_article)
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
        assert "Normalized whitespace" in steps

    def test_html_removal(self):
        text = "<p>Hello <b>world</b></p> This is a test."
        cleaned, steps = clean_text(text)
        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
        assert "Hello world This is a test." in cleaned
        assert "Removed HTML tags" in steps

    def test_url_removal(self):
        text = "Visit https://example.com for more info. Also check www.test.org please."
        cleaned, steps = clean_text(text)
        assert "https://example.com" not in cleaned
        assert "www.test.org" not in cleaned
        assert "Removed URLs" in steps

    def test_email_removal(self):
        text = "Contact us at info@example.com for details."
        cleaned, steps = clean_text(text)
        assert "info@example.com" not in cleaned
        assert "Removed email addresses" in steps

    def test_whitespace_normalization(self):
        text = "Hello    world\n\n\twith   extra   spaces."
        cleaned, steps = clean_text(text)
        assert "  " not in cleaned
        assert "Normalized whitespace" in steps

    def test_wrapping_quotes(self):
        text = '"This is an article wrapped in quotes."'
        cleaned, steps = clean_text(text)
        assert not cleaned.startswith('"')
        assert not cleaned.endswith('"')
        assert "Removed wrapping quotes" in steps

    def test_empty_input(self):
        cleaned, steps = clean_text("")
        assert cleaned == ""

    def test_already_clean(self):
        text = "This is already clean text with no issues."
        cleaned, steps = clean_text(text)
        assert cleaned == text
        assert "Normalized whitespace" in steps


class TestComputeArticleStats:
    def test_basic_stats(self, sample_article):
        stats = compute_article_stats(sample_article)
        assert stats["char_count"] > 0
        assert stats["word_count"] > 0
        assert stats["sentence_count"] > 0
        assert stats["estimated_tokens"] > 0
        assert stats["estimated_tokens"] > stats["word_count"]  # ~1.3x

    def test_empty_text(self):
        stats = compute_article_stats("")
        assert stats["char_count"] == 0
        assert stats["word_count"] == 0

    def test_single_sentence(self):
        stats = compute_article_stats("Hello world, this is one sentence.")
        assert stats["sentence_count"] == 1
        assert stats["word_count"] == 6


class TestChunkText:
    def test_short_text_no_chunking(self):
        text = "This is a short sentence. It does not need chunking."
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_chunking(self, sample_article):
        # Use a very small max_tokens to force chunking
        chunks = chunk_text(sample_article, max_tokens=50)
        assert len(chunks) > 1
        # All text should be preserved across chunks
        reconstructed = " ".join(chunks)
        # Word count should be approximately preserved
        assert abs(len(reconstructed.split()) - len(sample_article.split())) <= 2

    def test_empty_text(self):
        chunks = chunk_text("", max_tokens=100)
        assert chunks == []

    def test_single_long_sentence(self):
        # A single sentence longer than max_tokens gets its own chunk
        long_sentence = " ".join(["word"] * 200)
        chunks = chunk_text(long_sentence + ". Short sentence.", max_tokens=50)
        assert len(chunks) >= 1

    def test_with_tokenizer(self):
        """Test with a mock tokenizer."""
        from unittest.mock import MagicMock

        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.side_effect = lambda text, **kw: list(range(len(text.split())))

        text = "First sentence here. Second sentence here. Third sentence here."
        chunks = chunk_text(text, max_tokens=5, tokenizer=mock_tokenizer)
        assert len(chunks) >= 1


class TestPreprocessArticle:
    def test_full_pipeline(self, sample_article):
        result = preprocess_article(sample_article)
        assert "cleaned_text" in result
        assert "original_length" in result
        assert "cleaned_length" in result
        assert "cleaning_steps" in result
        assert "stats" in result
        assert result["original_length"] == len(sample_article)
        assert result["stats"]["word_count"] > 0

    def test_preserves_content(self, sample_article):
        result = preprocess_article(sample_article)
        # The cleaned text should be similar length to original (no major loss)
        assert result["cleaned_length"] >= result["original_length"] * 0.8
