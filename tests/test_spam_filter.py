"""Unit tests for binary spam and irrelevant content filtering."""

import pytest
from server.nlp.classifiers import model_suite


@pytest.fixture(scope="module", autouse=True)
def ensure_models():
    if model_suite.vectorizer is None:
        model_suite.load_artifacts()


def test_spam_detection_on_ad():
    spam_text = "HURRY! Mega 70% clearance sale on all luxury electronics this weekend at city mall! Click bit.ly/mega-deal"
    res = model_suite.predict(spam_text)
    assert res["is_spam"] is True
    assert res["spam_probability"] > 0.5


def test_non_spam_on_civic_alert():
    civic_text = "Water supply will remain interrupted in Begumpet due to scheduled maintenance on main feeder line."
    res = model_suite.predict(civic_text)
    assert res["is_spam"] is False
    assert res["spam_probability"] < 0.4
