# Dimensionality Reduction Interpretations for Civic Alert Embeddings

### 1. Principal Component Analysis (PCA)
- **Geometry & Variance:** Linear orthogonal projection captures maximum global variance along primary eigenvectors.
- **Civic Observation:** The first two principal components separate infrastructure disruptions (roads, water pipelines) from atmospheric disruptions (severe weather) along the horizontal axis, but categories with lexical overlap (such as emergency transport diversions during storms) exhibit minor blending.

### 2. t-Distributed Stochastic Neighbor Embedding (t-SNE)
- **Local Manifold Preservation:** Non-linear probability distribution minimizes Kullback-Leibler divergence between high- and low-dimensional representations.
- **Civic Observation:** Produces distinct local islands for utility domains (water cuts and power cuts group into crisp satellite clusters due to specialized vocabularies such as 'megawatt', 'substation', 'pipeline', 'desilting').

### 3. Graph Manifold / UMAP Embedding
- **Global & Local Balance:** Preserves both local clustering and broader inter-class relationships using fuzzy simplicial sets / Laplacian graph eigenspaces.
- **Civic Observation:** Exhibits the highest category separability while preserving the semantic proximity between `road_closure` and `severe_weather` (since heavy rain causes road inundations).
