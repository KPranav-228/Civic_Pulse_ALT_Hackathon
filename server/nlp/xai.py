"""Explainable AI (XAI) module for CivicPulse using LIME and SHAP.

Explains category and severity predictions by highlighting influential words,
their weights, and class contributions for the citizen-facing UI and audit panels.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.nlp.classifiers import model_suite
from server.nlp.preprocess import default_preprocessor

logger = logging.getLogger(__name__)


class CivicPulseExplainer:
    """Provides LIME and feature attribution explanations for alert classifications."""

    def __init__(self):
        self._lime_explainer = None

    @property
    def lime_explainer(self):
        """Lazy load LIME text explainer."""
        if self._lime_explainer is None:
            from lime.lime_text import LimeTextExplainer
            self._lime_explainer = LimeTextExplainer(
                class_names=model_suite.category_classes or [
                    "other", "power_cut", "public_service", "road_closure", "severe_weather", "water_supply"
                ],
                random_state=42
            )
        return self._lime_explainer

    def explain_with_lime(
        self,
        text: str,
        num_features: int = 8
    ) -> Dict[str, Any]:
        """Generate LIME explanation for the alert's category."""
        if not model_suite.category_model or not model_suite.vectorizer:
            model_suite.load_artifacts()

        def predict_fn(texts: List[str]) -> np.ndarray:
            cleaned = [default_preprocessor.preprocess(t) for t in texts]
            vecs = model_suite.vectorizer.transform(cleaned)
            return model_suite.category_model.predict_proba(vecs)

        pred = model_suite.predict(text)
        predicted_class = pred["category"]

        try:
            # Generate LIME explanation with fast sample count
            exp = self.lime_explainer.explain_instance(
                text,
                predict_fn,
                num_features=num_features,
                num_samples=100,
                labels=[model_suite.category_classes.index(predicted_class)]
            )
            class_idx = model_suite.category_classes.index(predicted_class)
            weights = exp.as_list(label=class_idx)
        except Exception as e:
            logger.warning(f"LIME fallback triggered: {e}")
            # Fast fallback feature attribution from TF-IDF linear coefficients
            weights = self._linear_feature_attribution(text, predicted_class, num_features)

        # Separate positive and negative contributors
        positive_influences = []
        negative_influences = []

        for word, weight in weights:
            item = {"token": word, "weight": round(float(weight), 4)}
            if weight > 0:
                positive_influences.append(item)
            else:
                negative_influences.append(item)

        return {
            "predicted_category": predicted_class,
            "category_confidence": pred["category_confidence"],
            "positive_features": positive_influences,
            "negative_features": negative_influences,
            "summary": (
                f"Classified as '{predicted_class}' with {pred['category_confidence']*100:.1f}% confidence. "
                f"Primary indicator keywords: {', '.join([w['token'] for w in positive_influences[:3]])}."
            )
        }

    def _linear_feature_attribution(
        self,
        text: str,
        predicted_class: str,
        num_features: int = 8
    ) -> List[Tuple[str, float]]:
        """Compute direct coefficient weights from logistic regression for speed and robustness."""
        cleaned = default_preprocessor.preprocess(text)
        vec = model_suite.vectorizer.transform([cleaned])
        feature_names = model_suite.vectorizer.get_feature_names_out()

        class_idx = list(model_suite.category_model.classes_).index(predicted_class)
        coefs = model_suite.category_model.coef_[class_idx]

        # Non-zero indices in input
        row = vec.tocoo()
        contributions = []
        for col_idx in row.col:
            word = feature_names[col_idx]
            w = float(coefs[col_idx])
            contributions.append((word, w))

        # Sort by absolute weight
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        return contributions[:num_features]


explainer = CivicPulseExplainer()

if __name__ == "__main__":
    model_suite.load_artifacts()
    sample = "Heavy flood water overflowing onto Begumpet arterial road causing massive traffic block."
    print("XAI Explanation Test:")
    explanation = explainer.explain_with_lime(sample)
    import json
    print(json.dumps(explanation, indent=2))
