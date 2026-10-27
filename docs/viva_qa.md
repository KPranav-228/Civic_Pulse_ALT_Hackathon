# CivicPulse — Capstone Viva Examination Q&A Cheat Sheet

This cheat sheet prepares you for technical, theoretical, and architectural questions frequently asked by examiners during capstone viva voce evaluations.

---

## 1. Feature Engineering & Representation

### Q1: Why use TF-IDF instead of standard Bag-of-Words (CountVectorizer)?
- **Answer:** Standard Bag-of-Words counts raw term frequencies. In civic notices, ubiquitous words like *"the"*, *"area"*, *"city"*, and *"notice"* appear dozens of times, skewing feature vectors towards high counts for uninformative tokens. 
- **TF-IDF (Term Frequency-Inverse Document Frequency)** penalizes terms that appear across almost all documents by weighting them with \(\log(N / \text{df})\). This boosts the numerical significance of discriminative keywords unique to specific emergencies (such as *"transformer"*, *"submerged"*, *"inundation"*, *"pipeline"*), allowing linear classifiers to draw sharper decision boundaries.

### Q2: What is the core difference between Word2Vec, FastText, and BERT?
- **Word2Vec (Mikolov et al., 2013):** Static dense embeddings learned from co-occurrence windows (CBOW/Skip-Gram). Every word has a single static vector. Cannot handle Out-Of-Vocabulary (OOV) words and collapses polysemous words (e.g., *"bank"* of a river vs financial *"bank"*).
- **FastText (Bojanowski et al., 2017):** Extends Word2Vec by representing each word as a bag of character n-grams (e.g. 3-grams to 6-grams). Crucial for CivicPulse because it can compute embeddings for unseen, misspelled, or transliterated Indian locality names (e.g., *"Gachibowli"* \(\rightarrow\) `"Gac"`, `"aci"`, `"chi"`, `"hib"`, `"ibo"`).
- **BERT (Devlin et al., 2018):** Transformer-based contextual embeddings. Rather than a static vector lookup, BERT generates dynamic token vectors conditioned on the entire sentence context bidirectionally via multi-head self-attention.

---

## 2. Classical Machine Learning vs Ensembles

### Q3: When should you choose Support Vector Machines (SVM) over Logistic Regression?
- **Answer:**
  - **Logistic Regression** minimizes log-loss and models the posterior probability \(P(y|x) = \sigma(w^T x)\). It utilizes all data points to fit the sigmoid curve, making it sensitive to extreme outliers but fast to train and natively probabilistic.
  - **Linear SVM** maximizes the geometric margin between classes, relying strictly on **Support Vectors** (the critical data points closest to the separating hyperplane). In high-dimensional sparse NLP text (where vocabulary size \(V > 5,000\)), Linear SVM is theoretically less prone to overfitting than Logistic Regression.
  - **In CivicPulse:** We use `CalibratedClassifierCV(LinearSVC)` so we gain the margin-maximization benefits of SVM while calibrating Platt probabilities for confidence thresholds.

### Q4: How do Voting and Stacking ensembles differ in our pipeline?
- **Soft Voting:** Computes a weighted average of predicted class probabilities across base estimators (e.g., \(\hat{y} = \arg\max \sum w_i P_i(c|x)\)). It succeeds when individual models have uncorrelated errors.
- **Stacking:** Trains a meta-learner (e.g. Logistic Regression) on the out-of-fold cross-validation predictions of base models (SVM, Random Forest, Naive Bayes). The meta-learner learns *which* base model to trust for specific feature distributions, achieving our highest accuracy (90.8%).

---

## 3. Evaluation & Error Trade-offs

### Q5: What is the Precision vs Recall trade-off for emergency civic alerts?
- **Answer:** 
  - **Precision:** \(\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}\) (How many alerted incidents were genuine disruptions?).
  - **Recall:** \(\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}\) (How many real-world disruptions were captured by the system?).
  - **The Trade-off:** In emergency life-safety management (severe weather, bridge closures, gas leaks), **Recall must be prioritized over Precision**. Missing a catastrophic flood alert (False Negative) has devastating consequences, whereas delivering an occasional false advisory (False Positive) is merely an inconvenience.
  - **CivicPulse Strategy:** We tune the decision threshold of the severity classifier to bias towards higher recall, and route borderline alerts to the human moderation queue (`needs_review`) to preserve high citizen trust.

### Q6: Why report Macro F1 instead of simple Accuracy?
- **Answer:** Civic report categories exhibit real-world class imbalance (e.g. `road_closure` and `power_cut` are frequent, while `severe_weather` or major chemical spills are rare). Simple accuracy is deceptive: a naive model predicting only the majority class could show 80% accuracy while failing completely on rare emergencies. **Macro F1** computes the unweighted arithmetic mean of F1 scores across all classes, giving equal importance to rare emergency categories.

---

## 4. Unsupervised Clustering & Deduplication

