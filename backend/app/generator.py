import os
from typing import List, Dict
import google.generativeai as genai

GENERATION_MODEL = "gemini-2.5-flash-lite"


def build_prompt(question: str, chunks: List[Dict], repo: str = "") -> str:
    """
    Build prompt

    Structure
    - Each chunk labeled with file path, language, symbol name, and score
    - Cite file paths in the answer
    """

    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        symbol = f" · {chunk['symbol_name']}" if chunk['symbol_name'] else ""
        header = (
            f"[Chunk {i} | {chunk['filepath']}{symbol} | "
            f"{chunk['language']} | score: {chunk['similarity_score']}]"
        )
        context_blocks.append(f"{header}\n```{chunk['language']}\n{chunk['content']}\n```")

    context = "\n\n---\n\n".join(context_blocks)
    repo_line = f" The repository is: {repo}." if repo else ""

    prompt = f"""
    You are an experienced software engineer helping a developer navigate and understand a codebase.{repo_line}
    
    RULES:
    - Answer using ONLY the code context provided below. Do not invent functions, classes, or files that are not shown.
    - If the answer is not in the provided context, say exactly: "Not found in the indexed codebase."
    - Always cite file paths when referencing specific code (e.g., "In `src/auth.py`...").
    - Be concise and precise. Developers want direct answers, not essays.
    - If asked where something is implemented, give the file path and function/class name.
    - If asked how something works, explain the logic from the actual code shown.
    
    CODE CONTEXT:
    {context}
    
    QUESTION:
    {question}
    
    ANSWER:
    """

    return prompt


def generate_answer(question: str, chunks: List[Dict], repo: str = "") -> str:

    prompt = build_prompt(question, chunks, repo)
    model = genai.GenerativeModel(GENERATION_MODEL)

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=2048,
        ),
    )

    return response.text.strip()
