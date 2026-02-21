from pydantic import BaseModel
from typing import List, Optional


class IndexRequest(BaseModel):
    repo_url: str


class IndexResponse(BaseModel):
    message: str
    repo: str
    num_files: int
    num_chunks: int
    skipped_files: int
    languages: List[str]


class RetrievedChunk(BaseModel):
    content: str
    filepath: str
    language: str
    chunk_type: str        # "function" | "class" | "file"
    symbol_name: str       #  name of the function or class that code was from
    start_line: int
    similarity_score: float
    chunk_length: int


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 6


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    num_chunks_retrieved: int
    repo: Optional[str] = None
