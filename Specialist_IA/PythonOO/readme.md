# Créer des Personnes

Attributs:
 - id
 - nom
 - prenom
 
# Créer de comptes courants

Attributs:
 - numero
 - titulaire: Personne
 - solde

Ajoutez, un constructeur prenant en paramètre : 
	- Le numéro, le titulaire ,le solde

Comportement:
 - Retrait(somme)
 - Depot(somme)
  
Contrainte:
 - Pas de retrait de somme négative
 - Pas de dépot de somme négative
 - Retrait ne doit amener à un solde négatif

---------------------------------------------------------------------------------------------------------------------
Exercice 2

Surcharger l’opérateur « + » de la classe « Courant » afin qu’il retourne la somme, de type double, des soldes. Cependant, les soldes négatifs ne doivent pas être pris en compte.

Créer une classe « Banque ».

Attributs: - nom - comptes: dict<numero, Courant>

Ajouter une méthode « AvoirDesComptes » à la classe « Banque » recevant en paramètre le titulaire (Personne) qui calculera les avoirs de tous ses comptes en utilisant l’opérateur « + ».