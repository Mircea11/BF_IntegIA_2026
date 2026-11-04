# E12 — Rapport d'audit du baseline (expérience 12)

**Source :** `E12_baseline_106_answers.csv`, export PostgreSQL. 106 questions et 106 réponses ; chaque réponse dispose de cinq métadonnées de passages. Audit du 4 novembre 2026.

## Méthode

Comparaison **manuelle** de la réponse générée à la réponse attendue du jeu de test. Les catégories sont : **conforme** (répond à la question principale, même si certains détails de la référence non demandés sont omis), **partielle** (éléments demandés manquants), **non conforme** (erreur, omission centrale, ou refus injustifié) et **à vérifier** (information additionnelle ou formulation ambiguë nécessitant la lecture de documents). Ce n'est **ni une évaluation automatique certifiée, ni une preuve de fidélité aux sources** : le CSV ne contient pas le texte intégral des cinq passages.

## Résultats

| Indicateur | Résultat |
|---|---:|
| Expérience et statut | 12, `done` (confirmé dans PostgreSQL lors de la session) |
| Questions / réponses sauvegardées | 106 / 106 |
| Questions répondables / hors corpus | 100 / 6 |
| Conformes à la question principale | **86/106 (81,1 %)** |
| Partielles | **4/106 (3,8 %)** |
| Non conformes | **14/106 (13,2 %)** |
| À vérifier sur documents sources | **2/106 (1,9 %)** |
| Refus corrects hors corpus | **5/6 (83,3 %)** |
| Refus injustifiés, y compris refus rédigés librement | **8/100 (8 %)** |
| Réponses avec au moins une référence [n] | **96/106 (90,6 %)** |
| Références [n] pointant vers un rang 1–5 valide | **Toutes les références présentes** |
| Latence moyenne (PostgreSQL) | 15,93 s |

Les refus exacts normalisés sont au nombre de 8 : cinq corrects hors corpus et trois injustifiés. **Cinq autres réponses répondables** refusent ou déclarent l'information indisponible sans respecter la formulation exacte : **Q011, Q012, Q013, Q071, Q072**. Le nombre d'abstentions injustifiées atteint donc **8**, et non 3.

## Échecs avérés par comparaison à la référence (14)

- **Q011** : Réponse numérique attendue 1408 pg/mL absente ; refus malgré une référence explicite.
- **Q012** : Ne fournit aucun effet indésirable attendu de l'amoxicilline–acide clavulanique ; déclare l'information indisponible.
- **Q013** : Ne relève pas l'hyperkaliémie à 6,0 mmol/L ni la contre-indication et l'alternative attendues.
- **Q017** : Décrit le scanner préopératoire au lieu de l'aspect observé pendant l'opération ; péritonite localisée absente.
- **Q045** : Infère indûment l'absence de metformine, alors que sa dose n'est pas documentée.
- **Q050** : Omet M. Pierre Perrin et affirme à tort que son stade n'est pas spécifié.
- **Q058** : Ajoute la spironolactone à la liste ; ce médicament n'est pas dans la réponse de référence.
- **Q063** : Refus ; l'insuffisance mitrale existe dans le chunk 2 du document d'imagerie mais pas dans les cinq chunks sélectionnés.
- **Q071** : Refuse alors que les cinq effets indésirables de la prednisone figurent dans la référence.
- **Q072** : Refuse la conduite à tenir avec la metformine avant/après le produit de contraste.
- **Q078** : Refus ; manque la réduction/espacement des prises de morphine et les risques liés à l'IRC.
- **Q083** : Décrit les constatations du scanner plutôt que l'aspect peropératoire ; péritonite localisée absente.
- **Q089** : Refus ; manque la contre-indication IEC et le délai de 36 h.
- **Q090** : Indique d'autres effets du tramadol, mais omet nausées et vertiges demandés par la référence.

## Réponses partielles (4)

- **Q020** : Identifie les cinq médicaments mais omet la distinction contre-indication/adaptation et les doses attendues.
- **Q037** : Omet la natrémie ; cite uniquement kaliémie et créatinine.
- **Q064** : Omet la lévofloxacine ; ajoute la gentamicine en association avec la clindamycine.
- **Q092** : Omet le ramipril (veille de l'anesthésie générale) parmi les médicaments à suspendre.

## À vérifier sur les documents sources (2)

- **Q066** : Ajoute sacubitril/valsartan aux contre-indications de l'hyperkaliémie : vérifier la fiche médicament et la distinction contre-indication/précaution.
- **Q093** : Dose actuelle 40 mg correcte, mais formule contradictoire : ordonnance à 60 mg décrite comme confirmant 40 mg. Vérifier dates et citations.

## Erreurs et diagnostic du pipeline

- **Q045 : refus nécessaire manqué**. Une ordonnance listant d'autres médicaments n'établit pas l'absence de metformine. Piste : renforcer l'interdiction d'inférence à partir du silence documentaire (règle 11, expérience distincte).
- **Q063 : retrieval (vérifié avec Qdrant)**. Le document d'imagerie pertinent existe, mais le chunk retenu était l'en-tête ; la phrase « insuffisance mitrale modérée » est dans son chunk 2, non transmis à Qwen.
- **Q017 / Q083 : mauvaise source ou raisonnement inter-documentaire**. Les réponses utilisent les résultats de scanner pour une question portant sur les constatations opératoires.
- **Q050 / Q064 / Q092 : défaut d'exhaustivité** dans les questions de liste.
- **Q012 / Q013 / Q071 / Q072 / Q078 / Q089 :** recherche et génération restent à départager par lecture des passages effectivement transmis.

## Recommandations de prochaine action

1. Conserver l'expérience 12 et le prompt baseline sans changement.
2. Réaliser l'évaluation documentaire ciblée des 14 non conformes et de 2 cas à vérifier ; ne pas confondre absence de preuve dans le top 5 et absence dans le corpus.
3. Calculer les métriques de recherche E12 pour les 100 questions répondables, car deux classements diffèrent de l'expérience E11.
4. Seulement ensuite comparer une variante de prompt (règle 11) sur des questions fixes, sans modifier le baseline.

**Limites :** l'exactitude relative aux réponses attendues ne garantit pas la correction clinique ; les citations sont valides structurellement, mais leur support factuel n'a pas été testé. Les textes du jeu de données sont fictifs et ne sont pas des recommandations médicales.
