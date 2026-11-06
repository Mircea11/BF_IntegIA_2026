# RAG Hôpital — Audit des doublons (AVANT Qdrant)

## Méthode
- Chunks existants : `data/chunks/chunks.jsonl` (lecture seule).
- Fichiers source : `data/hopital` (lecture seule).
- Documents exacts : SHA-256 sur les octets DOCX/PDF originaux.
- Chunks exacts : SHA-256 sur le texte brut, avec ligne patient.
- Chunks identiques APRÈS normalisation : SHA-256 du texte normalisé : audit seulement, 
  aucune fusion fondée sur ce hash (la ponctuation et les décimales peuvent être significatives).
- Doublons approximatifs : shingles de 3 mots normalisés, 
  MinHash/LSH (seuil de candidats 0.65) puis Jaccard EXACT des candidats.
- Pour la similarité seulement, la ligne patient ajoutée au chunk est ignorée.
- LSH est probabiliste : des paires similaires peuvent ne pas être proposées.
- Aucun chunk et aucun document n'est supprimé des sources, aucun index modifié.

## Résultats
- Fichiers DOCX/PDF examinés : **280**.
- Groupes de fichiers identiques (SHA-256) : **0**.
- Documents reconstruits des chunks : **280**.
- Chunks examinés : **1173**.
- Groupes de chunks strictement identiques : **0**.
- Groupes de chunks identiques après normalisation : **0**.
- Dont groupes avec textes bruts DISTINCTS (variantes de format ou autre) : **0**.
- Chunks à normalisation vide exclus de ce hash : 0.
- Variantes normalisées à examiner : `reports/dedup_audit/chunks_normalized_format_variants.csv`.
- Documents écartés de l'audit LSH (trop courts) : 0.
- Chunks écartés de l'audit LSH (trop courts) : 72.
- Écran LSH : activé, probabiliste.
- Paires de documents candidates LSH : **184**.
- Paires de chunks candidates LSH : **2263**.
- Paires de documents Jaccard >= 0.80 parmi les candidates : **0**.
- Paires de chunks Jaccard >= 0.80 parmi les candidates : **1691**.
- Paires de chunks Jaccard >= 0.90 parmi les candidates : **1082**.
- Paires de chunks cross-patient >= 0.80 parmi les candidates : **1127**.
- Portée de la consolidation expérimentale : **same-document**.
- Chunks dans la copie : **1173**.
- Occurrences fusionnées dans la copie uniquement : **0**.
- Groupes fusionnés : **0**, dont **0** multi-documents.
- Chaque chunk conservé porte `source_references` (toutes les occurrences, avec `document`, `chunk_id`, `date`, `patient_ipp`, `title`, etc.), `source_documents`, `source_chunk_ids` et `duplicate_count`.
- Copie distincte : `data/chunks/chunks_dedup_preview.jsonl`.
- Audit des regroupements : `reports/dedup_audit/preview_merged_groups.csv`.
- Contrôle obligatoire : `python scripts/validate_dedup_preview.py`.

## Vérifications supplémentaires du cours 07

- Hash normalisé : détecte des variantes textuelles ; aucune suppression automatique.
- Le formateur illustre les bigrammes (`--k 2`) et un seuil LSH de 0.2 sur quatre petits textes ; les réglages par défaut de cet audit de corpus sont des trigrammes et un seuil de 0.65 pour limiter le volume de candidats.
- MMR agit à la recherche (dense + sparse → RRF → MMR), et non sur le corpus avant Qdrant. Prévoir une expérience séparée après cet audit.
- Les résultats Jaccard affichés sont EXACTS pour les paires proposées par LSH, mais LSH ne garantit pas de retrouver toutes les paires.


## Documents les plus similaires

| ID A | ID B | Jaccard | Patients différents ? |
|---|---|---:|---|
| 4100006_2025-10-28_sortie.docx | 4100036_2025-08-20_sortie.docx | 0.775 | Oui |
| 4100004_2025-12-07_sortie.docx | 4100044_2025-06-16_sortie.docx | 0.771 | Oui |
| 4100024_2025-04-29_sortie.docx | 4100034_2025-06-03_sortie.docx | 0.763 | Oui |
| 4100026_2026-04-06_sortie.docx | 4100046_2026-05-22_sortie.docx | 0.757 | Oui |
| 4100009_2025-10-12_sortie.docx | 4100049_2025-04-22_sortie.docx | 0.750 | Oui |
| 4100006_2025-10-28_sortie.docx | 4100056_2025-04-02_sortie.docx | 0.749 | Oui |
| 4100005_2025-06-14_sortie.docx | 4100045_2025-03-18_sortie.docx | 0.748 | Oui |
| 4100004_2025-12-07_sortie.docx | 4100014_2025-02-24_sortie.docx | 0.747 | Oui |
| 4100014_2025-02-24_sortie.docx | 4100044_2025-06-16_sortie.docx | 0.747 | Oui |
| 4100005_2025-06-14_sortie.docx | 4100025_2025-07-18_sortie.docx | 0.740 | Oui |
| 4100025_2025-07-18_sortie.docx | 4100045_2025-03-18_sortie.docx | 0.740 | Oui |
| 4100009_2025-10-12_sortie.docx | 4100039_2025-07-16_sortie.docx | 0.739 | Oui |

## Chunks les plus similaires

| ID A | ID B | Jaccard | Patients différents ? |
|---|---|---:|---|
| 4100001_2025-06-30_bilan.docx::2 | 4100011_2025-02-23_bilan.docx::2 | 1.000 | Oui |
| 4100001_2025-06-30_bilan.docx::2 | 4100021_2025-04-11_bilan.docx::2 | 1.000 | Oui |
| 4100001_2025-06-30_bilan.docx::2 | 4100031_2025-09-01_bilan.docx::2 | 1.000 | Oui |
| 4100001_2025-06-30_bilan.docx::2 | 4100041_2025-01-08_bilan.docx::2 | 1.000 | Oui |
| 4100001_2025-06-30_bilan.docx::2 | 4100051_2025-12-23_bilan.docx::2 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::2 | 4100021_2025-04-18_consultation.docx::2 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100002_2025-04-13_consultation.docx::3 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100006_2025-07-03_consultation.docx::2 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100009_2025-08-20_consultation.docx::2 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100010_2025-10-31_consultation.docx::2 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100011_2025-03-02_consultation.docx::3 | 1.000 | Oui |
| 4100001_2025-07-07_consultation.docx::3 | 4100012_2025-11-24_consultation.docx::3 | 1.000 | Oui |

## Décision avant déduplication

1. Examiner les paires à haut Jaccard : identité de patient, dates, médicaments, chiffres, négations.
2. Jamais de fusion inter-patients ; fusion inter-documents uniquement en mode same-patient explicite, avec IPP connu ET texte brut identique.
3. Chaque chunk consolidé conserve toutes les références sources et dates; adapter l'évaluateur au champ source_references avant une comparaison A/B.
4. Si une déduplication est retenue : créer une NOUVELLE collection Qdrant, pas modifier la baseline.
5. Comparer la nouvelle indexation aux métriques E11 (Hit@5, Fact Recall@5, nDCG@5).
