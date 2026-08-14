from personne import Personne
from compte_courant import Courant
from compte_epargne import Epargne
from solde_insuffisant_exception import SoldeInsuffisantException


# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

# courant.retrait(25)
# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

# courant.depot(50)
# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

john_doe = Personne(1, "Doe", "John")
courant = Courant("BE01", john_doe, -100)
print(courant)

try: 
    courant.retrait(50)
except ValueError as error:
    print(error)
except SoldeInsuffisantException as exception:
    print(exception)


#epargne = Epargne("BE01", john_doe, 100)
try: 
    epargne = Epargne("EP01", john_doe, 100)
    epargne.retrait(50)
    print(epargne.date_dernier_retrait)
except ValueError as error:
    print(error)
except SoldeInsuffisantException as exception:
    print(exception)
print(epargne)

#python -c "import sys; print(sys.executable); print(sys.version)"

from personne import Personne
from compte_courant import Courant
from compte_epargne import Epargne
from solde_insuffisant_exception import SoldeInsuffisantException


def tester_retrait(compte, montant):
    try:
        print(f"\nRetrait de {montant} EUR sur {compte.numero}")
        compte.retrait(montant)
        print("Retrait accepté")
        print(compte)
    except ValueError as error:
        print(f"Erreur ValueError : {error}")
    except SoldeInsuffisantException as exception:
        print(f"Erreur SoldeInsuffisantException : {exception}")


def tester_depot(compte, montant):
    try:
        print(f"\nDépôt de {montant} EUR sur {compte.numero}")
        compte.depot(montant)
        print("Dépôt accepté")
        print(compte)
    except ValueError as error:
        print(f"Erreur ValueError : {error}")

print("-"*50)
print("-"*50)
print("-"*50)
print("-"*50)
if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")

    print("_" * 50)
    print("TEST 1 — Création d'un compte courant")

    # Courant(numero, titulaire, ligne_de_credit, solde)
    courant = Courant("BE01", john_doe, 100, 500)
    print(courant)
    courant.afficher_compte()

    print("_" * 50)
    print("TEST 2 — Dépôt sur compte courant")

    tester_depot(courant, 50)
    tester_depot(courant, -20)

    print("_" * 50)
    print("TEST 3 — Retraits sur compte courant")

    tester_retrait(courant, 300)   # accepté
    tester_retrait(courant, 200)   # accepté si limite de crédit respectée
    tester_retrait(courant, 200)   # devrait être refusé si dépasse ligne de crédit
    tester_retrait(courant, -10)   # ValueError

    print("_" * 50)
    print("TEST 4 — Intérêts compte courant")

    try:
        print(f"Intérêt courant : {courant.CalculInteret()}")
    except AttributeError:
        print("Méthode CalculInteret introuvable. Vérifie le nom exact dans Courant et Compte.")

    print("_" * 50)
    print("TEST 5 — Création d'un compte épargne")

    epargne = Epargne("EP01", john_doe, 1000)
    print(epargne)
    print(f"Date dernier retrait : {epargne.date_dernier_retrait}")

    print("_" * 50)
    print("TEST 6 — Dépôt sur épargne")

    tester_depot(epargne, 200)
    tester_depot(epargne, -50)

    print("_" * 50)
    print("TEST 7 — Retraits sur épargne")

    tester_retrait(epargne, 100)
    print(f"Date dernier retrait : {epargne.date_dernier_retrait}")

    tester_retrait(epargne, 5000)
    tester_retrait(epargne, -10)

    print("_" * 50)
    print("TEST 8 — Intérêts épargne")

    try:
        print(f"Intérêt épargne : {epargne.CalculInteret()}")
    except AttributeError:
        print("Méthode CalculInteret introuvable. Vérifie le nom exact dans Epargne et Compte.")

    print("_" * 50)
    print("TEST 9 — Opérateur +")

    courant2 = Courant("BE02", john_doe, 100, -200)

    print(f"courant + 50 = {courant + 50}")
    print(f"courant2 + 50 = {courant2 + 50}")
    print(f"courant + courant2 = {courant + courant2.solde}")

    print("_" * 50)
    print("FIN DES TESTS")