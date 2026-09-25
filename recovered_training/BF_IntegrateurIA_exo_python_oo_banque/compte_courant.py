from personne import Personne

class Courant:
    def __init__(self, numero: str, titulaire: Personne, solde: float = 0):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde

    def retrait(self, montant: float) -> None:
        if montant <= 0:
            print("Montant invalide")
        elif self.solde < montant:
            print("Solde insffisant")
        else:
            self.solde -= montant

    def depot(self, montant: float) -> None:
        if montant <= 0:
            print("Montant invalide")
        else:
            self.solde += montant

if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")
    courant = Courant("BE01", john_doe, 100)
    print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

    courant.retrait(25)
    print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")
    
    courant.depot(50)
    print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")