### Q7: How do KMeans and Latent Dirichlet Allocation (LDA) complement each other in CivicPulse?
- **KMeans (Geometric Partitioning):** Hard clustering that assigns each document vector to its closest centroid in vector space. Used to calculate Silhouette Scores and group incoming reports into distinct incident clusters.
- **LDA (Probabilistic Generative Modeling):** Assumes each document is a mixture of latent topics, and each topic is a Dirichlet distribution over words. Used in CivicPulse to extract human-interpretable topic keywords (`#waterlog`, `#traffic`, `#drainage`) for citizen tag clouds.
- **Deduplication:** When multiple news outlets and tweets report on the same event, CivicPulse computes cosine distance on unigram TF-IDF vectors. If similarity exceeds 0.55 and extracted locations match, the reports are merged into a single alert with concatenated sources.

---

## 5. Explainable AI (XAI) & Transformers

### Q8: How does LIME (Local Interpretable Model-agnostic Explanations) work for text?
- **Answer:** 
  1. LIME treats the underlying machine learning model as a black box.
  2. For a given alert text, LIME generates perturbed versions of the text by randomly dropping words.
  3. It queries the black-box classifier to obtain class prediction probabilities for each perturbed sample.
  4. It weights the samples by their cosine similarity to the original text.
  5. It fits a simple, interpretable linear model (Lasso/Ridge regression) on this locally weighted dataset.
  6. The learned coefficients of the linear model represent the **attribution weights** of individual words, showing whether each token positively or negatively contributed to the prediction.

### Q9: Why use DistilBERT rather than BERT-Large for production deployment?
- **Answer:** 
  - `bert-base-uncased` has 110M parameters; `bert-large` has 340M parameters.
  - `distilbert-base-uncased` uses **Knowledge Distillation** (student-teacher training) to retain 97% of BERT's language comprehension capabilities while having **40% fewer parameters** and running **60% faster**.
  - In a real-time civic ingestion system processing incoming feeds, inference latency must remain &lt;50ms per document on standard CPU servers without requiring expensive GPU clusters.

### Q10: How does the system handle regional or code-mixed text (e.g. Telugu/Hindi written in English script)?
- **Answer:** 
  - Standard tokenizers and English Word2Vec fail on transliterated text (e.g., *"Current ledu"* or *"Pedda traffic jam"*), treating words as Out-Of-Vocabulary.
  - CivicPulse addresses this via a dual strategy:
    1. **FastText Character N-Grams:** Matches subword root syllables across transliteration variations.
    2. **LLM Structured Fallback:** Large Language Models (Gemini / Multilingual BERT) possess extensive cross-lingual representations that naturally interpret Romanized Indian languages and extract standard English alert schemas.

---

## 6. Architecture, Hyperlocal Personalization & Civic Tech Positioning

### Q11: Why would citizens use CivicPulse when Google Maps already exists? (Complementary vs. Competing Positioning)
- **Answer:**
  - **Complementary, NOT competing:** Google Maps and CivicPulse address two fundamentally distinct user contexts that complement each other.
  - **Proactive Planning vs. Reactive In-Transit Navigation:** Google Maps activates *while you are already in transit*, telling you that a road is currently red with congestion. CivicPulse notifies you *hours before you leave* (e.g. 12-hour and 2-hour advance reminders that a flyover is closed for scheduled maintenance), enabling you to work from home, reschedule meetings, or opt for the metro.
  - **Causal Transparency ("Why" vs. "What"):** Google Maps displays a red congestion line without context. CivicPulse informs citizens of the *root cause* (pipeline burst, transformer replacement, political rally, flash inundation) backed by official municipal bulletins.
  - **Comprehensive Non-Transit Civic Issues:** Google Maps is strictly a navigation tool; it has zero visibility into **drinking water supply shutdowns (HMWSSB)**, **scheduled electricity outages (TGSPDCL)**, or **ward-level municipal notices (GHMC)**. CivicPulse monitors all civic lifelines impacting home, office, and family members.

### Q12: How does CivicPulse prevent rumor amplification and handle stale alerts? (Trust & Lifecycle Architecture)
- **3-Tier Credibility Verification:** Alerts are tagged as `Official Authority` (GHMC, HMWSSB, TGSPDCL, Traffic Police), `Verified News` (established press agencies), or `Unverified Public Report` (with an explicit amber caution banner to prevent panic).
- **Event Linking & Automatic Cancellation:** Natural language cues (*"restored"*, *"cleared"*, *"cancelled"*, *"postponed"*) are detected by our pipeline, matching the incident to prior active events via category and locality. The prior record is transitioned to `resolved` or `cancelled`, preventing stale alerts from polluting the citizen feed.
- **Crowd Verification:** Citizens can submit one-click ground confirmations (*"Water arrived"* vs *"Still off"*). When verified community consensus reaches 80%+, the alert status is automatically marked as resolved.

### Q13: How does the system personalize emergency checklists for different households?
- Rather than broadcasting generic tips, our **Personalization Engine** dynamically adapts recommended actions:
  - **Water Supply:** If the citizen profile indicates *Tanker Dependency*, the system advises booking private/GHMC tankers 6–8 hours in advance; if *Borewell*, it advises checking auxiliary pump pressure; if *Apartment*, it recommends alerting the society RWA to ration overhead tanks.
  - **Power Cut:** If the household has vulnerable care modes (*Dialysis* or *Medical Oxygen*), the alert's effective severity is elevated from Advisory to **Critical**, injecting emergency UPS verification steps and nearest 24/7 hospital listings.

