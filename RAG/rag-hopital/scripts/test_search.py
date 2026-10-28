from rag_hopital.rag.search import search


question = "Quelle est la glycémie à jeun de Mme Anne DUBOIS ?"

results = search(question, top_k=5)

for rank, point in enumerate(results, 1):
    print(f"\n--- Result {rank} ---")
    print("Score:", round(point.score, 4))
    print("Document:", point.payload["document"])
    print("Patient:", point.payload["patient_name"])
    print("Text:", point.payload["text"][:500])