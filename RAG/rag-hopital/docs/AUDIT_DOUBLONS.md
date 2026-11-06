# RAG Hôpital — Audit des doublons et traçabilité des sources (v3)

**État : prototype expérimental, sans modification de la baseline.**

## 1. Où placer le contrôle ?

`data/hopital/` → conversion → `scripts/chunk_corpus.py` → `data/chunks/chunks.jsonl` → **audit exact + MinHashLSH/Jaccard** → **copie JSONL avec provenance** → **validation** → décision humaine → **nouvelle** collection Qdrant si l'expérience est approuvée.

C'est une expérience possible pour la section 8 de l'exercice. Elle ne remplace pas le travail enregistré dans PostgreSQL.

## 2. Installation initiale (ne pas écraser l'existant)

Dans le terminal VS Code :

```bash
cd ~/formation/RAG/rag-hopital
source .venv/bin/activate
unzip -n ~/Downloads/rag_hopital_dedup_audit_v3.zip -d .
python -c 'import datasketch; print("datasketch OK")'
```

Si `datasketch` manque, l'installer dans **cet** environnement uniquement (`uv pip install datasketch` avec le `.venv` activé, ou `python -m pip install datasketch` si `pip` est disponible). On peut aussi lancer un audit **exact uniquement** avec `--skip-lsh`.

## 3. Exécuter le contrôle initial — mode prudent

```bash
python scripts/audit_duplicates.py --emit-safe-copy
python scripts/validate_dedup_preview.py
sed -n '1,100p' reports/dedup_audit/SYNTHESE.md
```

Le mode par défaut `same-document` fusionne **uniquement** des chunks dont le texte est *strictement* identique, appartenant au **même document et à la même identité patient**. Il ne fait aucune suppression inter-document, ne touche pas à `data/chunks/chunks.jsonl`, ne supprime rien dans Docker et ne contacte ni Qdrant ni PostgreSQL.

Pour un audit limité aux doublons exacts (si la bibliothèque LSH est absente) :

```bash
python scripts/audit_duplicates.py --emit-safe-copy --skip-lsh
python scripts/validate_dedup_preview.py
```

## 4. Où sont les références de tous les documents ?

Dans chaque ligne de `data/chunks/chunks_dedup_preview.jsonl` :

```json
{
  "chunk_id": "consultation_A.docx::12",
  "document": "consultation_A.docx",
  "text": "Passage identique conservé...",
  "occurrence_count": 3,
  "duplicate_count": 2,
  "source_document_count": 2,
  "source_documents": ["consultation_A.docx", "consultation_B.docx"],
  "source_chunk_ids": ["consultation_A.docx::12", "consultation_A.docx::13", "consultation_B.docx::7"],
  "source_references": [
    {"document": "consultation_A.docx", "chunk_id": "consultation_A.docx::12", "chunk_index": 12, "patient_ipp": "001", "date": "2026-01-02", "title": "A"},
    {"document": "consultation_A.docx", "chunk_id": "consultation_A.docx::13", "chunk_index": 13, "patient_ipp": "001", "date": "2026-01-02", "title": "A"},
    {"document": "consultation_B.docx", "chunk_id": "consultation_B.docx::7", "chunk_index": 7, "patient_ipp": "001", "date": "2026-01-05", "title": "B"}
  ]
}
```

*Exemple schématique* : le script conserve **tous** les champs de métadonnées réels de chaque chunk dans `source_references`, sauf le texte dupliqué. Les champs `patient_name`, `doc_type`, `service`, `care_path`, `format`, etc. restent disponibles. Les métadonnées au niveau supérieur (`document`, `date`, `title`...) continuent de désigner la **source primaire**. Pour citer toutes les sources ou vérifier les dates, consulter **source_references**, et non seulement `document`.

`duplicate_count` = occurrences supplémentaires (3 occurrences ⇒ 2 doublons). `occurrence_count` = nombre total d'occurrences (3).

## 5. Option expérimentale : fusion entre documents du même patient

**Ne lancer qu'après avoir examiné les résultats de l'audit prudent.**

```bash
python scripts/audit_duplicates.py --emit-safe-copy --preview-scope same-patient
python scripts/validate_dedup_preview.py --preview-scope same-patient
```

Ce mode autorise la fusion inter-document **seulement** si les textes bruts sont strictement identiques et que `patient_ipp` est **connu et identique**. Les documents sans IPP (par exemple, des notices générales) ne sont **pas** fusionnés entre eux. Les passages simplement similaires (Jaccard élevé, MinHash) ne sont **jamais** fusionnés automatiquement. Des textes identiques de patients différents ne sont jamais fusionnés.

**Réserve métier :** un passage peut être identique mais apparaître dans des documents de dates ou de types différents. Le script garde toutes les dates et les titres en provenance ; toutefois, un humain doit vérifier que la présentation RAG n'attribue pas la preuve à la mauvaise consultation.

