from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768

_model: SentenceTransformer = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_chunks(chunks: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Embed a list of code chunks in batches.
    Returns numpy array of shape (num_chunks, EMBEDDING_DIM)
    """

    model = _get_model()
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        embeddings = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.append(embeddings)
        print(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")

    return np.vstack(all_embeddings).astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    model = _get_model()
    prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
    embedding = model.encode(prefixed_query, normalize_embeddings=True)
    return np.array([embedding], dtype=np.float32)