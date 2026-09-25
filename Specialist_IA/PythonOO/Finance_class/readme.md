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

------------------------------------------------------------------------------------------------------------------------------------
Exercice 3
Créer une classe « Epargne » permettant la gestion d’un carnet d’épargne qui devra implémenter :

Les propriétés publiques :
Numéro (string)
Solde (float) - Lecture seule
DateDernierRetrait (DateTime) - représentant la date du dernier retrait sur le carnet
Titulaire (Personne)
Les méthodes publiques :
void Retrait(float Montant)
void Depot(float Montant)
Ajouter à la classe « Courant »:

La propriété publique :

Ligne de crédit - représentant la limite négative du compte strictement supérieur ou égale à 0
Et modifier les méthodes pour intégrer cette nouvelle limite négative du solde

Créer une classe « Compte » avec tous les éléments communs à « Courant » et « Épargne »

Si nous ajoutions la « ligne_de_credit » dans « Compte », définir sur papier les modifications qu’il faudrait apporter à nos classes.