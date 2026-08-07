# Module 11 — Sous-requêtage & Fonctions de fenêtrage — Exercices (stagiaires)

Base utilisée : Northwind (`products`, `categories`, `orders`, `order_details`, `customers`).

> **Notes d'adaptation** (par rapport à la version AdventureWorks d'origine) :
> Northwind n'a qu'un seul niveau de catégorie (pas de sous-catégorie), pas de
> table d'historique des coûts (`ProductCostHistory`), pas de schéma d'achats
> (`Purchasing`), pas de flag "commande en ligne", et les clients n'ont
> qu'un `contact_name` (pas de nom/prénom séparés). Chaque exercice concerné
> précise l'adaptation retenue.

## Partie 1 — Sous-requêtage

### Exercice 1 — Produits les plus chers par catégorie
Récupérer, pour chaque catégorie de `categories`, le ou les produits de
`products` dont le `unit_price` est le plus élevé de la catégorie.

### Exercice 2 — Vue clients dynamique avec segmentation
Créer une vue `v_clients_segmentation` contenant : `customer_id`,
`company_name`, `contact_name`, le nombre de commandes passées par le
client, et un flag `segment` valant `'Top client'` si le client a passé
plus de commandes que la moyenne des autres clients, sinon
`'Client standard'`. Ajouter une colonne `anciennete_jours` correspondant
au nombre de jours entre la date de sa première commande et aujourd'hui.

### Exercice 3 — Produits : prix catalogue vs dernier prix pratiqué
Récupérer tous les produits distincts avec :
a. leur id, nom et catégorie (si NULL, remplacer par `'NA'`) — *adaptation :
Northwind n'ayant pas de sous-catégorie, on ne garde qu'un seul niveau de
catégorie.*
b. leur `unit_price` (prix catalogue actuel).
c. le dernier prix pratiqué pour ce produit dans `order_details` (celui de
la commande la plus récente) — *adaptation : à défaut de table
`ProductCostHistory`, on utilise l'historique des prix effectivement
facturés dans les commandes.*
d. une colonne calculant la différence entre les deux, pour vérifier s'il y
en a une.

### Exercice 4 — Quantités et montants vendus, par année et catégorie
*Adaptation : Northwind n'a pas de schéma d'achats (`Purchasing`) comme
AdventureWorks ; l'exercice compare donc deux mesures de vente.*
Faire une requête qui donne, pour toutes les années et catégories de
produit : le total des quantités vendues, et le total du montant vendu
(`quantity * unit_price * (1 - discount)`). La table doit compter 4
colonnes : Année, Catégorie, Total Quantité, Total Montant.

### Exercice 5 — Évolution des quantités commandées, mois par mois vs N-1
Faire une table donnant, pour chaque année et chaque mois : le total des
quantités commandées (`quantity`), le total de l'année précédente pour ce
même mois, et la différence entre les deux en valeur brute et en
pourcentage.

## Partie 2 — Fonctions de fenêtrage

### Exercice 1 — Top 10 des produits par quantité vendue
*Adaptation : Northwind ne distingue pas les canaux de vente (pas de flag
"en ligne" comme dans AdventureWorks) ; on classe donc l'ensemble des
ventes.*
Classer les produits selon leur quantité totale vendue (créer une colonne
de classement) et ne récupérer que les 10 meilleurs.

### Exercice 2 — Cumul des ventes par jour, réinitialisé chaque année
Calculer le montant total des ventes par jour de commande, puis un total
cumulé de ce montant qui doit se réinitialiser à chaque nouvelle année.

### Exercice 3 — Part de marché de chaque produit
Calculer la part (en %) de chaque produit dans le total des ventes.
Calculer également sa part (en %) au sein des ventes de sa propre
catégorie.

### Exercice 4 — Ventes du jour vs moyenne mobile des 3 jours précédents
Calculer le montant des ventes par jour, et déterminer si ce montant est
au-dessus ou en dessous de la moyenne des 3 jours précédents. Créer un
flag pour l'indiquer.

### Exercice 5 — Délai moyen entre deux commandes par client
Pour chaque client, calculer le temps moyen (en jours) entre deux
commandes consécutives. Si le client n'a passé qu'une seule commande, la
valeur doit être NULL.

### Exercice 6 — Vue Pareto des ventes par catégorie de produit
*Adaptation : pas de sous-catégorie dans Northwind, on utilise la
catégorie.*
Créer une vue permettant de tracer facilement une courbe de Pareto des
ventes par catégorie de produit. La vue doit contenir la catégorie, le
total des ventes, ainsi que le pourcentage cumulé des ventes, trié du plus
vendu au moins vendu.
