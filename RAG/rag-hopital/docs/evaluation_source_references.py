"""Reference example ONLY — not wired into the production evaluator.

The original judge_chunk(question, document, text) compares against ONE document.
After cross-document consolidation the evidence document may be any preserved source.

Do not substitute this blindly into E11. Keep a separate experiment.
"""


def judge_chunk_from_sources(question: dict, payload: dict) -> list[dict]:
    text = str(payload.get("text", "")).casefold()
    refs = payload.get("source_references") or [{"document": payload.get("document")}]
    valid_docs = {str(ref.get("document")) for ref in refs}
    matches = []
    for evidence in question.get("evidence", []):
        if str(evidence.get("document")) not in valid_docs:
            continue
        if all(str(snippet).casefold() in text for snippet in evidence.get("snippets", [])):
            matches.append(evidence)
    return matches
