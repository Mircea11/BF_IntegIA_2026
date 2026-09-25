from personne import Personne
from compte_courant import Courant

john_doe = Personne(1, "Doe", "John")
courant = Courant("BE01", john_doe, 100)
print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

courant.retrait(25)
print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

courant.depot(50)
print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")