import json
import os
import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional

INDEX_PATH = "vectorstore/faiss.index"
METADATA_PATH = "vectorstore/metadata.json"
REPO_INFO_PATH = "vectorstore/repo_info.json"

def build_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS IndexFlatIP index with L2-normalized vectors for cosine similarity search
    """

    dim = embeddings.shape[1]
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, metadata: List[Dict], repo_info: Dict):
    os.makedirs("vectorstore", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    with open(REPO_INFO_PATH, "w") as f:
        json.dump(repo_info, f, indent=2)
    print(f"Saved index: {index.ntotal} vectors.")


def load_index() -> Tuple[faiss.Index, List[Dict]]:
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError("No index found. Please index a repo first.")
    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
    return index, metadata


def get_repo_info() -> Optional[Dict]:
    if not os.path.exists(REPO_INFO_PATH):
        return None
    with open(REPO_INFO_PATH, "r") as f:
        return json.load(f)


def search(
    index: faiss.Index,
    metadata: List[Dict],
    query_embedding: np.ndarray,
    top_k: int = 6,
) -> List[Dict]:
    """
    Search FAISS index for most similar  chunks.
    Returns top_k results with similarity scores.
    """

    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata[idx]
        results.append({
            "content": chunk["content"],
            "filepath": chunk["filepath"],
            "language": chunk["language"],
            "chunk_type": chunk["chunk_type"],
            "symbol_name": chunk["symbol_name"],
            "start_line": chunk["start_line"],
            "similarity_score": float(round(score, 4)),
            "chunk_length": len(chunk["content"]),
        })
    return results


def index_exists() -> bool:
    return os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)


def get_index_size() -> int:
    if not index_exists():
        return 0
    return faiss.read_index(INDEX_PATH).ntotal
