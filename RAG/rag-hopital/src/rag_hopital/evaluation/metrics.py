def judge_chunk(question: dict, document: str, text: str) -> list:
    """Find reference evidence matching a retrieved chunk."""

    matches = []
    normalized_text = text.casefold()

    for evidence in question["evidence"]:

        if evidence["document"] != document:
            continue

        if all(
            snippet.casefold() in normalized_text
            for snippet in evidence["snippets"]
        ):
            matches.append(evidence)

    return matches
# ============================================================
# [E09.2 — SECTION 2] CALCUL DU nDCG
# ============================================================

# log2 calcule le logarithme en base 2.
# Il permet de réduire le poids des résultats mal classés.
from math import log2


def ndcg_at_k(
    retrieved_grades: list[int],
    ideal_grades: list[int],
    k: int = 5,
) -> float:
    """
    Calcule le nDCG pour les k premiers résultats.

    retrieved_grades :
        Grades dans l'ordre réel de Qdrant.

    ideal_grades :
        Grades dans le meilleur ordre possible.

    k :
        Nombre de résultats à évaluer.
    """

    # DCG : qualité du classement réellement obtenu.
    dcg = 0.0

    # enumerate() donne le rang et le grade de chaque résultat.
    # start=1 signifie que les rangs commencent à 1.
    for rank, grade in enumerate(retrieved_grades[:k], start=1):

        # Ajouter le gain du résultat en tenant compte de son rang.
        dcg += grade / log2(rank + 1)

    # Trier les grades attendus du plus élevé au plus faible.
    sorted_grades = sorted(ideal_grades, reverse=True)[:k]

    # IDCG : qualité maximale théorique du classement.
    idcg = 0.0

    for rank, grade in enumerate(sorted_grades, start=1):
        idcg += grade / log2(rank + 1)

    # Éviter une division par zéro.
    if idcg == 0:
        return 0.0

    # Normaliser le résultat.
    # Un classement idéal obtient 1.0.
    return dcg / idcg

# ============================================================
# [E09.3 — SECTION 3] IDENTIFIER LES FAITS NÉCESSAIRES
# ============================================================

def required_facts(question: dict) -> set:
    """
    Identifier les faits nécessaires pour répondre à une question.

    Paramètre :
        question : dictionnaire issu du golden dataset.

    Retour :
        Ensemble des identifiants des faits nécessaires.

    Exemple :
        Q001 -> {0}

        Une question multi-hop pourrait retourner {0, 1}.
    """

    # Un ensemble (set) ne contient pas de doublons.
    #
    # Deux documents différents peuvent apporter le même fait.
    # Nous ne devons donc pas compter ce fait deux fois.
    facts = set()

    # Examiner chaque preuve fournie par le formateur.
    for evidence in question["evidence"]:

        # Conserver uniquement les preuves nécessaires.
        #
        # grade == 2 : preuve contenant un fait requis.
        # fact is not None : identifiant du fait disponible.
        if evidence["grade"] == 2 and evidence["fact"] is not None:

            # Ajouter l'identifiant du fait à notre ensemble.
            facts.add(evidence["fact"])

    # Renvoyer les identifiants des faits nécessaires.
    return facts
# ============================================================
# [E09.4 — SECTION 4] COUVERTURE DES FAITS NÉCESSAIRES
# ============================================================

def evaluate_fact_coverage(
    question: dict,
    ranked_matches: list[list[dict]],
    k: int = 5,
) -> dict:
    """
    Vérifier si les chunks récupérés couvrent tous les faits
    nécessaires pour répondre à une question.

    ENTRÉES
    -------
    question :
        Question du golden dataset, avec ses preuves.

    ranked_matches :
        Liste des preuves reconnues pour chaque chunk,
        dans l'ordre du classement Qdrant.

    k :
        Nombre maximal de chunks à évaluer.

    SORTIE
    ------
    Dictionnaire contenant :
        required_facts       : faits nécessaires ;
        found_facts          : faits retrouvés ;
        fact_recall          : proportion des faits retrouvés ;
        first_complete_rank  : premier rang où tous les faits
                               sont disponibles.
    """

    # [E09.4-A1] Identifier tous les faits nécessaires.
    #
    # La fonction required_facts() existe déjà.
    # Elle lit les champs "grade" et "fact" du golden dataset.
    needed = required_facts(question)

    # [E09.4-A2] Créer un ensemble vide.
    #
    # Il contiendra les faits effectivement retrouvés.
    found = set()

    # Au départ, la réponse complète n'a pas été trouvée.
    first_complete_rank = None

    # [E09.4-A3] Examiner les chunks dans l'ordre de Qdrant.
    #
    # enumerate() ajoute un numéro de rang à chaque élément.
    # start=1 signifie que le premier chunk a le rang 1.
    for rank, matches in enumerate(ranked_matches[:k], start=1):

        # Un chunk peut correspondre à plusieurs preuves.
        for evidence in matches:

            # Seules les preuves de grade 2 apportent
            # un fait nécessaire.
            #
            # Nous vérifions aussi que "fact" n'est pas None.
            # Attention : fact=0 est un identifiant valide.
            if (
                evidence["grade"] == 2
                and evidence["fact"] is not None
            ):

                # Ajouter ce fait à l'ensemble des faits trouvés.
                #
                # Un set évite de compter deux fois
                # le même fait présent dans plusieurs documents.
                found.add(evidence["fact"])

        # [E09.4-A4] Vérifier si tous les faits sont disponibles.
        #
        # issubset() signifie :
        # Tous les éléments de "needed" sont-ils dans "found" ?
        #
        # Nous gardons uniquement le PREMIER rang complet.
        if (
            needed
            and needed.issubset(found)
            and first_complete_rank is None
        ):
            first_complete_rank = rank

    # [E09.4-A5] Calculer la proportion des faits retrouvés.
    #
    # Exemple :
    # 2 faits nécessaires, 1 fait trouvé -> recall = 0.5.
    #
    # Si aucun fait n'est défini, le recall vaut 0.
    # Les questions out_of_corpus seront évaluées séparément.
    fact_recall = (
        len(needed.intersection(found)) / len(needed)
        if needed
        else 0.0
    )

    # [E09.4-A6] Retourner les résultats.
    return {
        "required_facts": needed,
        "found_facts": found,
        "fact_recall": fact_recall,
        "first_complete_rank": first_complete_rank,
    }