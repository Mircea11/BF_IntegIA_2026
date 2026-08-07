# Module 7 — Les Procédures Stockées — Exercices (stagiaires)

Base utilisée : Northwind (`employees`, `orders`, `order_details`).

## Exercice 1 — Procédure simple (DML)
Créer une procédure `changer_titre_employe(p_employee_id INT, p_nouveau_titre TEXT)`
qui met à jour le `title` d'un employé donné. Tester avec `CALL`.

## Exercice 2 — Procédure avec INOUT
Créer une procédure `cloturer_commande(p_order_id INT, INOUT p_montant_total NUMERIC)`
qui marque une commande comme expédiée (renseigne `shipped_date` à la
date du jour) et renvoie, via `INOUT`, le montant total de cette commande.

## Exercice 3 — Procédure avec SQL dynamique
Créer une procédure `copier_table(p_nom_table TEXT)` qui :

- si `p_nom_table` correspond à une table existante du schéma `public` :
  crée une copie de cette table, nommée `<nom_table>_copy` (ex :
  `customers` → `customers_copy`), **seulement si cette copie n'existe pas
  déjà** (sinon, ne rien faire, juste un message) ;
- si `p_nom_table` ne correspond à aucune table existante : afficher un
  message d'erreur, puis lister (avec une boucle) les noms de toutes les
  tables disponibles du schéma `public`.

Indice : le nom de la table n'est connu qu'au moment de l'appel (c'est un
paramètre), donc impossible d'écrire directement `SELECT * FROM
p_nom_table`. Il faut construire la requête sous forme de **chaîne de
caractères**, puis l'exécuter avec `EXECUTE` — `EXECUTE` permet de faire
tourner n'importe quel `SELECT`/`CREATE`/`INSERT`... écrit comme du texte
plutôt que du SQL "en dur". Pour construire proprement cette chaîne (en y
insérant le nom de table), utiliser la fonction `format('... %I ...',
p_nom_table)` : elle remplace `%I` par la valeur passée, comme un `RAISE
NOTICE` avec `%`, mais en échappant correctement le nom (utile s'il
contient des caractères spéciaux).
