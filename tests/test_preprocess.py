"""Unit tests for CivicPulse preprocessing pipeline."""

import pytest
from server.nlp.preprocess import TextPreprocessor, default_preprocessor


def test_html_stripping():
    sample = "<b>URGENT:</b> Severe water cut scheduled in <p>Begumpet</p>."
    cleaned = default_preprocessor.remove_html_tags(sample)
    assert "<b>" not in cleaned
    assert "<p>" not in cleaned
    assert "Begumpet" in cleaned


def test_url_and_email_stripping():
    sample = "Visit https://ghmc.gov.in/alerts or contact alerts@civicpulse.org for info."
    cleaned = default_preprocessor.remove_urls(sample)
    assert "https://" not in cleaned
    cleaned = default_preprocessor.remove_emails(cleaned)
    assert "@" not in cleaned


def test_contraction_expansion():
    sample = "Roads won't open and services can't resume until evening."
    expanded = default_preprocessor.expand_contractions(sample)
    assert "will not" in expanded.lower()
    assert "cannot" in expanded.lower()
    assert "won't" not in expanded


def test_custom_preprocessor_ablation():
    # Preprocessor with stopwords retained
    p_with_stops = TextPreprocessor(remove_stopwords=False, lemmatize=False)
    processed = p_with_stops.preprocess("The road is blocked in the city")
    tokens = processed.split()
    assert "the" in tokens
    assert "is" in tokens

    # Preprocessor with stopwords removed
    p_no_stops = TextPreprocessor(remove_stopwords=True, lemmatize=False)
    processed_no_stops = p_no_stops.preprocess("The road is blocked in the city")
    tokens_no_stops = processed_no_stops.split()
    assert "the" not in tokens_no_stops
    assert "is" not in tokens_no_stops
    assert "road" in tokens_no_stops


def test_step_by_step_trace():
    sample = "Water supply won't resume in Indiranagar until tomorrow! Visit http://test.com"
    trace = default_preprocessor.preprocess_with_steps(sample)
    assert "original" in trace
    assert "steps" in trace
    assert "final" in trace
    assert len(trace["steps"]) >= 6
