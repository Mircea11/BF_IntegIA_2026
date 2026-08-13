# Exercice 3
# Créer une classe « Epargne » permettant la gestion d’un carnet d’épargne qui devra implémenter :

# Les propriétés publiques :
# Numéro (string)
# Solde (float) - Lecture seule
# DateDernierRetrait (DateTime) - représentant la date du dernier retrait sur le carnet
# Titulaire (Personne)
# Les méthodes publiques :
# void Retrait(float Montant)
# void Depot(float Montant)
# Ajouter à la classe « Courant »:

# La propriété publique :

# Ligne de crédit - représentant la limite négative du compte strictement supérieur ou égale à 0
# Et modifier les méthodes pour intégrer cette nouvelle limite négative du solde

# Créer une classe « Compte » avec tous les éléments communs à « Courant » et « Épargne »

# Si nous ajoutions la « ligne_de_credit » dans « Compte », définir sur papier les modifications qu’il faudrait apporter à nos classes.
from personne import Personne
from compte import Compte
from compte_courant import Courant
#from datetime import datetime

class Epargne (Compte):
    def __init__(self, numero: str, titulaire: Personne, solde: float = 0.0,):
             # variables inherited from CompteCourant
             super().__init__(numero, titulaire, solde )
             #self.DateDernierRetrait = None
    # def Depot(self,somme: float) -> None: is inherited
 
    def retrait(self, montant: float) -> None:
            if self.solde < montant:
                print("Solde insuffisant")
            else:
                super().retrait(montant)

    def __str__(self):
          return f"Le compte épargne {self.numero} posédé par {self.titulaire.prenom} avec { self.solde} eur"



    
if __name__ == "__main__":

    john_doe = Personne(1, "Doe", "John")

    epargne = Epargne("EP01", john_doe, 1000)

    print(epargne)

    #epargne.afficher_compte()

    epargne.depot(200)
  
    epargne.retrait(100)

    #epargne.afficher_compte()
    print(epargne)
    print(epargne + 50)
    #print(f"Date dernier retrait : {epargne.DateDernierRetrait}")

    epargne = Epargne("EP01", john_doe, 1000)
    


    print("_" * 50)
    epargne.depot(200)
    epargne.retrait(150)
    #epargne.Courant.afficher_compte()
    print(epargne)
    print("_" * 50)
    epargne.retrait(300)
    #epargne.afficher_compte()
    print(epargne)
