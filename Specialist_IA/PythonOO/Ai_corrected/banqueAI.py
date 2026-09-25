from personne import Personne
from compte import Compte


class Banque:
    def __init__(self, nom: str, comptes=None):
        self.nom = nom
        self.comptes = comptes if comptes is not None else dict()

    def ajouter_compte(self, compte: Compte) -> None:
        if not isinstance(compte, Compte):
            print("Ce n'est pas un compte valide.")
            return
        self.comptes[compte.numero] = compte

    def retirer_compte(self, compte: Compte) -> None:
        self.comptes.pop(compte.numero)

    def avoir_des_comptes(self, titulaire: Personne) -> float:
        total = 0.0

        for compte in self.comptes.values():
            if compte.titulaire.id == titulaire.id:
                total = compte + total

        return total

    # alias matching the exercise wording
    def AvoirDesComptes(self, titulaire: Personne) -> float:
        return self.avoir_des_comptes(titulaire)
