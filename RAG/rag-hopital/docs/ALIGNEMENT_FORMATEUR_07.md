# Alignement avec le cours du formateur — `07_indexation_avancee.ipynb`

| Cours (cellules) | Fonction du cours | RAG Hôpital audit v3 | Décision |
|---|---|---|---|
| 0–4 | Normalisation du texte (minuscules, accents, ponctuation) | `normalize()` + `chunks_normalized_sha256.csv` | **Audit seul**, pas fusion sur texte normalisé |
| 5–6 | Shingles bigrammes et Jaccard exact | `shingles()` et `jaccard()` | Par défaut trigrammes pour analyse de corpus; `--k 2` pour reproduire le cours |
| 8–10 | MinHash 128 permutations + MinHashLSH; score approché des candidats | `approximate_pairs()` + Jaccard **exact** sur chaque candidat | LSH = recherche probabiliste de paires, jamais critère de suppression |
| 11–13 | MMR pour diversifier les résultats de recherche | **Pas intégré dans l'audit** | Expérience ultérieure autonome: dense + sparse → RRF → MMR |

## Réglages et précautions

- Démonstration cours : bigrammes (n=2), seuil LSH 0.2 sur quatre textes, 128 permutations.
- Audit corpus Hôpital : trigrammes (k=3), seuil LSH 0.65, 128 permutations, limite de longueur minimale 8 shingles. Ces valeurs sont paramétrables, donc **approche alignée**, mais pas paramètres identiques par défaut.
- Les scores indiqués par `chunks_similar_lsh_candidates.csv` sont le Jaccard **exact** (intersection / union) sur les shingles, non l'estimation `MinHash.jaccard`.
- Le texte peut changer après normalisation sans être **médicalement équivalent**. Exemple : les chaînes `Dose 2.5 mg` et `Dose 2 5 mg` peuvent se normaliser à la même représentation. Elles ne sont **jamais fusionnées** dans le mode de consolidation.
- LSH ne garantit pas la découverte de toutes les paires. Des passages courts (moins de 8 shingles) ne sont pas comparés par défaut.
- Les 280 documents du cours sont le contexte de l'exercice, pas un nombre vérifié par ce package : le rapport affiche le total réellement trouvé dans le corpus local.
- Le notebook du professeur illustre aussi la différence entre déduplication et MMR. L'audit ne modifie **pas** le retrieval, et ne préjuge pas de l'effet sur Hit@5, Recall@5 ou nDCG@5.
- Les paramètres Qdrant du professeur (collection `Veltis`, port 6333, embeddings externes) ne correspondent pas au RAG Hôpital local (par défaut port 16333, collection `hopital_bge_m3_512`, collection hybride séparée). **Ne pas transférer directement le code de connexion**.
- Correction à connaître : dans une explication markdown du professeur les symboles `&` et `|` sont intervertis ; son **code** Jaccard est correct : `len(u & v) / len(u | v)`. Le nombre de paires non ordonnées est `n(n-1)/2`, et non `n(n-1)`.

## Étape opérationnelle

```bash
cd ~/formation/RAG/rag-hopital
source .venv/bin/activate
python -c "import datasketch, unidecode; print('OK')"
python -m unittest discover -s tests -p 'test_dedup*.py' -v
python scripts/audit_duplicates.py --emit-safe-copy
python scripts/validate_dedup_preview.py
sed -n '1,100p' reports/dedup_audit/SYNTHESE.md
```

Ne pas lancer d'indexation de la copie avant décision sur les règles et création d'une **nouvelle collection**.
