# E14 — Évaluation LLM-as-Judge

## Configuration
- Réponses évaluées : baseline E12, expérience PostgreSQL ID 12
- Générateur : Qwen 3.5 9B
- Juge : Granite 4.1 8B
- Échantillon : 26 questions, 13 catégories
- Méthode : comparaison à la réponse de référence

## Résultats
- Exactitude moyenne : 92.3 %
- Complétude moyenne : 80.8 %
- Réponses jugées exactes : 24/26
- Réponses jugées complètes : 18/26
- Réponses incorrectes : 2/26

## Limites
- L'échantillon exclut les questions hors corpus, évaluées séparément.
- Le juge compare les réponses aux références.
- La fidélité aux passages et la validité des citations ne sont pas vérifiées.
- Les appréciations du juge nécessitent une validation humaine.
