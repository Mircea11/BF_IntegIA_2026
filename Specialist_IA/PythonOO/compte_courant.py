from solde_insuffisant_exception import SoldeInsuffisantException

from personne import Personne
from compte import Compte

class Courant(Compte):
    def __init__(self, numero: str, titulaire: Personne, ligne_de_credit: float, solde:float = 0):
        super().__init__(numero, titulaire, solde)
        self.__ligne_de_credit = 0
        try:
            self.ligne_de_credit = ligne_de_credit
        except ValueError as error:
            print(error)

    #getter        
    @property
    def ligne_de_credit(self):
        return self.__ligne_de_credit

    #setter
    @ligne_de_credit.setter
    def ligne_de_credit(self, valeur):
        if valeur < 0:
            raise ValueError("La ligne de crdit ne peut pas etre negative")
        


    def retrait(self, montant: float) -> None:
        if montant < 0:
            raise ValueError
        pass
        if self.solde - montant < - self.ligne_de_credit:
             raise SoldeInsuffisantException(self.solde)
        else: super().retrait(montant)

    def __str__(self):
        return f"Le compte courant {self.numero} posédé par {self.titulaire.prenom} avec {self.solde} EUR"

    def afficher_compte(self):
         print(f"Compte numéro : {self.numero}")
         print(f"Titulaire : {self.titulaire.prenom} {self.titulaire.nom}")
         print(f"Solde : {self.solde}")
         print(f"Ligne de crédit : {self.ligne_de_credit}")

if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")
    courant = Courant("BE01", john_doe, 100)
    print("_"*50)
    print(f"Le compte corant {courant.numero} pocédé par { courant.titulaire.prenom} { courant.titulaire.nom} ")  
    # courant.Retrait (25)
    # print(courant)
    # print(epagne)

    print("_"*50)
    john = Personne(1, "Doe", "John")

    courant = Courant("BE01", john, 100, 500)
    print("_" * 50)
    courant.retrait(300)
    courant.afficher_compte()
    print(courant)
    courant.retrait(152)
    courant.retrait(100)
    courant.retrait(152)