**Attention :** les deux commandes de génération utilisent le même nom de copie et les mêmes rapports, et régénèrent uniquement ces *fichiers d'expérience*. Il faut archiver les résultats d'un mode avant de lancer l'autre si l'on veut comparer les deux.

## 6. Rapports produits

- `reports/dedup_audit/SYNTHESE.md` : bilan et premières paires à inspecter.
- `reports/dedup_audit/documents_exact_sha256.csv` : fichiers DOCX/PDF identiques à l'octet près.
- `reports/dedup_audit/chunks_exact_sha256.csv` : textes de chunks exactement identiques.
- `reports/dedup_audit/chunks_normalized_sha256.csv` : tous les groupes identiques après normalisation (y compris brut identique).
- `reports/dedup_audit/chunks_normalized_format_variants.csv` : groupes dont les textes bruts diffèrent malgré une normalisation identique, **pour revue uniquement**.
- `reports/dedup_audit/documents_similar_lsh_candidates.csv` : documents candidats similaires.
- `reports/dedup_audit/chunks_similar_lsh_candidates.csv` : chunks candidats similaires.
- `reports/dedup_audit/preview_merged_groups.csv` : **tous les groupes consolidés et leurs documents**.
- `reports/dedup_audit/chunks_preview_exclusions.csv` : correspondance ID exclu → ID conservé.
- `data/chunks/chunks_dedup_preview.jsonl` : **copie séparée**, avec `source_references` dans chaque point.

Notebooks : `notebooks/duplicate_audit_review.ipynb` inspecte l'audit, montre les sources et compare Jaccard sur un exemple réel. `notebooks/duplicate_original_reference.ipynb` est une copie de l'exercice initial ; il ne se substitue pas au notebook du formateur.

## 7. Validation de la traçabilité

La commande `python scripts/validate_dedup_preview.py` vérifie entre autres :

1. Chaque chunk d'origine est présent **une fois et une seule** dans les `source_references` de la copie.
2. Chaque référence conserve ses métadonnées initiales (`date`, document, patient, titre...).
3. Tous les textes fusionnés sont strictement égaux.
4. Aucun regroupement inter-patients ; aucun regroupement inter-documents dans le mode prudent.
5. `duplicate_count`, `source_chunk_ids`, `source_documents`, SHA-256 sont cohérents.

Un rapport `PASS` signifie **traçabilité correcte selon les règles vérifiées**, et non validation médicale de la fusion.

## 8. Évaluation et limites

- Le SHA-256 normalisé aligne l'audit avec la première partie du cours 07 : majuscules, accents, ponctuation ou espaces peuvent différer. Il ne provoque **aucune fusion automatique** (par exemple, la normalisation de `2.5` et `2 5` est la même).
- Le cours 07 illustre `shingles(n=2)`, `MinHash(num_perm=128)`, `MinHashLSH(threshold=0.2)` sur 4 textes. Les réglages par défaut pour le corpus Hôpital sont `--k 3` et `--lsh-threshold 0.65` pour limiter le nombre de paires proposées. Ils sont paramétrables.
- Le cours 07 comporte aussi **MMR** : intervention au niveau du retrieval, après fusion dense/sparse par RRF. Nous ne l'installons **pas** durant l'audit de doublons ; c'est une expérience distincte.
- Les documents comparés par Jaccard sont reconstruits depuis les chunks existants : leur score n'est pas une comparaison canonique des DOCX/PDF. Les shingles sont des trigrammes de mots par défaut. MinHashLSH ne garantit pas de retrouver toutes les paires similaires : c'est un filtre probabiliste.
- Le script d'indexation existant lit `data/chunks/chunks.jsonl` et utilise des collections existantes. **Ne pas le réorienter vers la copie sans créer explicitement une collection d'expérience distincte** : sinon on mélange des conditions expérimentales.
- Pour l'évaluation E11, la fonction courante `judge_chunk(question, document, text)` vérifie `evidence['document'] == document`. Après fusion multi-documents, il faut utiliser les documents présents dans **`source_references`**, faute de quoi des preuves reconnues seront artificiellement perdues. Un petit exemple d'adaptation est fourni dans `docs/evaluation_source_references.py` (non branché à la baseline).
- Baseline E11 avec reranking : Hit@5 88 %, Fact Recall@5 92,63 %, nDCG@5 80,89 %. Mesurer les mêmes indicateurs après déduplication, en contrôlant les autres paramètres (embedder, candidats, prompts, etc.).
- **Aucun chiffre de doublons réels n'est avancé avant exécution sur le corpus local**.
- Pour vérifier le module seul : `python -m unittest discover -s tests -p test_dedup_provenance.py -v`.

## 9. Compatibilité vérifiée avec le notebook `07_indexation_avancee.ipynb`

Voir `docs/ALIGNEMENT_FORMATEUR_07.md`. Le code du professeur utilise `Veltis`, un serveur d'embeddings et un port Qdrant qui **ne sont pas** ceux de RAG Hôpital. Ne pas recopier ses constantes de connexion.
