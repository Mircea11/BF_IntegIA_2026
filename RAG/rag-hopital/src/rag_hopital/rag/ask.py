"""
Hospital RAG — E12
Generation of answers grounded in retrieved documents.
"""

import json
from time import perf_counter
from urllib.request import Request, urlopen

from rag_hopital.rag.search import search


def build_passages(chunks):
    """Format retrieved chunks with numbered source identifiers."""

    return "\n\n".join(
        f'<passage id="{i}">\n'
        f'{chunk.payload["text"]}\n'
        f'</passage>'
        for i, chunk in enumerate(chunks, 1)
    )


def generate_answer(
    question,
    chunks,
    *,
    model,
    llm_url,
    system_prompt,
    max_tokens=400,
    enable_thinking=None,
):
    """Call an OpenAI-compatible LLM server."""

    user_prompt = (
        build_passages(chunks)
        + "\n\nQuestion : "
        + question
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }

    # Optional: some models support explicit thinking control.
    if enable_thinking is not None:
        payload["chat_template_kwargs"] = {
            "enable_thinking": enable_thinking
        }

    request = Request(
        llm_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urlopen(request, timeout=180) as response:
        result = json.load(response)

    return {
        "answer": result["choices"][0]["message"]["content"],
        "finish_reason": result["choices"][0]["finish_reason"],
        "usage": result.get("usage"),
        "model": model,
    }


def ask(
    question,
    *,
    model,
    llm_url,
    system_prompt,
    method="hybrid",
    candidates=30,
    top_k=5,
    rerank=True,
    max_tokens=400,
    enable_thinking=None,
):
    """Run retrieval, reranking and answer generation."""

    start = perf_counter()

    chunks = search(
        query=question,
        method=method,
        candidates=candidates,
        top_k=top_k,
        rerank=rerank,
    )

    retrieval_seconds = perf_counter() - start

    if not chunks:
        return {
            "question": question,
            "answer": None,
            "sources": [],
            "retrieval_seconds": retrieval_seconds,
            "total_seconds": perf_counter() - start,
            "status": "no_passages",
        }

    result = generate_answer(
        question,
        chunks,
        model=model,
        llm_url=llm_url,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        enable_thinking=enable_thinking,
    )

    result.update({
        "question": question,
        "sources": [
            {
                "id": i,
                "document": chunk.payload.get("document"),
                "chunk_index": chunk.payload.get("chunk_index"),
            }
            for i, chunk in enumerate(chunks, 1)
        ],
        "retrieval_seconds": round(retrieval_seconds, 2),
        "total_seconds": round(perf_counter() - start, 2),
        "status": "completed",
    })

    return result
