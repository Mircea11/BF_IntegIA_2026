# Exercice 2

# Surcharger l’opérateur « + » de la classe « Courant » afin qu’il retourne la somme, de type double, des soldes.
# Cependant, les soldes négatifs ne doivent pas être pris en compte.

# Créer une classe « Banque ».

# Attributs: - nom - comptes: dict<numero, Courant>

# Ajouter une méthode « AvoirDesComptes » à la classe « Banque » recevant en paramètre le titulaire (Personne)
# qui calculera les avoirs de tous ses comptes en utilisant l’opérateur « + ».

class Personne:
    def __init__(self, id, nom, prenom):
        self.id = id
        self.nom = nom
        self.prenom = prenom

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Courant:
    def __init__(self, numero: str, titulaire: Personne, solde: float = 0.0):
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde

    def __add__(self, other):
        solde_self = self.solde if self.solde > 0 else 0

        if isinstance(other, Courant):
            solde_other = other.solde if other.solde > 0 else 0
        elif isinstance(other, (int, float)):
            solde_other = other if other > 0 else 0
        else:
            raise TypeError("On peut additionner seulement un Courant ou un nombre.")

        return float(solde_self + solde_other)
    def __str__(self):
         return f"{self.prenom} {self.nom} {solde_self} + {solde_other}"

# comptes = dict()

#     comptes["BE01"] = Courant("BE01", john, 100.0)

class Banque:
    def __init__(self, nom: str, comptes: dict):
        self.nom = nom
        self.comptes = comptes

    def AvoirDesComptes(self, titulaire: Personne):
        total = 0.0

        for compte in self.comptes.values():
            if compte.titulaire.id == titulaire.id:
                total = compte + total

        return total
# #  avoir_john = banque.AvoirDesComptes(john)
    def ajouter_compte(self, compte):
        pass
        #self.compte(compte.numero) = compte
    def retirer_compte(self,compte):
        self.comptes.pop(compte.numero)
        pass

if __name__ == "__main__":
    john = Personne("01", "Doe", "John")
    anna = Personne("02", "Smith", "Anna")

    comptes = dict()

    comptes["BE01"] = Courant("BE01", john, 100.0)
    comptes["BE02"] = Courant("BE02", john, 250.0)
    comptes["BE03"] = Courant("BE03", john, -50.0)
    comptes["BE04"] = Courant("BE04", anna, 500.0)
    comptes["BE05"] = Courant("BE05", anna, 300.0)
    comptes["BE06"] = Courant("BE06", anna, -100.0)

    banque = Banque("NeoBanque", comptes)

    for numero in banque.comptes:
        compte = banque.comptes[numero]
        print(f"{numero} : {compte.titulaire} - solde : {compte.solde}")

    print("_" * 50)

    avoir_john = banque.AvoirDesComptes(john)
    print(f"Avoir total de {john} : {avoir_john}")
    print("_" * 50)
    avoir_anna = banque.AvoirDesComptes(anna)
    print(f"Avoir total de {anna} : {avoir_anna}")
    print("_" * 50)
    #print(comptes)
    print("_" * 50)
    print(compte.titulaire,compte.numero, compte.solde)