from abc import ABC, abstractmethod
from personne import Personne
from solde_insuffisant_exception import SoldeInsuffisantException


class Compte(ABC):
    def __init__(self, numero: str, titulaire: Personne, solde: float = 0.0):
        self.numero = numero
        self.titulaire = titulaire
        self._solde = float(solde)

    @property
    def solde(self) -> float:
        """Solde en lecture seule depuis l'extérieur."""
        return self._solde

    @property
    def solde_disponible(self) -> float:
        """Montant maximum retirable. Par défaut: pas de découvert."""
        return self.solde

    def depot(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("Montant invalide pour un dépôt")
        self._solde += montant

    def retrait(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("Montant invalide pour un retrait")
        if montant > self.solde_disponible:
            raise SoldeInsuffisantException(self.solde)
        self._solde -= montant

    # aliases if the exercise/test uses capitalized names
    def Depot(self, montant: float) -> None:
        self.depot(montant)

    def Retrait(self, montant: float) -> None:
        self.retrait(montant)

    def __add__(self, other):
        """Somme les soldes positifs seulement."""
        if hasattr(other, "solde"):
            other = other.solde

        solde_self = self.solde if self.solde > 0 else 0
        solde_other = other if other > 0 else 0

        return float(solde_self + solde_other)

    def __radd__(self, other):
        return self.__add__(other)

    @abstractmethod
    def CalculInteret(self) -> float:
        pass

    def AppliquerInteret(self) -> None:
        self._solde += self.CalculInteret()
