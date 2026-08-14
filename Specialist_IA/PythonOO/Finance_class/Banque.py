# Exercice 2

# Surcharger l’opérateur « + » de la classe « Courant » afin qu’il retourne la somme, de type double, des soldes.
# Cependant, les soldes négatifs ne doivent pas être pris en compte.

# Créer une classe « Banque ».

# Attributs: - nom - comptes: dict<numero, Courant>

# Ajouter une méthode « AvoirDesComptes » à la classe « Banque » recevant en paramètre le titulaire (Personne)
# qui calculera les avoirs de tous ses comptes en utilisant l’opérateur « + ».

# class Personne:
#     def __init__(self, id, nom, prenom):
#         self.id = id
#         self.nom = nom
#         self.prenom = prenom

#     def __str__(self):
#         return f"{self.prenom} {self.nom}"



# class Courant:
#     def __init__(self, numero: str, titulaire: Personne, solde: float = 0.0):
#         self.numero = numero
#         self.titulaire = titulaire
#         self.solde = solde

#     def __add__(self, other):
#         solde_self = self.solde if self.solde > 0 else 0

#         if isinstance(other, Courant):
#             solde_other = other.solde if other.solde > 0 else 0
#         elif isinstance(other, (int, float)):
#             solde_other = other if other > 0 else 0
#         else:
#             raise TypeError("On peut additionner seulement un Courant ou un nombre.")

        
#         def __str__(self):
#             return f"{self.prenom} {self.nom} {solde_self} + {solde_other}"
        
#         return float(solde_self + solde_other)

# # comptes = dict()

# #     comptes["BE01"] = Courant("BE01", john, 100.0)


from personne import Personne
from compte_courant import Courant
from compte_epargne import Epargne
from compte import Compte


class Banque:
    def __init__(self, nom: str, comptes = None):
        self.nom = nom

        if comptes is None:
            comptes= dict()
        self.comptes = comptes

    def ajouter_compte(self, compte: Compte):
        if not isinstance(compte, Compte):
            print("Ce n'est pas une compte valide que vous tentez d'ajouter a la banque!")
            return
        
        self.comptes[compte.numero] = compte

    
    def retirer_compte(self,compte):
        self.comptes.pop(compte.numero)
        


    def avoir_des_comptes(self, titulaire):
        total = 0.0

        for compte in self.comptes.values():
            if compte.titulaire == titulaire:
                total = compte + total

        return total
# #  avoir_john = banque.AvoirDesComptes(john)


if __name__ == "__main__":
    titulaire1 = Personne("01", "Doe", "John")
    titulaire2 = Personne("02", "Smith", "Anna")

    #comptes = dict()

    compte1 = Courant("BE01", titulaire1, 100.0, -50)
    compte2 = Courant("BE02", titulaire1, 250.0, 250)
    compte3 = Epargne("BE03", titulaire1, 250.0)
    compte4 = Courant("BE04", titulaire2, 500.0)
    compte5 = Courant("BE05", titulaire2, 300.0)
    compte6 = Courant("BE06", titulaire2, -100.0)

    banque = Banque("NeoBanque")
    banque2 = Banque("AutreBanque")


    # for numero in banque.comptes:
    #     compte = banque.comptes[numero]
    #     print(f"{numero} : {compte.titulaire} - solde : {compte.solde}")

    print("_" * 50)

    # avoir_john = banque.avoir_des_comptes(titulaire1)
    # print(f"Avoir total de {titulaire1} : {avoir_john}")
    # print("_" * 50)
    # avoir_anna = banque.avoir_des_comptes(titulaire2)
    # print(f"Avoir total de {titulaire2} : {avoir_anna}")
    # print("_" * 50)
    #print(comptes)
    
    #print(Compte.titulaire, Compte.numero, Compte.solde)
    try:
        banque.ajouter_compte("mon grand compte courant")
        banque.ajouter_compte(compte1)
        banque2.ajouter_compte(compte2)
        banque2.ajouter_compte(compte3)
    except Exception as exception:
        print(exception)
    print("_" * 50)

    print(banque.avoir_des_comptes(titulaire1))
    print(banque2.avoir_des_comptes(titulaire1))
    print(titulaire1)