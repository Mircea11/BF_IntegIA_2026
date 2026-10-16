# AI Integration Specialist — Training & Applied Work (2026)

**Training period:** July–December 2026 · **Last reviewed:** 16 October 2026

## Purpose

This repository records training exercises, notebooks, datasets and technical experiments in SQL, Python, data engineering, deep learning and AI integration. My professional background is industrial market intelligence, forecasting, production planning, supply-chain data and reporting. I am developing practical skills across the full path from data intake to validated decision support.

**Status:** Learning repository, not a collection of production-ready applications. The content includes instructor materials, independently attempted exercises, adapted examples, AI-assisted work and generated outputs. Repository presence does not establish independent mastery.

## Training path

| Period | Modules |
|---|---|
| July 2026 | Relational database modelling; declarative and procedural SQL |
| August 2026 | Python fundamentals and OOP; SQLAlchemy, requests, async Python; NumPy/Polars |
| September 2026 | LLM concepts, Git, Keras/PyTorch, vLLM, Docker and ETL |
| October, through 16 October | Docling, Qdrant, RAG retrieval and evaluation; n8n introduction |
| Upcoming | Advanced RAG, agent orchestration/monitoring, deployment, safety, fine-tuning and final project |

## Repository navigation

| Directory | Main contents |
|---|---|
| [Specialist_IA](Specialist_IA/) | Relational modelling, SQL, Python and OOP exercises |
| [formation](formation/) | Technical training, vLLM, Docker and related exercises |
| [deeplearning](deeplearning/) | ML/DL notebooks and model experiments |
| [ETL](ETL/) | ETL resources, data and training exercises |
| [RAG](RAG/) | Document extraction, embeddings, Qdrant and RAG evaluation |
| [N8N](N8N/) | Workflow automation course resources |
| [recovered_training](recovered_training/) | Recovered and supplementary files; may contain duplicates and third-party content |

## Selected practical work

### SQL and Python
PostgreSQL data modelling and queries; Python OOP projects covering banking, vehicles and games; API/JSON handling; asynchronous Python; DataFrame and visualization exercises.

### RAG document processing and evaluation
The October experiments use a synthetic Veltis document corpus to investigate extraction, indexing, retrieval, reranking and answer generation.

- **Extraction:** Docling, PDF/HTML/DOCX/PPTX processing and structured JSON/Markdown.
- **Indexing and retrieval:** BGE-M3 embeddings, Qdrant, dense retrieval, BM25 sparse retrieval and hybrid Reciprocal Rank Fusion (RRF).
- **Chunking experiments:** comparison of approximately 100-token and 544-token configurations.
- **Tracking:** PostgreSQL metadata and provenance-related exercises.
- **Evaluation:** 22-question evaluation set, document/evidence hit metrics, baseline-versus-enriched comparisons and retrieval regressions.
- **Reranking and generation:** BGE reranking with Top-10/Top-20 comparisons; local vLLM and Nemotron generation with retrieved evidence.

Key notebooks:
- [Hybrid dense/sparse retrieval — 14 October](RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex14-10-26_Qdrant_dense_sparse_hybrid_RRF.ipynb)
- [RAG and PostgreSQL — 14 October](RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex14-10-26_RAG_100_LLM_PostgreSQL.ipynb)
- [Integrated RAG notebook — 15 October](RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex15-10-26_RAG_100_LLM_PostgreSQL_REEXECUTABLE.ipynb)

These notebooks contain saved code and outputs. A clean-install, end-to-end reproducibility check remains to be documented; performance on a training corpus must not be generalized to other datasets.

## Environment and reproducibility

Exercises use Python/Jupyter, PostgreSQL, Qdrant, Docker, Docling, vLLM and other packages. Some require a course GPU workstation, running local model services, local databases and datasets. There is **no verified single setup** that executes the entire repository.

To reproduce an experiment: inspect its own setup notes and dependency files, create an isolated environment, configure services and input data, remove environment-specific paths/credentials, then execute from the beginning and compare results.

## Current learning priorities

1. Explain and independently reproduce the document → extraction → metadata → chunks → embeddings → retrieval → reranking → answer workflow.
2. Validate retrieval with ground-truth evidence, regression tests and explicit metrics.
3. Document one experiment sufficiently for another person to reproduce.
4. Continue the scheduled n8n training while strengthening independent Python and SQL fundamentals.

## Repository maintenance

- [ ] Add reproducible setup notes for one primary RAG experiment.
- [ ] Separate instructor assets, duplicate/recovered files and original exercises.
- [ ] Record benchmark definitions, environment, parameters and results.
- [ ] Check repository history and files for credentials, confidential information and redistribution rights.
- [ ] Promote one validated case study into a separate professional portfolio.

## Attribution

Teaching slides, exercises, reference datasets, tutorials and third-party projects belong to their respective authors and are subject to their terms. Do not assume all contents are open-licensed. Work may include guided or AI-assisted development; individual competence is assessed separately.

---
*Training log and experiment archive · Reviewed 16 October 2026.*
