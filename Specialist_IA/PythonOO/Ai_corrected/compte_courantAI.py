from personne import Personne
from compte import Compte


class Courant(Compte):
    def __init__(self, numero: str, titulaire: Personne, ligne_de_credit: float = 0.0, solde: float = 0.0):
        super().__init__(numero, titulaire, solde)
        self.__ligne_de_credit = 0.0
        self.ligne_de_credit = ligne_de_credit

    @property
    def ligne_de_credit(self) -> float:
        return self.__ligne_de_credit

    @ligne_de_credit.setter
    def ligne_de_credit(self, valeur: float) -> None:
        if valeur < 0:
            raise ValueError("La ligne de crédit ne peut pas être négative")
        self.__ligne_de_credit = float(valeur)

    @property
    def solde_disponible(self) -> float:
        return self.solde + self.ligne_de_credit

    def CalculInteret(self) -> float:
        if self.solde >= 0:
            return self.solde * 0.03
        return self.solde * 0.0975

    def __str__(self):
        return (
            f"Compte courant {self.numero} | Titulaire : {self.titulaire} | "
            f"Solde : {self.solde} EUR | Ligne de crédit : {self.ligne_de_credit} EUR"
        )

    def afficher_compte(self):
        print(f"Compte numéro : {self.numero}")
        print(f"Titulaire : {self.titulaire.prenom} {self.titulaire.nom}")
        print(f"Solde : {self.solde}")
        print(f"Ligne de crédit : {self.ligne_de_credit}")
