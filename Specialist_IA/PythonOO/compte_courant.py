from personne import Personne

class   CompteCourant:
    def __init__(self, numero: str, titulaire: Personne, solde = 0, ligne_credit: float = 0.0):
         self.numero = numero
         self.titulaire = titulaire
         self.solde = solde
         self.ligne_credit = ligne_credit
    @property
    def ligne_credit(self):
        return self.__ligne_credit

    @ligne_credit.setter
    def ligne_credit(self, valeur):
        if valeur < 0:
            print("La ligne de crédit doit etre superioe ou egale a 0.")
            self.__ligne_credit = 0.0
        else:
            self.__ligne_credit = valeur

    def Depot(self,somme: float) -> None:
        if somme <=0:
            print("Somme doive pas etre negative")
        else:
            self.solde += somme
        # def accelerer(self, est_sur_eau, acceleration=50):
        # if est_sur_eau:
        #     Bateau.accelerer(self,self.acceleration)
        #                 #Methode d'aceleration du bateau
        # else: 
        #     Voiture.accelerer(self,self.acceleration)
        #     return super().accelerer(acceleration)
        # def __str__(self):
        #  return Voiture.__str__(self)
    

    def Retrait(self, somme: float) -> None:
        
        if somme <=0:
            print("Somme doive pas etre negative")
        elif self.solde - somme < -self.ligne_credit:
            print("Retrait refusé : limite de crédit dépassée.")
        else:
            self.solde -= somme
        #return self.solde

    def afficher_compte(self):
        print(f"Compte numéro : {self.numero}")
        print(f"Titulaire : {self.titulaire.prenom} {self.titulaire.nom}")
        print(f"Solde : {self.solde}")
        print(f"Ligne de crédit : {self.ligne_credit}")


if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")
    courant = CompteCourant("BE01", john_doe, 100)
    print("_"*50)
    print(f"Le compte corant {courant.numero} pocédé par { courant.titulaire.prenom} { courant.titulaire.nom} ")  
    # courant.Retrait (25)
    # print(courant)
    # print(epagne)

    print("_"*50)
    john = Personne(1, "Doe", "John")

    courant = CompteCourant("BE01", john, 100, 500)
    print("_" * 50)
    courant.Retrait(300)
    courant.afficher_compte()
    