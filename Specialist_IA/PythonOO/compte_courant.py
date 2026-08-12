from personne import Personne

class   CompteCourant:
    def __init__(self, numero: str, titulaire: Personne, solde = 0):
         self.numero = numero
         self.titulaire = titulaire
         self.solde = solde
if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")
    courant = CompteCourant("BE01", john_doe, 100)
    print("_"*50)
    print(f"Le compte corant {courant.numero} pocédé par { courant.titulaire.prenom} { courant.titulaire.nom} ")
# Ajoutez, un constructeur prenant en paramètre : 
# 	- Le numéro, le titulaire ,le solde
    # def __init__(self, numero, titulaire, solde):
    #     self.numero = numero
    #     self.titulaire = titulaire
    #     self.solde = solde
#Comportement:
    def Depot(self,somme: float) -> None:
        if somme <=0:
            print("Somme doive pas etre negative")
        else:
            self.solde += somme

    def Retrait(self, somme: float) -> None:
        if somme <=0:
            print("Somme doive pas etre negative")
        elif self.solde <somme:
            print("Solde insuffisant")
        else:
            self.solde -= somme
        return self.solde

    def afficher_compte(self):
        print(f"Compte numéro : {self.numero}")
        print(f"Titulaire : {self.titulaire.prenom} {self.titulaire.nom}")
        print(f"Solde : {self.solde}")
    
    