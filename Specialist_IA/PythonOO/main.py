from personne import Personne
from compte_courant import Courant
from compte_epargne import Epargne
from solde_insuffisant_exception import SoldeInsuffisantException


# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

# courant.retrait(25)
# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

# courant.depot(50)
# print(f"Le compte courant {courant.numero} possédé par {courant.titulaire.prenom} avec {courant.solde} €")

john_doe = Personne(1, "Doe", "John")
courant = Courant("BE01", john_doe, -100)
print(courant)

try: 
    courant.retrait(50)
except ValueError as error:
    print(error)
except SoldeInsuffisantException as exception:
    print(exception)


#epargne = Epargne("BE01", john_doe, 100)
try: 
    epargne.retrait(50)
    print(epargne.date_dernier_retrait)
except ValueError as error:
    print(error)
except SoldeInsuffisantException as exception:
    print(exception)
print(epargne)

#python -c "import sys; print(sys.executable); print(sys.version)"