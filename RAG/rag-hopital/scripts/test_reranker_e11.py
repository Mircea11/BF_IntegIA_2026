# E11.4 — Test du reranker BGE-M3 local
# Exécution sur CPU, sans téléchargement

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1. Chemin du modèle existant
MODEL_PATH = "/home/bm/models/rag/reranker/bge-reranker-v2-m3"

# 2. Question et documents
question = "Quel traitement est prescrit au patient diabétique ?"

documents = [
    "Le patient diabétique reçoit un traitement par metformine.",
    "Le patient présente une fracture du poignet après une chute.",
]

# 3. Charger le tokenizer et le modèle local
print("Chargement du reranker...")

torch.set_num_threads(2)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True
).to("cpu")

model.eval()

# 4. Préparer les paires question-document
pairs = [[question, document] for document in documents]

inputs = tokenizer(
    pairs,
    padding=True,
    truncation=True,
    return_tensors="pt",
    max_length=512
)

# 5. Calculer les scores de pertinence
with torch.inference_mode():
    scores = model(**inputs).logits.view(-1).tolist()

# 6. Classer les documents
results = sorted(
    zip(documents, scores),
    key=lambda item: item[1],
    reverse=True
)

# 7. Afficher les résultats
print("\n=== RÉSULTATS DU RERANKING ===")

for rank, (document, score) in enumerate(results, start=1):
    print(f"{rank}. Score : {score:.4f}")
    print(f"   {document}")

print("\nE11.4 : TEST TERMINÉ")