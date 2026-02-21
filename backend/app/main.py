import shutil

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    IndexRequest, IndexResponse,
    QueryRequest, QueryResponse,
    RetrievedChunk,
)
from app.ingest import clone_repo, ingest_repo
from app.embeddings import configure_gemini, embed_chunks, embed_query
from app.retrieval import (
    build_index, save_index, load_index, search,
    index_exists, get_index_size, get_repo_info,
)
from app.generator import generate_answer

app = FastAPI(
    title="Repo RAG — Codebase Q&A",
    description="Index a GitHub repository and ask natural language questions about the code.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

CLONE_DIR = "data/repo"


@app.on_event("startup")
async def startup():
    configure_gemini()
    print("Gemini configured")

@app.post("/index", response_model=IndexResponse)
async def index_repo(request: IndexRequest):
    """
      1. git clone with --depth=1 (to shallow clone)
      2. Walk through every code file
      3. Split files into chunks using AST-aware approach
      4. Embed each chunk with Gemini gemini-embedding-001 (RETRIEVAL_DOCUMENT)
      5. Store embeddings in FAISS
    """

    repo_url = request.repo_url.strip().rstrip("/")

    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="Please provide a full GitHub URL (https://github.com/owner/repo)."
        )

    # Clone
    print(f"Cloning {repo_url}...")
    try:
        clone_repo(repo_url, CLONE_DIR)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Ingest
    print("Ingesting files...")
    chunks, languages, skipped = ingest_repo(CLONE_DIR)

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No indexable source files found in this repository."
        )

    print(f"Found {len(chunks)} chunks across {len(languages)} languages.")

    # Embed
    print("Embedding chunks...")
    texts = [c["content"] for c in chunks]
    embeddings = embed_chunks(texts)

    # Index
    print("Building FAISS index...")
    index = build_index(embeddings)

    repo_info = {
        "repo_url": repo_url,
        "num_files": len(set(c["filepath"] for c in chunks)),
        "num_chunks": len(chunks),
        "languages": languages,
    }
    save_index(index, chunks, repo_info)

    # Clean up clone to save disk space
    shutil.rmtree(CLONE_DIR, ignore_errors=True)

    return IndexResponse(
        message="Repository indexed successfully.",
        repo=repo_url,
        num_files=repo_info["num_files"],
        num_chunks=len(chunks),
        skipped_files=skipped,
        languages=languages,
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
      1. Embed query
      2. FAISS top-k search
      3. Build prompt
      4. Generate answer with gemini
      5. Return answer + source chunks + scores
    """

    if not index_exists():
        raise HTTPException(
            status_code=404,
            detail="No index found. POST to /index with a GitHub repo URL first."
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    query_embedding = embed_query(request.question)
    index, metadata = load_index()
    raw_results = search(index, metadata, query_embedding, top_k=request.top_k)

    if not raw_results:
        raise HTTPException(status_code=500, detail="No results from index.")

    repo_info = get_repo_info()
    repo_url = repo_info.get("repo_url", "") if repo_info else ""

    answer = generate_answer(request.question, raw_results, repo=repo_url)
    chunks = []
    for r in raw_results:
        chunk = RetrievedChunk(**r)
        chunks.append(chunk)

    return QueryResponse(
        question=request.question,
        answer=answer,
        retrieved_chunks=chunks,
        num_chunks_retrieved=len(chunks),
        repo=repo_url,
    )
