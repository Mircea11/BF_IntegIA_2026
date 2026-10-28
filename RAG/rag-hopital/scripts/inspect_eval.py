import json
from collections import Counter

from rag_hopital.config import settings

path = settings.corpus_path / "hopital_eval.json"

questions = json.loads(path.read_text(encoding="utf-8"))

print("Total questions:", len(questions))

print("\nQuestions by type:")
for question_type, count in sorted(
    Counter(q["type"] for q in questions).items()
):
    print(f"{question_type}: {count}")

print("\nFirst question:")
print(json.dumps(questions[0], indent=2, ensure_ascii=False))
