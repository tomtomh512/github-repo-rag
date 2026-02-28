# Repo RAG

A RAG application to ask questions about a public GitHub repository. **Optimized for Python and JavaScript/TypeScript projects**

<img src="assets/thumbnail.png">

## Tech Stack
Python, Google Gemini, FAISS, FastAPI

## Running Locally

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Steps

**1. Clone this repository**

```bash
git clone https://github.com/your-username/repo-rag.git
cd repo-rag
```

**2. Set your Gemini API key**

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=example_gemini_key
```

**3. Start the services**

```bash
docker-compose up --build
```


- **Backend:** `http://localhost:8000`
- **Frontend:** `http://localhost:5173`

---

## Index and Query Pipelines

### Index Pipeline (`POST /index`)

1. **Clone:** Shallow-clones the repo into a temporary directory

2. **Walk:** Walk through each file. (Limits: Skips files over 150 KB and up to 500 files are indexed)

3. **Chunk:** Files are split into meaningful chunks based on the code's language
   - **Python:** Splits on top-level `def` and `class` statements
   - **JavaScript/TypeScript:** Splits on `function`, `class`, and top-level `const` arrow function declarations
   - **Everything else:** Sliding window chunking, 1200-char chunks, 200-char overlap
   
   Chunk metadata: `filepath`, `language`, `chunk_type` (`function` | `class` | `file`), `symbol_name`, and `start_line`.

4. **Embed:** Chunks are embedded with `gemini-embedding-001`, producing 3072-dimensional vectors

5. **Store:** Embeddings are L2-normalized and added to a FAISS `IndexFlatIP` index (Index and chunk metadata are persisted to disk under `vectorstore/`)



### Query Pipeline (`POST /query`)

1. **Embed:** Embed query with `gemini-embedding-001`

2. **Search:** The query vector is L2-normalized and searched against the FAISS index. The top-k most similar chunks (default: 6) are returned with cosine similarity scores

3. **Generate:** Retrieved chunks are assembled into a prompt for `gemini-2.5-flash-lite`

4. **Respond:** Return the generated answer, along with the question, and the retrieved source chunks with their scores, filepaths, and symbol names.

---