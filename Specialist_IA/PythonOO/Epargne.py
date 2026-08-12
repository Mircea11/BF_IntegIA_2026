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
from compte_courant import CompteCourant
from datetime import datetime

class Epargne (CompteCourant):
    def __init__(self, numero: str, titulaire: Personne,  DateDernierRetrait, solde = 0.0,):
             # variables inherited from CompteCourant
             super().__init__(numero, titulaire, solde, ligne_credit=0.0)
             self.DateDernierRetrait = None
    # def Depot(self,somme: float) -> None: is inherited
 
    def Retrait(self, somme: float) -> None:
            if somme <=0:
                print("Somme doive pas etre negative")
            elif self.solde <somme+100:
                print("Somme doive pas depacais 100")
            else:
                self.solde -= somme
                self.DateDernierRetrait = datetime.now()
            return self.solde



    
if __name__ == "__main__":

    john = Personne(1, "Doe", "John")

    epargne = Epargne("EP01", john, 1000)

    epargne.afficher_compte()

    epargne.Depot(200)
  
    epargne.Retrait(100)

    epargne.afficher_compte()
    print(f"Date dernier retrait : {epargne.DateDernierRetrait}")

    epargne = Epargne("EP01", john, 1000)
    


    print("_" * 50)
    epargne.Depot(200)
    epargne.Retrait(150)
    epargne.afficher_compte()
    print("_" * 50)
    epargne.Retrait(300)
    epargne.afficher_compte()
