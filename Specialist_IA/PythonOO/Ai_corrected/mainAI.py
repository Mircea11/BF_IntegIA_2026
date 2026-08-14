from personne import Personne
from compte_courant import Courant
from compte_epargne import Epargne
from banque import Banque
from solde_insuffisant_exception import SoldeInsuffisantException


def tester_action(description, action):
    print("_" * 50)
    print(description)
    try:
        resultat = action()
        if resultat is not None:
            print(resultat)
    except ValueError as error:
        print(f"ValueError : {error}")
    except SoldeInsuffisantException as error:
        print(f"SoldeInsuffisantException : {error}")


if __name__ == "__main__":
    john = Personne(1, "Doe", "John")
    anna = Personne(2, "Smith", "Anna")

    courant = Courant("BE01", john, ligne_de_credit=100, solde=500)
    epargne = Epargne("EP01", john, solde=1000)
    courant_negatif = Courant("BE02", john, ligne_de_credit=500, solde=-200)
    compte_anna = Courant("BE03", anna, ligne_de_credit=100, solde=300)

    tester_action("Création Personne", lambda: john)
    tester_action("Création compte courant", lambda: courant)
    tester_action("Création compte épargne", lambda: epargne)

    tester_action("Dépôt valide sur courant: +50", lambda: courant.depot(50))
    print(courant)

    tester_action("Dépôt invalide sur courant: -20", lambda: courant.depot(-20))

    tester_action("Retrait valide courant: -600, autorisé grâce à ligne de crédit", lambda: courant.retrait(600))
    print(courant)

    tester_action("Retrait refusé courant: dépasse ligne de crédit", lambda: courant.retrait(100))

    tester_action("Retrait valide épargne: -100", lambda: epargne.retrait(100))
    print(epargne)

    tester_action("Retrait refusé épargne: solde insuffisant", lambda: epargne.retrait(5000))

    tester_action("Intérêt courant positif/négatif", lambda: (courant.CalculInteret(), courant_negatif.CalculInteret()))
    tester_action("Intérêt épargne", lambda: epargne.CalculInteret())

    tester_action("Appliquer intérêt épargne", lambda: epargne.AppliquerInteret())
    print(epargne)

    tester_action("Opérateur + avec nombre", lambda: courant + 50)
    tester_action("Opérateur + entre comptes", lambda: courant + courant_negatif)

    banque = Banque("NeoBanque")
    banque.ajouter_compte(courant)
    banque.ajouter_compte(epargne)
    banque.ajouter_compte(courant_negatif)
    banque.ajouter_compte(compte_anna)
    banque.ajouter_compte("pas un compte")

    tester_action("Avoirs de John dans la banque", lambda: banque.avoir_des_comptes(john))
    tester_action("Avoirs de Anna dans la banque", lambda: banque.AvoirDesComptes(anna))
