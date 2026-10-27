"""Feature extraction module for CivicPulse.

Supports Bag-of-Words (BoW), TF-IDF (unigrams & bigrams), gensim Word2Vec,
pretrained GloVe, FastText (with subword support for misspelled place names),
and Transformer contextual embeddings (BERT / DistilBERT).
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# Configure logging
logger = logging.getLogger(__name__)

RANDOM_SEED = 42


def build_bow_vectorizer(
    texts: List[str],
    max_features: int = 5000,
    binary: bool = False
) -> Tuple[CountVectorizer, Any]:
    """Fit a CountVectorizer (Bag-of-Words) and transform input texts."""
    vectorizer = CountVectorizer(
        max_features=max_features,
        binary=binary
    )
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def build_tfidf_vectorizer(
    texts: List[str],
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2)
) -> Tuple[TfidfVectorizer, Any]:
    """Fit a TF-IDF Vectorizer with unigrams & bigrams and transform input texts."""
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def train_word2vec(
    tokenized_texts: List[List[str]],
    vector_size: int = 100,
    window: int = 5,
    min_count: int = 1,
    seed: int = RANDOM_SEED
):
    """Train a Word2Vec model on the tokenized corpus."""
    from gensim.models import Word2Vec
    model = Word2Vec(
        sentences=tokenized_texts,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=1,
        seed=seed,
        epochs=30
    )
    return model


def get_word2vec_document_vector(
    model: Any,
    tokens: List[str],
    dim: int = 100
) -> np.ndarray:
    """Average word vectors for a token list, returning a document embedding."""
    vectors = []
    for w in tokens:
        if w in model.wv:
            vectors.append(model.wv[w])
    if vectors:
        return np.mean(vectors, axis=0)
    return np.zeros(dim, dtype=np.float32)


def load_glove_vectors(
    glove_path: Union[str, Path],
    dim: int = 50
) -> Dict[str, np.ndarray]:
    """Load GloVe vectors from a text file, or generate a deterministic synthetic set if not present."""
    p = Path(glove_path)
    embeddings_dict: Dict[str, np.ndarray] = {}

    if p.exists():
        logger.info(f"Loading GloVe vectors from {p}...")
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < dim + 1:
                    continue
                word = parts[0]
                vector = np.array(parts[1:dim + 1], dtype=np.float32)
                embeddings_dict[word] = vector
        return embeddings_dict

    # Deterministic fallback: Generate 50d vectors seeded by word hash
    logger.warning(f"GloVe file not found at {p}. Initializing synthetic deterministic GloVe({dim}d).")
    return embeddings_dict


def get_glove_document_vector(
    glove_dict: Dict[str, np.ndarray],
    tokens: List[str],
    dim: int = 50
) -> np.ndarray:
    """Average GloVe vectors for a token list."""
    vectors = []
    for w in tokens:
        if w in glove_dict:
            vectors.append(glove_dict[w])
        elif not glove_dict:
            # Deterministic hash vector fallback
            rng = np.random.RandomState(abs(hash(w)) % (2**31))
            vectors.append(rng.normal(0, 0.2, dim).astype(np.float32))
    if vectors:
        return np.mean(vectors, axis=0)
    return np.zeros(dim, dtype=np.float32)


def train_fasttext(
    tokenized_texts: List[List[str]],
    vector_size: int = 100,
    window: int = 5,
    min_count: int = 1,
    seed: int = RANDOM_SEED
):
    """Train a FastText model with subword n-grams for out-of-vocabulary place names."""
    from gensim.models import FastText
    model = FastText(
        sentences=tokenized_texts,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        min_n=3,
        max_n=6,
        workers=1,
        seed=seed,
        epochs=30
    )
    return model


def get_fasttext_document_vector(
    model: Any,
    tokens: List[str],
    dim: int = 100
) -> np.ndarray:
    """Average FastText vectors for a token list (subwords handle misspelled names)."""
    vectors = []
    for w in tokens:
        try:
            vectors.append(model.wv[w])
        except KeyError:
            continue
    if vectors:
        return np.mean(vectors, axis=0)
    return np.zeros(dim, dtype=np.float32)


def get_bert_embeddings(
    texts: List[str],
    model_name: str = "distilbert-base-uncased",
    pooling: str = "mean",
    batch_size: int = 16
) -> np.ndarray:
    """Extract contextual embeddings using HuggingFace Transformers."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    all_embeddings = []

    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt"
            ).to(device)

            outputs = model(**encoded)

            if pooling == "cls":
                # First token embedding
                batch_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            else:
                # Mean pooling over attention mask
                mask = encoded["attention_mask"].unsqueeze(-1)
                summed = torch.sum(outputs.last_hidden_state * mask, dim=1)
                counts = torch.clamp(mask.sum(dim=1), min=1e-9)
                batch_emb = (summed / counts).cpu().numpy()

            all_embeddings.append(batch_emb)

    return np.vstack(all_embeddings)


def build_document_vectors(
    texts: List[str],
    method: str = "tfidf",
    preprocessor: Any = None,
    **kwargs
) -> Tuple[Any, np.ndarray]:
    """Unified factory interface for generating document representations."""
    from server.nlp.preprocess import default_preprocessor

    prep = preprocessor or default_preprocessor
    cleaned_texts = [prep.preprocess(t) for t in texts]

    if method == "bow":
        vec, mat = build_bow_vectorizer(cleaned_texts, **kwargs)
        return vec, mat.toarray()

    elif method == "tfidf":
        vec, mat = build_tfidf_vectorizer(cleaned_texts, **kwargs)
        return vec, mat.toarray()

    elif method == "word2vec":
        tokenized = [t.split() for t in cleaned_texts]
        dim = kwargs.get("vector_size", 100)
        model = train_word2vec(tokenized, vector_size=dim)
        doc_vecs = np.array([get_word2vec_document_vector(model, tok, dim=dim) for tok in tokenized])
        return model, doc_vecs

    elif method == "fasttext":
        tokenized = [t.split() for t in cleaned_texts]
        dim = kwargs.get("vector_size", 100)
        model = train_fasttext(tokenized, vector_size=dim)
        doc_vecs = np.array([get_fasttext_document_vector(model, tok, dim=dim) for tok in tokenized])
        return model, doc_vecs

    elif method == "bert":
        model_name = kwargs.get("model_name", "distilbert-base-uncased")
        pooling = kwargs.get("pooling", "mean")
        embs = get_bert_embeddings(cleaned_texts, model_name=model_name, pooling=pooling)
        return None, embs

    raise ValueError(f"Unsupported representation method: {method}")
