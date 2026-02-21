import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".md": "markdown",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".env": "env",
    ".sh": "bash",
    ".bash": "bash",
    ".dockerfile": "dockerfile",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".txt": "text",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", "vendor", "target", "out", "bin", "obj",
    ".idea", ".vscode", "*.egg-info",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".whl", ".lock",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".min.js", ".min.css", ".map",
}

MAX_FILE_BYTES = 150_000   # skip files larger than this
MAX_TOTAL_FILES = 500      # cap total files indexed
CHUNK_SIZE = 1200          # chars per chunk for plain-text chunking for non code files (ex. markdown, yml)
CHUNK_OVERLAP = 200

def clone_repo(repo_url: str, destination: str) -> str:
    """
    Shallow-clone a public GitHub repo
    Returns the local path
    Raises on failure
    """

    if os.path.exists(destination):
        shutil.rmtree(destination)

    result = subprocess.run(
        ["git", "clone", "--depth=1", repo_url, destination],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(f"git clone failed:\n{result.stderr}")

    return destination

def should_skip(abs_path: Path, rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in SKIP_DIRS:
            return True

    suffix = abs_path.suffix.lower()
    name = abs_path.name.lower()

    if suffix in SKIP_EXTENSIONS:
        return True
    if name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    if abs_path.stat().st_size > MAX_FILE_BYTES:
        return True
    return False


def walk_repo(repo_path: str) -> List[Tuple[Path, str]]:
    """
    Walk repo and return list of (path, language)
    """

    # convert the string into a Path object for cleaner file handling
    root = Path(repo_path)
    results = []

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        # Get relative path
        rel = p.relative_to(root)
        if should_skip(p, rel):
            continue

        # Check extension
        suffix = p.suffix.lower()
        # Special case for Dockerfile
        if p.name == "Dockerfile" or p.name.startswith("Dockerfile."):
            lang = "dockerfile"
        else:
            lang = EXTENSION_MAP.get(suffix)

        if lang is None:
            continue  # unknown extension — skip

        results.append((p, lang))

        # File limit protection
        if len(results) >= MAX_TOTAL_FILES:
            break

    return results


# Chunking strategies

def chunk_python(source: str, filepath: str) -> List[Dict]:
    """
    Split by def and class statements
    """

    chunks = []
    # Match def or class at column 0 (top-level only)
    pattern = re.compile(r'^(def |class )', re.MULTILINE)
    lines = source.splitlines(keepends=True)
    matches = [m.start() for m in pattern.finditer(source)]

    if not matches:
        return chunk_plain(source, filepath, "python")

    # Build position → line number map
    pos_to_line = {}
    pos = 0
    for i, line in enumerate(lines):
        pos_to_line[pos] = i + 1
        pos += len(line)

    def nearest_line(char_pos):
        candidates = [p for p in pos_to_line if p <= char_pos]
        return pos_to_line[max(candidates)] if candidates else 1

    for i, start in enumerate(matches):
        end = matches[i + 1] if i + 1 < len(matches) else len(source)
        block = source[start:end].rstrip()
        if not block.strip():
            continue

        # Extract symbol name
        first_line = block.split('\n')[0]
        sym_match = re.match(r'(?:def |class )(\w+)', first_line)
        symbol = sym_match.group(1) if sym_match else ""
        chunk_type = "function" if first_line.startswith("def ") else "class"

        chunks.append({
            "content": block,
            "filepath": filepath,
            "language": "python",
            "chunk_type": chunk_type,
            "symbol_name": symbol,
            "start_line": nearest_line(start),
        })

    if chunks:
        return chunks
    else:
        return chunk_plain(source, filepath, "python")


def chunk_js_ts(source: str, filepath: str, language: str) -> List[Dict]:
    """
    Split by function/class/arrow-function definitions
    """

    chunks = []
    pattern = re.compile(
        r'^(?:export\s+)?(?:async\s+)?(?:function\s+\w+|class\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?\()',
        re.MULTILINE
    )
    matches = [m.start() for m in pattern.finditer(source)]

    if not matches:
        return chunk_plain(source, filepath, language)

    lines = source.splitlines(keepends=True)
    pos_to_line = {}
    pos = 0
    for i, line in enumerate(lines):
        pos_to_line[pos] = i + 1
        pos += len(line)

    def nearest_line(char_pos):
        candidates = [p for p in pos_to_line if p <= char_pos]
        return pos_to_line[max(candidates)] if candidates else 1

    for i, start in enumerate(matches):
        end = matches[i + 1] if i + 1 < len(matches) else len(source)
        block = source[start:end].rstrip()
        if not block.strip():
            continue

        first_line = block.split('\n')[0]
        sym_match = re.search(r'(?:function|class|const)\s+(\w+)', first_line)
        symbol = sym_match.group(1) if sym_match else ""
        chunk_type = "class" if "class " in first_line else "function"

        chunks.append({
            "content": block,
            "filepath": filepath,
            "language": language,
            "chunk_type": chunk_type,
            "symbol_name": symbol,
            "start_line": nearest_line(start),
        })

    if chunks:
        return chunks
    else:
        return chunk_plain(source, filepath, language)


def chunk_plain(source: str, filepath: str, language: str) -> List[Dict]:
    """
    Generic sliding-window chunker for languages without a smart parser.
    """

    chunks = []
    text = source
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        if end < len(text):
            boundary = text.rfind('\n', start, end)
            if boundary > start:
                end = boundary

        block = text[start:end].strip()
        if block:
            # Estimate start line
            start_line = text[:start].count('\n') + 1
            chunks.append({
                "content": block,
                "filepath": filepath,
                "language": language,
                "chunk_type": "file",
                "symbol_name": "",
                "start_line": start_line,
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks

def ingest_repo(repo_path: str) -> Tuple[List[Dict], List[str], int]:
    """
    Walk through every code file and chunk them
    Returns:
      - list of chunk dicts
      - list of unique languages found
      - count of skipped files
    """

    files = walk_repo(repo_path)
    all_chunks = []
    languages_seen = set()
    skipped = 0
    root = Path(repo_path)

    for full_path, language in files:
        try:
            source = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped += 1
            continue

        if not source.strip():
            skipped += 1
            continue

        rel_path = str(full_path.relative_to(root))
        languages_seen.add(language)

        # Optimized chunking for python and js/ts
        if language == "python":
            chunks = chunk_python(source, rel_path)
        elif language in ("javascript", "typescript"):
            chunks = chunk_js_ts(source, rel_path, language)
        else:
            chunks = chunk_plain(source, rel_path, language)

        all_chunks.extend(chunks)

    return all_chunks, sorted(languages_seen), skipped
