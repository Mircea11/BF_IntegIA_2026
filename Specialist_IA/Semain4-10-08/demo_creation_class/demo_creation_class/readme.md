# Exercice 1

## Créer des Personnes

Attributs:
 - id 
 - nom
 - prenom
 
## Créer de comptes courants

Attributs:
 - numero
 - titulaire: Personne
 - solde

Ajoutez, un constructeur prenant en paramètre : 
 - Le numéro
 - le titulaire 
 - le solde

Comportement:
 - Retrait(somme)
 - Depot(somme)
  
Contrainte:
 - Pas de retrait de somme négative
 - Pas de dépot de somme négative
 - Retrait ne doit amener à un solde négatif