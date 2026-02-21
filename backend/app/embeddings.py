import os
import time
from typing import List
import numpy as np
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 3072


def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
    for attempt in range(5):
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type=task_type,
            )
            return result["embedding"]
        except ResourceExhausted:
            print(f"retry {attempt + 1}/5")
            time.sleep(30)
    raise RuntimeError("failed after 5 retries")


def embed_chunks(chunks: List[str], batch_size: int = 20) -> np.ndarray:
    """
    Embed a list of code chunks
    Returns numpy array of shape (num_chunks, EMBEDDING_DIM)
    """

    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        batch_embeddings = []

        for text in batch:
            embedding = embed_text(text, task_type="RETRIEVAL_DOCUMENT")
            batch_embeddings.append(embedding)
            time.sleep(0.65)    # delay calls to stay under the rate limit

        all_embeddings.extend(batch_embeddings)
        print(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")

    return np.array(all_embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embed the query
    """
    embedding = embed_text(query, task_type="RETRIEVAL_QUERY")  # use RETRIEVAL_QUERY because not code
    return np.array([embedding], dtype=np.float32)
