from de import De

def generer_caracteristique():
    d6 = De(1,6)

    jets = []

    for i in range(4):
        jets.append(d6.lance())

    jets_tries = sorted(jets, reverse = True)
    meilleurs_jets = jets_tries[:3]

    total = sum(meilleurs_jets)

    return total

def modificateur(valeur: int) -> int:
    if valeur < 5:
        return -1
    elif valeur < 10:
        return 0
    elif valeur < 15:
        return 1
    else:
        return 2