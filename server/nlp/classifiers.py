"""Classifiers module for CivicPulse.

Implements and benchmarks classical machine learning models:
- Logistic Regression
- Support Vector Machine (LinearSVC & SVC)
- Decision Tree
- Multinomial Naive Bayes
- K-Nearest Neighbors
- Random Forest
- Gradient Boosting
- Voting and Stacking Ensembles

Provides training, cross-validation benchmarking, model persistence, and inference pipelines.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier

from server.nlp.features import build_tfidf_vectorizer
from server.nlp.preprocess import default_preprocessor

logger = logging.getLogger(__name__)
RANDOM_SEED = 42

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def get_classical_models() -> Dict[str, Any]:
    """Return dictionary of classical algorithms for comparative benchmarking."""
    return {
        "Logistic Regression": LogisticRegression(
            C=1.0, max_iter=1000, random_state=RANDOM_SEED
        ),
        "Linear SVM": LinearSVC(
            C=1.0, random_state=RANDOM_SEED, dual="auto"
        ),
        "Kernel SVM (RBF)": SVC(
            C=1.0, kernel="rbf", probability=True, random_state=RANDOM_SEED
        ),
        "Naive Bayes": MultinomialNB(alpha=0.5),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=20, random_state=RANDOM_SEED
        ),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5, weights="distance"),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=20, random_state=RANDOM_SEED
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=4, random_state=RANDOM_SEED
        )
    }


def build_voting_ensemble(models: Dict[str, Any]) -> VotingClassifier:
    """Construct a soft-voting ensemble using top probability estimators."""
    estimators = [
        ("lr", LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_SEED)),
        ("rf", RandomForestClassifier(n_estimators=100, max_depth=15, random_state=RANDOM_SEED)),
        ("nb", MultinomialNB(alpha=0.5)),
        ("svc", SVC(C=1.0, probability=True, random_state=RANDOM_SEED))
    ]
    return VotingClassifier(estimators=estimators, voting="soft")


def build_stacking_ensemble() -> StackingClassifier:
    """Construct a stacking classifier with LogisticRegression meta-estimator."""
    base_estimators = [
        ("lr", LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_SEED)),
        ("rf", RandomForestClassifier(n_estimators=50, max_depth=10, random_state=RANDOM_SEED)),
        ("nb", MultinomialNB(alpha=0.5))
    ]
    meta_learner = LogisticRegression(max_iter=500, random_state=RANDOM_SEED)
    return StackingClassifier(
        estimators=base_estimators,
        final_estimator=meta_learner,
        cv=3
    )


def benchmark_models(
    X_train: Any,
    y_train: Any,
    cv_folds: int = 5
) -> pd.DataFrame:
    """Run stratified cross-validation on all algorithms and return benchmark table."""
    models = get_classical_models()
    models["Voting Ensemble"] = build_voting_ensemble(models)
    models["Stacking Ensemble"] = build_stacking_ensemble()

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_SEED)
    results = []

    for name, clf in models.items():
        logger.info(f"Cross-validating: {name}...")
        try:
            scores = cross_validate(
                clf,
                X_train,
                y_train,
                cv=cv,
                scoring=["accuracy", "f1_macro", "f1_weighted", "precision_macro", "recall_macro"],
                n_jobs=-1
            )
            results.append({
                "Algorithm": name,
                "Accuracy (Mean)": np.mean(scores["test_accuracy"]),
                "Accuracy (Std)": np.std(scores["test_accuracy"]),
                "F1 Macro (Mean)": np.mean(scores["test_f1_macro"]),
                "F1 Macro (Std)": np.std(scores["test_f1_macro"]),
                "F1 Weighted (Mean)": np.mean(scores["test_f1_weighted"]),
                "Precision Macro": np.mean(scores["test_precision_macro"]),
                "Recall Macro": np.mean(scores["test_recall_macro"]),
            })
        except Exception as e:
            logger.error(f"Error evaluating {name}: {e}")

    df = pd.DataFrame(results).sort_values("F1 Macro (Mean)", ascending=False).reset_index(drop=True)
    return df


class CivicPulseModelSuite:
    """Production suite holding trained TF-IDF vectorizer, category, severity, and spam models."""

    def __init__(self):
        self.vectorizer = None
        self.category_model = None
        self.severity_model = None
        self.spam_model = None
        self.category_classes = []
        self.severity_classes = []
        self.high_severity_metrics = {}

    @staticmethod
    def compute_high_severity_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
        """Calculate per-class metrics and aggregate precision for high-severity alerts (Critical & Warning)."""
        from sklearn.metrics import precision_recall_fscore_support

        labels = ["critical", "warning"]
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, zero_division=0
        )

        # High severity binary precision: predicted in {critical, warning} vs true in {critical, warning}
        high_sev_set = {"critical", "warning"}
        bin_true = [1 if y in high_sev_set else 0 for y in y_true]
        bin_pred = [1 if y in high_sev_set else 0 for y in y_pred]
        bin_p, bin_r, bin_f1, _ = precision_recall_fscore_support(
            bin_true, bin_pred, average="binary", zero_division=0
        )

        return {
            "high_severity_precision": round(float(bin_p), 4),
            "high_severity_recall": round(float(bin_r), 4),
            "high_severity_f1": round(float(bin_f1), 4),
            "critical_precision": round(float(p[0]), 4),
            "critical_recall": round(float(r[0]), 4),
            "critical_f1": round(float(f1[0]), 4),
            "warning_precision": round(float(p[1]), 4),
            "warning_recall": round(float(r[1]), 4),
            "warning_f1": round(float(f1[1]), 4),
        }

    def train_suite(
        self,
        seed_data_path: Union[str, Path],
        reports_dir: Optional[Union[str, Path]] = None
    ):
        """Train and persist full production model suite from seed dataset."""
        with open(seed_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_texts = [d["text"] for d in data]
        cleaned_texts = [default_preprocessor.preprocess(t) for t in raw_texts]

        # 1. Fit shared TF-IDF Vectorizer
        self.vectorizer, X = build_tfidf_vectorizer(cleaned_texts, max_features=5000, ngram_range=(1, 2))

        # 2. Train Spam Filter (Binary)
        y_spam = np.array([1 if d.get("is_spam", False) else 0 for d in data])
        self.spam_model = LogisticRegression(C=2.0, max_iter=1000, random_state=RANDOM_SEED)
        self.spam_model.fit(X, y_spam)

        # 3. Train Category Classifier on non-spam items
        non_spam_indices = [i for i, d in enumerate(data) if not d.get("is_spam", False)]
        X_cat = X[non_spam_indices]
        y_cat = [data[i]["category"] for i in non_spam_indices]
        self.category_classes = sorted(list(set(y_cat)))

        # Ensemble or Logistic Regression for Category
        self.category_model = LogisticRegression(C=2.0, max_iter=1000, random_state=RANDOM_SEED)
        self.category_model.fit(X_cat, y_cat)

        # 4. Train Severity Classifier
        y_sev = [data[i]["severity"] for i in non_spam_indices]
        self.severity_classes = sorted(list(set(y_sev)))
        self.severity_model = LogisticRegression(C=1.5, max_iter=1000, random_state=RANDOM_SEED)
        self.severity_model.fit(X_cat, y_sev)

        # 4b. Evaluate high-severity metrics (Critical & Warning)
        sev_preds = self.severity_model.predict(X_cat)
        self.high_severity_metrics = self.compute_high_severity_metrics(y_sev, sev_preds)

        # 5. Persist artifacts
        self.save_artifacts()

        # 6. Save benchmark table if reports_dir given
        if reports_dir:
            p_rep = Path(reports_dir) / "comparison_tables"
            p_rep.mkdir(parents=True, exist_ok=True)
            benchmarks = benchmark_models(X_cat, y_cat, cv_folds=5)
            benchmarks.to_csv(p_rep / "classical_algorithm_comparison.csv", index=False)
            benchmarks.to_markdown(p_rep / "classical_algorithm_comparison.md", index=False)
            logger.info(f"Saved benchmark results to {p_rep}")

    def save_artifacts(self, dir_path: Optional[Path] = None):
        """Save models to disk."""
        target = dir_path or MODEL_DIR
        target.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, target / "tfidf_vectorizer.pkl")
        joblib.dump(self.spam_model, target / "spam_classifier.pkl")
        joblib.dump(self.category_model, target / "category_classifier.pkl")
        joblib.dump(self.severity_model, target / "severity_classifier.pkl")
        metadata = {
            "category_classes": self.category_classes,
            "severity_classes": self.severity_classes,
            "high_severity_precision": self.high_severity_metrics.get("high_severity_precision", 0.0),
            "high_severity_metrics": self.high_severity_metrics,
        }
        with open(target / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved production models to {target}")

    def load_artifacts(self, dir_path: Optional[Path] = None):
        """Load trained models from disk."""
        target = dir_path or MODEL_DIR
        if (target / "tfidf_vectorizer.pkl").exists():
            self.vectorizer = joblib.load(target / "tfidf_vectorizer.pkl")
            self.spam_model = joblib.load(target / "spam_classifier.pkl")
            self.category_model = joblib.load(target / "category_classifier.pkl")
            self.severity_model = joblib.load(target / "severity_classifier.pkl")
            with open(target / "metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.category_classes = meta.get("category_classes", [])
                self.severity_classes = meta.get("severity_classes", [])
                self.high_severity_metrics = meta.get("high_severity_metrics", {})
            logger.info("Production models loaded successfully.")
            return True
        logger.warning(f"Model artifacts not found in {target}")
        return False

    def predict(self, raw_text: str) -> Dict[str, Any]:
        """Classify single raw text for spam, category, and severity."""
        cleaned = default_preprocessor.preprocess(raw_text)
        if self.vectorizer is None:
            if not self.load_artifacts():
                seed_file = PROJECT_ROOT / "seed" / "seed_data.json"
                if seed_file.exists():
                    self.train_suite(seed_file)
                else:
                    raise RuntimeError("Models not loaded or trained.")

        vec = self.vectorizer.transform([cleaned])

        # Spam check
        spam_prob = float(self.spam_model.predict_proba(vec)[0][1])
        is_spam = spam_prob >= 0.5

        # Category prediction
        cat_probs = self.category_model.predict_proba(vec)[0]
        cat_idx = np.argmax(cat_probs)
        category = self.category_model.classes_[cat_idx]
        cat_conf = float(cat_probs[cat_idx])

        # Severity prediction
        sev_probs = self.severity_model.predict_proba(vec)[0]
        sev_idx = np.argmax(sev_probs)
        severity = self.severity_model.classes_[sev_idx]
        sev_conf = float(sev_probs[sev_idx])

        # Keyword rules and secondary category detection
        raw_lower = raw_text.lower()
        secondary_categories: List[str] = []

        WEATHER_KEYWORDS = [
            "cloudburst", "rain", "rainfall", "flooding", "flood",
            "waterlogging", "waterlogged", "cyclone", "heatwave",
            "inundation", "downpour", "thunderstorm", "flash flood"
        ]
        has_weather = any(w in raw_lower for w in WEATHER_KEYWORDS)

        # Primary override for heavy weather terms (e.g. cloudburst waterlogging)
        primary_weather_triggers = [
            "cloudburst", "cyclone", "heatwave", "flash flood",
            "cloudburst waterlogging", "heavy rainfall", "inundation"
        ]
        if any(t in raw_lower for t in primary_weather_triggers) or (
            "waterlogging" in raw_lower and category == "road_closure"
        ):
            if category != "severe_weather":
                secondary_categories.append(category)
                category = "severe_weather"
                cat_conf = max(cat_conf, 0.88)
        elif has_weather and category != "severe_weather":
            secondary_categories.append("severe_weather")

        # Also detect road closure as secondary if traffic diversion occurs during other issues
        if category != "road_closure" and any(r in raw_lower for r in ["traffic diverted", "road closed", "diversion", "flyover blocked", "lane closed"]):
            if "road_closure" not in secondary_categories:
                secondary_categories.append("road_closure")

        return {
            "cleaned_text": cleaned,
            "is_spam": is_spam,
            "spam_probability": round(spam_prob, 4),
            "category": category,
            "category_confidence": round(cat_conf, 4),
            "secondary_categories": secondary_categories,
            "severity": severity,
            "severity_confidence": round(sev_conf, 4),
        }


# Global model suite singleton
model_suite = CivicPulseModelSuite()


if __name__ == "__main__":
    seed_file = Path(__file__).resolve().parent.parent.parent / "seed" / "seed_data.json"
    rep_dir = Path(__file__).resolve().parent.parent.parent / "reports"
    print("Training CivicPulse Model Suite on seed data...")
    model_suite.train_suite(seed_file, reports_dir=rep_dir)
    print("Inference Test:")
    test_text = "Severe pipeline burst in Begumpet causes drinking water disruption for 24 hours."
    res = model_suite.predict(test_text)
    print(json.dumps(res, indent=2))
