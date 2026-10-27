# CivicPulse — Syllabus Coverage & Capstone Mapping (CO1 – CO4)

This document provides a comprehensive mapping of the course learning outcomes (**CO1 to CO4**) to the exact code files, Jupyter notebooks, test suites, and API endpoints where each concept is implemented and demonstrated.

---

## High-Level Syllabus Mapping Matrix

| Course Outcome | Syllabus Topic / Module | Concrete Implementation File(s) | Interactive Notebook | Evaluation / Artifacts |
|---|---|---|---|---|
| **CO1: Foundations of NLP & Classical ML** | Industry NLP Applications Overview (chatbots, sentiment, recs) | `docs/case_studies.md`, `README.md` | `notebooks/01_intro_and_ml_basics.ipynb` (Section 1) | Comparative architectural notes |
| | Supervised vs Unsupervised Formulation | `server/nlp/classifiers.py`, `server/nlp/clustering.py` | `notebooks/01_intro_and_ml_basics.ipynb` (Section 2) | Supervised alert categorization vs unsupervised topic discovery |
| | 10 Classic Algorithms Benchmark (LR, SVM, DT, NB, KNN, Ensembles) | `server/nlp/classifiers.py` | `notebooks/01_intro_and_ml_basics.ipynb` (Section 4) | `reports/comparison_tables/classical_algorithm_comparison.csv` |
| | Python NLP Ecosystem (scikit-learn, NLTK, spaCy) | `server/nlp/preprocess.py`, `server/nlp/ner.py` | `notebooks/01_intro_and_ml_basics.ipynb` (Section 3) | Demonstration of tokenizers, stemmers, POS taggers, and NER |
| **CO2: Preprocessing, Features & Embeddings** | Multi-Stage Preprocessing Pipeline (clean, normalize, stem, lemmatize) | `server/nlp/preprocess.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 1) | Step-by-step trace `preprocess_with_steps()`, ablation study |
| | Preprocessing Ablation Study | `server/nlp/preprocess.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 2) | `reports/comparison_tables/preprocessing_ablation_study.csv` |
| | Feature Extraction: BoW & TF-IDF (unigrams & bigrams) | `server/nlp/features.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 3) | Vectorizer artifacts in `server/models/tfidf_vectorizer.pkl` |
| | Dense Word Embeddings: Word2Vec, GloVe, FastText | `server/nlp/features.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 4) | FastText out-of-vocabulary evaluation on Indian place names |
| | Contextual Embeddings: BERT / DistilBERT ([CLS] & mean pooling) | `server/nlp/features.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 5) | Feature representation comparison on identical downstream classifier |
| | Dimensionality Reduction & Manifold Projection (PCA, t-SNE, UMAP / Spectral) | `server/nlp/clustering.py` | `notebooks/02_preprocessing_features_embeddings.ipynb` (Section 6) | `reports/embedding_visualizations/pca_tsne_umap_comparison.png` |
| **CO3: Classification, Clustering, Evaluation & Deployment** | Multi-Task Classification: Spam / Irrelevant Filter | `server/nlp/classifiers.py`, `tests/test_spam_filter.py` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 1) | `server/models/spam_classifier.pkl` |
| | Multi-Task Classification: Alert Category Classification | `server/nlp/classifiers.py`, `tests/test_classifier.py` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 2) | `server/models/category_classifier.pkl` |
| | Multi-Task Classification: Severity / Urgency Mapping | `server/nlp/classifiers.py`, `tests/test_classifier.py` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 3) | `server/models/severity_classifier.pkl` |
| | Topic Modeling & Deduplication: KMeans & LDA | `server/nlp/clustering.py`, `tests/test_dedup.py` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 4) | Silhouette score, topic coherence, near-duplicate detection |
| | Rigorous Evaluation: Precision, Recall, Macro/Weighted F1, Confusion Matrix, Multiclass ROC/AUC | `server/nlp/classifiers.py` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 5) | `reports/confusion_matrices/`, `reports/roc_curves/` |
| | Production Deployment: FastAPI, Pydantic, Rate Limiting, Docker | `server/main.py`, `server/api/routes.py`, `Dockerfile`, `docker-compose.yml` | `notebooks/03_classification_clustering_evaluation.ipynb` (Section 6) | `/health`, `/api/alerts`, `/api/classify`, `/api/ingest` |
| **CO4: Transformers, Transfer Learning, XAI & Industry Cases** | Transformer Architecture & Attention Mechanism | Markdown theory guide in notebook 4 | `notebooks/04_transformers_finetuning_xai.ipynb` (Section 1) | Attention calculation walkthrough, Self-attention explainer |
| | Transformer Fine-Tuning: BERT / DistilBERT via HuggingFace | `server/nlp/features.py` | `notebooks/04_transformers_finetuning_xai.ipynb` (Section 2) | Transformer fine-tuning pipeline vs classical baseline table |
| | Low-Resource Transfer Learning Curve (N = 50, 100, 200, 500) | `server/nlp/classifiers.py` | `notebooks/04_transformers_finetuning_xai.ipynb` (Section 3) | Learning curves showing transformer sample efficiency |
| | Low-Resource Stress Test: Regional Language & Code-Mixed Text (Telugu/Hindi) | `seed/generate_dataset.py`, `notebooks/05_multilingual_indic_models.ipynb` | `notebooks/04_transformers_finetuning_xai.ipynb` & `notebooks/05_multilingual_indic_models.ipynb` | FastText vs DistilBERT vs IndicBERT vs Google MuRIL in `reports/comparison_tables/multilingual_indic_comparison.csv` |
| | Explainable AI: LIME Feature Attribution & Token Highlighting | `server/nlp/xai.py`, `client/src/components/XAIPanel.tsx` | `notebooks/04_transformers_finetuning_xai.ipynb` (Section 5) | "Why was this classified this way?" UI panel with token weights |
| | Industry Case Studies: IBM Watson, Google BERT, Azure NLP, TCS Ignio | `docs/case_studies.md` | `notebooks/04_transformers_finetuning_xai.ipynb` (Section 6) | Real-world NLP architectures and lessons applied to CivicPulse |

---

## Detailed CO Breakdown & Code Cross-References

### 1. CO1: Foundations of Natural Language Processing & Classical ML
- **Supervised vs Unsupervised Distinction:**
  - *Supervised:* Multi-class categorization (`road_closure`, `water_supply`, `power_cut`, `severe_weather`, `public_service`, `other`) and binary spam filtering using ground truth labeled synthetic training dataset (`seed/train.json`). See [`server/nlp/classifiers.py`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/server/nlp/classifiers.py).
  - *Unsupervised:* Topic modeling using KMeans and Latent Dirichlet Allocation (LDA) to discover unprompted emergency patterns without labels. See [`server/nlp/clustering.py`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/server/nlp/clustering.py).
- **10-Algorithm Comparison:**
  - Implemented in `train_all_classifiers()`:
    1. Logistic Regression (L2 regularization, liblinear/lbfgs)
    2. Linear Support Vector Machine (`CalibratedClassifierCV` around `LinearSVC`)
    3. Kernel SVM (Radial Basis Function `SVC(kernel='rbf')`)
    4. Multinomial Naive Bayes (`MultinomialNB(alpha=0.1)`)
    5. Decision Tree (`DecisionTreeClassifier(max_depth=12)`)
    6. K-Nearest Neighbors (`KNeighborsClassifier(n_neighbors=5)`)
    7. Random Forest (`RandomForestClassifier(n_estimators=150)`)
    8. Gradient Boosting (`HistGradientBoostingClassifier`)
    9. Soft Voting Classifier (combines Logistic Regression, Calibrated Linear SVM, and Random Forest)
    10. Stacking Classifier (Meta-learner Logistic Regression over base estimators)
  - Results exported to [`reports/comparison_tables/classical_algorithm_comparison.csv`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/comparison_tables/classical_algorithm_comparison.csv).
- **Python NLP Stack Meaningful Use:**
  - `scikit-learn`: Feature vectorization, TF-IDF matrix generation, classifier estimators, ensemble voting/stacking, stratified k-fold cross-validation, and metrics.
  - `NLTK`: Punctuation stripping, word and sentence tokenization, Porter and Snowball stemmers, and stop words dictionary.
  - `spaCy`: `en_core_web_sm` / fallback pipeline for Lemmatization and Named Entity Recognition (extracting `GPE`, `LOC`, `FAC`, `ORG`).

---

### 2. CO2: Preprocessing, Feature Extraction & Embeddings
- **Configurable Preprocessor Pipeline (`server/nlp/preprocess.py`):**
  - Configurable flags: HTML cleaning, URL stripping, email address stripping, contraction expansion (50+ colloquial forms), emoji normalization (emojis converted to text tags like `:warning:`), lowercasing, punctuation stripping, stop word filtering, and stemming/lemmatization.
  - Interactive trace method `preprocess_with_steps()` returns before-and-after text at each transform stage.
  - Preprocessing ablation study in [`reports/comparison_tables/preprocessing_ablation_study.csv`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/comparison_tables/preprocessing_ablation_study.csv).
- **Dense & Sparse Feature Extraction (`server/nlp/features.py`):**
  - **Bag-of-Words (BoW):** Term occurrence count matrix (`CountVectorizer`).
  - **TF-IDF:** Term frequency-inverse document frequency supporting unigrams and bigrams (`(1, 2)` ngram range).
  - **Word2Vec:** Gensim Continuous Bag-of-Words (CBOW) and Skip-Gram trained on the municipal alert corpus (`vector_size=100`, `window=5`).
  - **GloVe:** Pretrained word vectors parsed and mapped to corpus vocabulary with out-of-vocabulary handling.
  - **FastText:** Gensim FastText with character n-grams `(min_n=3, max_n=6)`, specifically demonstrated on out-of-vocabulary and transliterated Indian localities (`Gachibowli`, `Khajaguda`, `Kukatpally`).
  - **BERT / DistilBERT:** Contextual token representations extracted via HuggingFace `AutoTokenizer` and `AutoModel` using both `[CLS]` token and mean-pooled representations.
- **Dimensionality Reduction & Manifold Projection:**
  - 3-panel comparative projection in [`reports/embedding_visualizations/pca_tsne_umap_comparison.png`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/embedding_visualizations/pca_tsne_umap_comparison.png):
    1. **PCA:** Linear projection capturing global variance.
    2. **t-SNE:** Non-linear probabilistic projection preserving local neighborhood topologies.
    3. **Spectral / UMAP:** Graph Laplacian manifold projection separating distinct civic categories into tight, interpretable clusters.
  - Written interpretation in [`reports/embedding_visualizations/interpretation.md`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/embedding_visualizations/interpretation.md).

---

### 3. CO3: Classification, Clustering, Evaluation & Deployment
- **Three Core Classification Tasks:**
  1. *Spam / Clickbait Filter:* Distinguishes genuine civic incident notices from commercial advertisements, spam, and unrelated general news (`server/models/spam_classifier.pkl`).
  2. *Alert Category Classification:* Maps incoming text to 6 civic domains (`road_closure`, `water_supply`, `power_cut`, `severe_weather`, `public_service`, `other`).
  3. *Severity / Urgency Mapping:* Maps urgency level to 4 actionable levels (`critical`, `warning`, `advisory`, `info`).
- **Unsupervised Topic Modeling & Deduplication:**
  - **K-Means Clustering:** Optimal cluster discovery with Silhouette Score calculation.
  - **Latent Dirichlet Allocation (LDA):** Probabilistic generative topic model producing top co-occurring topic keywords.
  - **Deduplication Engine (`find_duplicate_reports`):** Computes pairwise cosine distance over unigram TF-IDF vectors to cluster near-duplicate reports about the same event.
- **Evaluation Artifacts:**
  - Multiclass One-vs-Rest ROC Curves & AUC: [`reports/roc_curves/multiclass_ovr_roc_curves.png`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/roc_curves/multiclass_ovr_roc_curves.png).
  - Category Confusion Matrix: [`reports/confusion_matrices/category_confusion_matrix.png`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/confusion_matrices/category_confusion_matrix.png).
  - Severity Confusion Matrix: [`reports/confusion_matrices/severity_confusion_matrix.png`](file:///c:/Users/prana/OneDrive/Documents/ALT_Project/reports/confusion_matrices/severity_confusion_matrix.png).
- **Production FastAPI Deployment:**
  - Pydantic v2 validation (`server/schemas/alert.py`).
  - Rate limiting via `slowapi` (`server/api/middleware.py`).
  - Live API documentation (`/docs`, `/redoc`).
  - Health check endpoint (`GET /health`).

---

### 4. CO4: Transformers, Transfer Learning, XAI & Industry Case Studies
- **Transformers & Attention:**
  - Detailed architectural breakdown in `notebooks/04_transformers_finetuning_xai.ipynb` covering Scaled Dot-Product Attention, Multi-Head Attention, and Transformer Encoders.
- **Transfer Learning on Low-Resource Data:**
  - Learning curve experiments comparing Logistic Regression vs fine-tuned DistilBERT on labeled subsets of `N = 50, 100, 200, 500` samples. Demonstrates how pretrained transformers excel when labeled examples are scarce.
- **Code-Mixed Low-Resource Stress Test:**
  - Synthetic dataset includes 15 transliterated Telugu and Hindi civic reports (e.g. *"Power cut aipoindi Madhapur lo"*). Evaluates subword FastText character n-grams and zero-shot transformer prompt handling.
- **Explainable AI (XAI):**
  - `server/nlp/xai.py`: Implements LIME (`LimeTextExplainer`) and feature attribution for model transparency.
  - Highlights token contributions (green for positive influence towards the class, red for opposing words).
  - Rendered interactively in the client UI via `client/src/components/XAIPanel.tsx`.
- **Real-World Case Studies (`docs/case_studies.md`):**
  - **IBM Watson:** Hybrid pipeline, question answering, and medical diagnosis lessons.
  - **Google BERT in Search:** Passage ranking, bi-directional context, and inference latency optimizations.
  - **Microsoft Azure Cognitive Services (NLP):** Enterprise entity recognition, sentiment analysis, and modular API design.
  - **TCS Ignio:** Autonomous IT incident triage, event correlation, and civic alerting analogies.

---

### 5. Advanced Production Capabilities: Hyperlocal, Delivery & Active Learning Loop
- **Hyderabad Locality Gazetteer & Haversine Distance (`server/nlp/gazetteer.py`):**
  - 32 canonical Hyderabad localities with coordinates, municipal zones, and alias dictionaries.
  - Fuzzy matching resolving variants (*"Gachibowli X Roads"* \(\rightarrow\) `Gachibowli`).
  - Great-circle Haversine distance spatial matching for arbitrary citizen monitoring radii.
- **Temporal Entity Extraction & Proactive Reminders (`server/nlp/time_extractor.py`, `server/services/reminder_service.py`):**
  - Extracts 12h/24h time spans (*"from 9 AM to 5 PM"*), durations, and relative dates (*"tomorrow"*).
  - Automatically schedules 12-hour and 2-hour advance reminders for upcoming disruptions.
- **Household Personalization & Vulnerable Care Modes (`server/services/personalization.py`):**
  - Adapts checklists dynamically to water source (tanker vs borewell vs municipal) and housing type (apartment vs independent).
  - Elevates effective power-cut severity to **Critical** for households with dialysis or medical oxygen reliance.
- **Multilingual Telugu & Hindi Generation (`server/services/multilingual.py`, `client/src/components/AlertCard.tsx`):**
  - Dynamic translation of titles, impacts, and action steps into Telugu and Hindi via Gemini LLM with high-quality dictionary fallbacks.
  - Browser Web Speech API Audio TTS read-aloud in English, Telugu, and Hindi.
- **Multi-Channel Delivery (`server/services/telegram_bot.py`, `server/services/sms_service.py`, `server/services/digest_service.py`):**
  - Full-featured Telegram bot with slash commands (`/start`, `/setlocality`, `/addlocation`, `/locations`, `/alerts`, `/reminders`).
  - Abstract SMS fallback provider (Twilio + MockSMSProvider).
  - Synthesized weekly civic digest for local neighborhoods.
- **Active Citizen Feedback & Operational Drift Monitoring (`server/scripts/merge_feedback.py`, `server/api/routes.py`):**
  - In-app "Wrong severity/category?" feedback queued for automated dataset merge and retraining.
  - Ground-truth community confirmations ("Water arrived" vs "Still off").
  - Operational monitoring endpoint (`GET /api/monitoring`) tracking class distributions, user false-alarm rates, and data drift indicators.

