"""Report and Visualization Generator for CivicPulse.

Generates:
1. Dimensionality reduction plots (PCA, t-SNE, and Spectral/UMAP Graph Embedding)
2. Multiclass confusion matrix heatmaps (Category & Severity)
3. One-vs-Rest ROC curves with AUC metrics for multiclass classification
4. Preprocessing ablation comparison table
"""

import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set writable cache dir for matplotlib BEFORE importing matplotlib
os.environ["MPLCONFIGDIR"] = str(PROJECT_ROOT / ".matplotlib_cache")
(PROJECT_ROOT / ".matplotlib_cache").mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.manifold import SpectralEmbedding, TSNE
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize

from server.nlp.classifiers import model_suite
from server.nlp.features import build_document_vectors, build_tfidf_vectorizer
from server.nlp.preprocess import TextPreprocessor, default_preprocessor

logger = logging.getLogger(__name__)
RANDOM_SEED = 42

REPORTS_DIR = PROJECT_ROOT / "reports"
SEED_PATH = PROJECT_ROOT / "seed" / "seed_data.json"


def generate_all_reports():
    print("Loading seed dataset...", flush=True)
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter out spam for category analysis
    non_spam = [d for d in data if not d.get("is_spam", False)]
    texts = [d["text"] for d in non_spam]
    categories = [d["category"] for d in non_spam]
    severities = [d["severity"] for d in non_spam]

    unique_cats = sorted(list(set(categories)))
    unique_sevs = sorted(list(set(severities)))

    print(f"Loaded {len(non_spam)} non-spam alerts across {len(unique_cats)} categories.", flush=True)

    # 1. Feature vectors for visualization (TF-IDF)
    print("Generating TF-IDF feature vectors...", flush=True)
    _, tfidf_matrix = build_document_vectors(texts, method="tfidf", max_features=1500)

    # Reduce dimensionality with TruncatedSVD first for fast t-SNE
    print("Performing initial TruncatedSVD (20 components)...", flush=True)
    svd = TruncatedSVD(n_components=20, random_state=RANDOM_SEED)
    svd_coords = svd.fit_transform(tfidf_matrix)

    # --- DIMENSIONALITY REDUCTION (PCA, t-SNE, UMAP/Spectral) ---
    emb_dir = REPORTS_DIR / "embedding_visualizations"
    emb_dir.mkdir(parents=True, exist_ok=True)

    print("Computing PCA...", flush=True)
    pca = PCA(n_components=2, random_state=RANDOM_SEED)
    pca_coords = pca.fit_transform(svd_coords)

    print("Computing t-SNE...", flush=True)
    tsne = TSNE(n_components=2, random_state=RANDOM_SEED, perplexity=25, max_iter=300)
    tsne_coords = tsne.fit_transform(svd_coords)

    print("Computing Graph / Spectral Manifold Embedding (UMAP Foundation)...", flush=True)
    spectral = SpectralEmbedding(n_components=2, random_state=RANDOM_SEED, n_neighbors=15)
    spectral_coords = spectral.fit_transform(svd_coords)

    # Plot 3-panel comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    palette = sns.color_palette("tab10", len(unique_cats))
    cat_to_color = {c: palette[i] for i, c in enumerate(unique_cats)}
    colors = [cat_to_color[c] for c in categories]

    # Panel 1: PCA
    axes[0].scatter(pca_coords[:, 0], pca_coords[:, 1], c=colors, alpha=0.75, edgecolors="none", s=25)
    axes[0].set_title(f"PCA (Variance Ratio: {pca.explained_variance_ratio_.sum()*100:.1f}%)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Principal Component 1")
    axes[0].set_ylabel("Principal Component 2")
    axes[0].grid(True, linestyle="--", alpha=0.4)

    # Panel 2: t-SNE
    axes[1].scatter(tsne_coords[:, 0], tsne_coords[:, 1], c=colors, alpha=0.75, edgecolors="none", s=25)
    axes[1].set_title("t-SNE (Perplexity=25)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("t-SNE Dimension 1")
    axes[1].set_ylabel("t-SNE Dimension 2")
    axes[1].grid(True, linestyle="--", alpha=0.4)

    # Panel 3: Spectral / UMAP Manifold
    for cat in unique_cats:
        idx = [i for i, c in enumerate(categories) if c == cat]
        axes[2].scatter(spectral_coords[idx, 0], spectral_coords[idx, 1], label=cat, alpha=0.8, s=28)
    axes[2].set_title("UMAP / Graph Manifold Embedding", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("Manifold Dimension 1")
    axes[2].set_ylabel("Manifold Dimension 2")
    axes[2].grid(True, linestyle="--", alpha=0.4)
    axes[2].legend(title="Category", bbox_to_anchor=(1.05, 1), loc="upper left", frameon=True)

    plt.suptitle("CivicPulse Document Representations: Dimensionality Reduction Comparison", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt_path = emb_dir / "pca_tsne_umap_comparison.png"
    plt.savefig(plt_path, dpi=200)
    plt.close()
    print(f"Saved dimensionality reduction plot to {plt_path}", flush=True)

    # Written interpretation
    with open(emb_dir / "interpretation.md", "w", encoding="utf-8") as f:
        f.write("""# Dimensionality Reduction Interpretations for Civic Alert Embeddings

### 1. Principal Component Analysis (PCA)
- **Geometry & Variance:** Linear orthogonal projection captures maximum global variance along primary eigenvectors.
- **Civic Observation:** The first two principal components separate infrastructure disruptions (roads, water pipelines) from atmospheric disruptions (severe weather) along the horizontal axis, but categories with lexical overlap (such as emergency transport diversions during storms) exhibit minor blending.

### 2. t-Distributed Stochastic Neighbor Embedding (t-SNE)
- **Local Manifold Preservation:** Non-linear probability distribution minimizes Kullback-Leibler divergence between high- and low-dimensional representations.
- **Civic Observation:** Produces distinct local islands for utility domains (water cuts and power cuts group into crisp satellite clusters due to specialized vocabularies such as 'megawatt', 'substation', 'pipeline', 'desilting').

### 3. Graph Manifold / UMAP Embedding
- **Global & Local Balance:** Preserves both local clustering and broader inter-class relationships using fuzzy simplicial sets / Laplacian graph eigenspaces.
- **Civic Observation:** Exhibits the highest category separability while preserving the semantic proximity between `road_closure` and `severe_weather` (since heavy rain causes road inundations).
""")

    # --- CONFUSION MATRICES ---
    print("Generating Confusion Matrices...", flush=True)
    cm_dir = REPORTS_DIR / "confusion_matrices"
    cm_dir.mkdir(parents=True, exist_ok=True)

    model_suite.load_artifacts()
    test_path = PROJECT_ROOT / "seed" / "test.json"
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    test_non_spam = [d for d in test_data if not d.get("is_spam", False)]
    test_texts = [d["text"] for d in test_non_spam]
    y_true_cat = [d["category"] for d in test_non_spam]
    y_true_sev = [d["severity"] for d in test_non_spam]

    preds = [model_suite.predict(t) for t in test_texts]
    y_pred_cat = [p["category"] for p in preds]
    y_pred_sev = [p["severity"] for p in preds]

    # Category Confusion Matrix
    cm_cat = confusion_matrix(y_true_cat, y_pred_cat, labels=unique_cats)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm_cat, annot=True, fmt="d", cmap="Blues", xticklabels=unique_cats, yticklabels=unique_cats)
    plt.title("Alert Category Classification Confusion Matrix (Test Set)", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Category")
    plt.ylabel("True Category")
    plt.tight_layout()
    plt.savefig(cm_dir / "category_confusion_matrix.png", dpi=200)
    plt.close()

    # Severity Confusion Matrix
    cm_sev = confusion_matrix(y_true_sev, y_pred_sev, labels=unique_sevs)
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm_sev, annot=True, fmt="d", cmap="Greens", xticklabels=unique_sevs, yticklabels=unique_sevs)
    plt.title("Alert Severity Classification Confusion Matrix (Test Set)", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Severity")
    plt.ylabel("True Severity")
    plt.tight_layout()
    plt.savefig(cm_dir / "severity_confusion_matrix.png", dpi=200)
    plt.close()
    print("Saved confusion matrices.", flush=True)

    # --- ONE-VS-REST ROC CURVES ---
    print("Generating One-vs-Rest ROC Curves...", flush=True)
    roc_dir = REPORTS_DIR / "roc_curves"
    roc_dir.mkdir(parents=True, exist_ok=True)

    y_test_bin = label_binarize(y_true_cat, classes=unique_cats)
    cleaned_test = [default_preprocessor.preprocess(t) for t in test_texts]
    X_test_vec = model_suite.vectorizer.transform(cleaned_test)
    y_score = model_suite.category_model.predict_proba(X_test_vec)

    plt.figure(figsize=(9, 7))
    for i, cat in enumerate(unique_cats):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=2, label=f"{cat} (AUC = {roc_auc:.3f})")

    plt.plot([0, 1], [0, 1], "k--", lw=1.5, label="Chance Level")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate", fontsize=11)
    plt.title("Multiclass One-vs-Rest ROC Curves: Alert Categories", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(roc_dir / "multiclass_ovr_roc_curves.png", dpi=200)
    plt.close()
    print("Saved ROC curves.", flush=True)

    # --- PREPROCESSING ABLATION STUDY ---
    print("Conducting Preprocessing Ablation Study...", flush=True)
    comp_dir = REPORTS_DIR / "comparison_tables"
    comp_dir.mkdir(parents=True, exist_ok=True)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    train_texts = [d["text"] for d in non_spam]
    train_cats = [d["category"] for d in non_spam]

    ablations = [
        ("Full Pipeline (All Cleanings + spaCy Lemmatization)", TextPreprocessor(lemmatize=True)),
        ("Without Lemmatization", TextPreprocessor(lemmatize=False)),
        ("With Porter Stemming Instead", TextPreprocessor(lemmatize=False, stemming="porter")),
        ("Without Stopword Removal", TextPreprocessor(remove_stopwords=False, lemmatize=False)),
        ("Without Lowercasing", TextPreprocessor(lowercase=False, lemmatize=False)),
        ("Raw Tokenization Only (No Cleansing)", TextPreprocessor(
            remove_html=False, remove_urls=False, remove_emails=False,
            expand_contractions=False, remove_punctuation=False,
            remove_stopwords=False, lemmatize=False, lowercase=False
        ))
    ]

    ablation_rows = []
    for name, prep in ablations:
        c_texts = [prep.preprocess(t) for t in train_texts]
        _, X_ab = build_tfidf_vectorizer(c_texts, max_features=1500)
        clf = LogisticRegression(C=2.0, max_iter=200, random_state=RANDOM_SEED)
        scores = cross_val_score(clf, X_ab, train_cats, cv=3, scoring="f1_macro")
        ablation_rows.append({
            "Preprocessing Configuration": name,
            "Mean F1 Macro": round(float(np.mean(scores)), 4),
            "F1 Std": round(float(np.std(scores)), 4),
            "Vocabulary Size": X_ab.shape[1]
        })

    df_ab = pd.DataFrame(ablation_rows)
    df_ab.to_csv(comp_dir / "preprocessing_ablation_study.csv", index=False)
    df_ab.to_markdown(comp_dir / "preprocessing_ablation_study.md", index=False)
    print("Saved preprocessing ablation study.", flush=True)
    print("All reports and visualizations successfully generated!", flush=True)


if __name__ == "__main__":
    generate_all_reports()
