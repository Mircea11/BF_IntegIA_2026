# E17 — RAG Hôpital : hybrid RRF versus MMR

## Purpose
Compare the instructor's notebook 07 (nested hybrid prefetch RRF followed by Qdrant MMR) against the already implemented E11 RRF retrieval. Keep E11 code, 100-question scores, and Qdrant collections untouched.

**Source alignment:** 07_indexation_avancee.ipynb, section "Maximal Marginal Relevance (MMR)"; Qdrant 1.19.1 supports MMR; Python `qdrant-client` must expose `models.Mmr` and `models.NearestQuery`.

## Install
From your own project root:

    cd ~/formation/RAG/rag-hopital
    source .venv/bin/activate
    unzip -n ~/Downloads/rag_hopital_E17_MMR_trial.zip -d .
    python scripts/check_e17_readiness.py

The archive only adds `scripts/experiment_mmr_e17.py`, `scripts/check_e17_readiness.py`, and `docs/E17_MMR_README.md`.

## Start only BGE-M3 embeddings (in SECOND Ubuntu terminal)

Check the endpoint printed by `check_e17_readiness.py` first; use the port from that endpoint. The previously used server was port 8101. In the second terminal:

    source ~/formation/formation/vLLM/vllm_server/.venv/bin/activate
    vllm serve /home/bm/models/rag/embedder/bge-m3 \
      --runner pooling --host 127.0.0.1 --port 8101 \
      --gpu-memory-utilization 0.2

**Do not run** `docker compose start` in helpdesk-ops. The command is for the embedding model alone. Keep it running during the trial. If the default vLLM backend does not serve BGE-M3 embeddings, consult your vLLM version's BGE-M3 pooling architecture configuration before retrying; do not reinstall everything blindly.

Confirm the service is running:

    curl -s http://127.0.0.1:8101/v1/models

Check model path and embeddings URL in `.env`: printed by readiness command. A mismatch between configured model name/path and served model name can cause a 404 for embeddings.

## Run trial (first terminal; rag-hopital venv)

    cd ~/formation/RAG/rag-hopital
    source .venv/bin/activate
    python scripts/check_e17_readiness.py
    python scripts/experiment_mmr_e17.py \
      --question "allergies médicamenteuses" --patient-ipp 4100001

This compares baseline RRF vs RRF+MMR **without reranker**, so only the MMR stage changes. For an additional E11 comparison with CPU reranker:

    python scripts/experiment_mmr_e17.py \
      --question "allergies médicamenteuses" \
      --patient-ipp 4100001 --rerank --mmr-pool 15 \
      --output reports/mmr/E17_pilot_rerank.json

MMR-with-rerank selects 15 intermediate results rather than the 30 reranked by baseline E11; measure the effect rather than declaring equivalence. The patient currently has only 16 indexed chunks; filtered examples may not provide enough diversity to showcase MMR. Repeat on a relevant multi-evidence question, with the same patient setting on both arms.

## Meaning of results
- 0.0 diversity: maximize query relevance; 1.0: maximize diversity. Initial 0.6 is a test value, NOT an optimum.
- Mean pairwise trigram Jaccard measures lexical redundancy among retrieved results, not semantic correctness.
- Qdrant MMR scores and RRF scores are not directly comparable.
- A full E11 comparison requires the 100-question benchmark (Hit@5, Fact Recall@5, nDCG@5) with matching conditions; this pilot does not calculate those metrics.
- Without a patient filter, mixed-patient results are possible. For evaluation, consider patient-specific questions and general medication-notice questions separately.
- Qdrant data is not changed. The script writes only `reports/mmr/E17_pilot.json` and, optionally, a second local JSON.

## Stop model after the experiment
In the separate terminal where vLLM is running press `Ctrl+C` and wait for it to exit. This does not affect HelpDesk-Ops Docker containers.
