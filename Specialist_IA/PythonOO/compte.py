from personne import Personne

class Compte:
    def __init__(self, numero: str, titulaire: Personne, solde: float =0):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde

    def retrait(self,montant: float) -> None:
        if montant <=0:
            raise ValueError
            #print("Montant invalide")
            
        else:
            self.solde -= montant

    def depot(self, montant: float) -> None:
        if montant <= 0:
            print("Montant invalide")
        else: 
            self.solde += montant

    def __add__(self, other):
        if self.solde < 0:
            return  other
        return self.solde + other   