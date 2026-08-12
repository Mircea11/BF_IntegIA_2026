# Module 6 — Les Fonctions — Exercices (stagiaires)

Base utilisée : Northwind (`customers`, `orders`, `order_details`,
`employees`).

## Exercice 1 — Fonction scalaire (agrégat)
Créer une fonction `chiffre_affaires_client(p_customer_id TEXT)` qui
retourne le montant total (`NUMERIC`) dépensé par un client, calculé sur
toutes ses commandes (`quantity * unit_price * (1 - discount)`).

## Exercice 2 — Fonction scalaire (calcul de date)
Créer une fonction `anciennete_employe(p_employee_id INT)` qui retourne le
nombre d'années pleines (`INT`) depuis la date d'embauche (`hire_date`)
d'un employé donné.

## Exercice 3 — Fonction scalaire avec conditions
Créer une fonction `remise_par_palier(p_montant NUMERIC)` qui retourne le
montant après remise, selon des paliers :

- 0 % en dessous de 100
- 5 % entre 100 et 499
- 10 % entre 500 et 999
- 15 % à partir de 1000

Utiliser un enchaînement `IF / ELSIF / ELSE`.

## Exercice 4 — Fonction tabulaire avec RETURN QUERY
Créer une fonction `commandes_client(p_customer_id TEXT)` qui retourne,
pour un client donné, la liste de ses commandes : `order_id`,
`order_date`, et le montant total de chaque commande (`montant`).
