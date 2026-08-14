from personne import Personne
from abc import ABC, abstractmethod

class Compte(ABC):
    def __init__(self, numero: str, titulaire: Personne, solde: float =0):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde

    def retrait(self,montant: float) -> None:
        if montant <=0:
            raise ValueError("Montant invalide pour un retrait")
        else:
            self.solde -= montant

    def depot(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("Montant invalide pour un dépôt")
        else: 
            self.solde += montant

    def __add__(self, other):
        if self.solde < 0:
            return  other
        return self.solde + other 

    

    @abstractmethod
    def CalcullInteret(self) -> float:
        if self.solde >= 0:
            return self.solde * 0.03
        else:
            return self.solde * 0.0975

    #def CalcullInteret (taux_livret_eparne: float = 0.045, taux_compte_courant: float):
