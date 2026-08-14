from de import De
from outils import generer_caracteristique, modificateur
from personnage import Personnage
from human import Humain
from nain import Nain
from monster import Monster
from loup import Loup
from orque import Orque
from dragonnette import Dragonnette

d6 = De(1,6)
d4 = De(1,4)



print ("Test d6")
print(d6.minimum)
print(d6.maximum)
for i in range(10):
    print(d6.lance())

print ("Test d4")
print(d4.minimum)
print(d4.maximum)
for i in range(10):
    print(d4.lance())


#from outils import generer_caracteristique

print("Test génération caractéristique")

for i in range(10):
    print(generer_caracteristique())


#from outils import modificateur


print("Test modificateur")

print("4  ->", modificateur(4))    # -1
print("5  ->", modificateur(5))    # 0
print("9  ->", modificateur(9))    # 0
print("10 ->", modificateur(10))   # 1
print("14 ->", modificateur(14))   # 1
print("15 ->", modificateur(15))   # 2
print("18 ->", modificateur(18))   # 2

#from personnage import Personnage


p1 = Personnage()
p2 = Personnage()

print("Avant combat")
print("P1 :", p1)
print("P2 :", p2)

print("_" * 50)

p1.frapper(p2)

print("_" * 50)
print("Après attaque")
print("P1 :", p1)
print("P2 :", p2)

print("_" * 50)
print("P2 est mort ?", p2.est_mort())

print("_" * 50)
p2.se_reposer()
print("Après repos de P2")
print("P2 :", p2)

# from personnage import Personnage
# from humain import Humain
# from nain import Nain


p = Personnage()
h = Humain()
n = Nain()

print("Personnage :", p)
print("Humain     :", h)
print("Nain       :", n)

print("_" * 50)

print("Types")
print("Humain is Hero?", isinstance(h, Humain))
print("Nain is Nain?", isinstance(n, Nain))
print("Humain is Personnage?", isinstance(h, Personnage))
print("Nain is Personnage?", isinstance(n, Personnage))

print("_" * 50)

print("Combat test")
h.frapper(n)
print("Après attaque")
print("Humain :", h)
print("Nain   :", n)

print("_" * 50)

print("Combat test")
n.frapper(h)
print("Après attaque")
print("Humain :", h)
print("Nain   :", n)

# This test creates one monster of each type.
# It verifies inheritance, bonuses, PV calculation, and loot generation.

# from personnage import Personnage
# from monstre import Monstre
# from loup import Loup
# from orque import Orque
# from dragonnet import Dragonnet


loup = Loup()
orque = Orque()
dragonnette = Dragonnette()

print(loup)
print(orque)
print(dragonnette)

print("_" * 50)

print("Loup is Monstre?", isinstance(loup, Monstre))
print("Orque is Monstre?", isinstance(orque, Monstre))
print("Dragonnette is Monstre?", isinstance(dragonnet, Monstre))

print("_" * 50)

print("Loup is Personnage?", isinstance(loup, Personnage))
print("Orque is Personnage?", isinstance(orque, Personnage))
print("Dragonnette is Personnage?", isinstance(dragonnet, Personnage))