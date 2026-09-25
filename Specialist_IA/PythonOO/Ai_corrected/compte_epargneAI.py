from datetime import datetime
from personne import Personne
from compte import Compte


class Epargne(Compte):
    def __init__(self, numero: str, titulaire: Personne, solde: float = 0.0, date_dernier_retrait=None):
        super().__init__(numero, titulaire, solde)
        self.date_dernier_retrait = date_dernier_retrait

    def retrait(self, montant: float) -> None:
        super().retrait(montant)
        self.date_dernier_retrait = datetime.now()

    def CalculInteret(self) -> float:
        return self.solde * 0.045

    def __str__(self):
        return (
            f"Compte épargne {self.numero} | Titulaire : {self.titulaire} | "
            f"Solde : {self.solde} EUR | Dernier retrait : {self.date_dernier_retrait}"
        )
