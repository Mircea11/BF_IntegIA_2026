import csv
import subprocess
import json
import re
import tomllib
from pathlib import Path
from urllib.request import Request, urlopen

from rag_hopital.config import settings

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "reports/E12_judge_sample_26.json"
ANSWERS = ROOT / "reports/E12_baseline_106_answers.csv"
OUTPUT = ROOT / "reports/E12_judge_26_granite8b.jsonl"
CONFIG = ROOT / "experiments/hybrid_bge_bm25_rerank_qwen9b.toml"

sample = json.loads(SAMPLE.read_text(encoding="utf-8"))

with ANSWERS.open(encoding="utf-8", newline="") as f:
    answers = {r["question_id"]: r for r in csv.DictReader(f)}

container = __import__("json").loads(
    subprocess.check_output(
        ["docker", "inspect", "helpdesk-ops-vllm-agent-1"],
        text=True
    )
)[0]

env = dict(
    item.split("=", 1)
    for item in container["Config"]["Env"]
    if "=" in item
)

api_key = next(
    (env[k] for k in ("VLLM_API_KEY", "OPENAI_API_KEY", "API_KEY")
     if env.get(k)),
    None
)

if not api_key:
    raise RuntimeError("Clé API Granite introuvable")

model = "granite4.1:8b"
url = "http://127.0.0.1:8001/v1/chat/completions"

completed = set()

if OUTPUT.exists():
    for line in OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            completed.add(json.loads(line)["question_id"])

system_prompt = """
Tu évalues un assistant RAG sur un corpus médical fictif.

Compare uniquement la réponse générée à la réponse de référence.
N'ajoute aucune connaissance médicale personnelle.

Attribue :
- exactitude : 0 (incorrecte), 1 (partielle), 2 (correcte)
- completude : 0 (absente), 1 (incomplète), 2 (complète)

Si les réponses ne permettent pas de trancher, signale-le
dans la justification.

Réponds uniquement en JSON :
{"exactitude": 0, "completude": 0, "justification": "..."}
"""

for index, question in enumerate(sample, 1):
    qid = question["id"]

    if qid in completed:
        continue

    row = answers[qid]

    input_data = {
        "question": row["question_text"],
        "reference": row["expected_answer"],
        "reponse_generee": row["answer"],
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(input_data, ensure_ascii=False),
            },
        ],
        "temperature": 0,
        "max_tokens": 300,
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )

    with urlopen(request, timeout=180) as response:
        result = json.load(response)

    content = result["choices"][0]["message"]["content"]

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"JSON invalide pour {qid}: {content}")

    evaluation = json.loads(match.group())

    for key in ("exactitude", "completude"):
        if evaluation.get(key) not in (0, 1, 2):
            raise ValueError(f"Note invalide pour {qid}: {evaluation}")

    evaluation["question_id"] = qid
    evaluation["type"] = question["type"]

    with OUTPUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")

    print(
        f"{index:02d}/26 {qid} | "
        f"Exactitude={evaluation['exactitude']}/2 | "
        f"Complétude={evaluation['completude']}/2",
        flush=True,
    )

print("Évaluation terminée :", OUTPUT)
