SELECT *
FROM order_details 

SELECT * from orders

SELECT EXTRACT(YEAR FROM o.order_date) AS year, pd.product_id
FROM orders
------------------------------------------------


SELECT 
current.*, 
previous.total as total_prec
FROM 
			(SELECT 
				EXTRACT(YEAR FROM o.order_date) AS year, 
				--od.product_id, 
				SUM(od.quantity) as Total
				
			FROM ORDERS o
			join order_details as od on o.order_id =od.order_id
			group BY year, od.product_id
			--order by year, product_id ) as current




	
LEFT JOIN 
		(SELECT 
				EXTRACT(YEAR FROM order_date) AS year, 
				od.product_id, 
				SUM(od.quantity) as Total
				
		FROM ORDERS o
			join order_details as od on o.order_id =od.order_id
			group BY year, od.product_id
			--order by year, product_id 
		) as previous

on previous.product_id = current.product_id and current.year = previous.year +1

ORDER by current.year, product_id






-----------------------------------------


SELECT * 
FROM
order_details
where product_id in (71,31)

SELECT product_id, sum (quantity) as Total
from order_details 
GROUP BY product_id
Having sum(quantity) > 1000


-----------------------------------------


SELECT * 
FROM
order_details
where product_id in ( 
				SELECT product_id--, sum (quantity) as Total
				from order_details 
				GROUP BY product_id
				Having sum(quantity) > 1000
)

LEFT JOIN products as P on P.



--------------------------------------------

SELECT D.*, P.product_name
FROM order_details as D
LEFT JOIN products as P on P.product_id = D.product_id

where d.product_id in ( 
				SELECT product_id--, sum (quantity) as Total
				from order_details 
				GROUP BY product_id
				Having sum(quantity) > 1000
)

LEFT JOIN products as P on P.

-------------------------------------------------------------------------

SELECT * from  categories


SELECT * from products

SELECT * FROM order_details 

SELECT * from orders


SELECT 
avg(unit_price)::numeric(10,2), 
category_name 

FROM products as p
join categories as c on c.category_id = p.category_id
group by category_name




SELECT 
p.product_name, 
p.unit_price,
p.category_id
from products as p
WHere unit_price < (SELECT 
avg(unit_price)::numeric(10,2)--, category_name 

FROM products as p
join categories as c on c.category_id = p.category_id

--group by category_name 
)

Group by 
p.product_name,
p.unit_price,
p.category_id



SELECT avg.*, p.*
FROM products as p
	LEFT join (
		SELECT AVG(unit_price) as avg_cat, category_id
		from products
		group by category_id
	) avg
on p.category_id = avg.category_id
WHERE p.unit_price < avg.avg_cat


---(difference in INNER and not LEFT )
SELECT avg.*, p.*
FROM products as p
	right join (
		SELECT AVG(unit_price)::numeric(10,2) as avg_cat, category_id
		from products
		group by category_id
	) avg
on p.category_id = avg.category_id AND p.unit_price < avg.avg_cat


---------------------------------------------Sourequetes correlees (WHERE p2.category_id = p.category_id)--------------------------------------------------
 SELECT *
 FROM products as p
 WHERE p.unit_price < (
	SELECT AVG(unit_price)::numeric(10,2) as avg_cat--, category_id
		from products as p2
		WHERE p2.category_id = p.category_id
		GROUP BY category_id
		)


------------------------------------------------------------------------CTE---------------------------------------
WITH liste_produits_sup_1000 AS (  
	SELECT product_id
    FROM order_details
    GROUP BY product_id
    HAVING SUM(quantity) > 1000
)

SELECT D.*, P.product_name
FROM order_details AS D
LEFT JOIN products AS P ON P.product_id = D.product_id
WHERE d.product_id  IN 
	( 
		SELECT * FROM liste_produits_sup_1000
  
);

---------------------------------

SELECT * from order_details

with total_general as (
	SELECT sum( order_details.quantity)
	FROM order_details
	)
SELECT sum (quantity):: NUMERIC(10,2)/(SELECT * FROM total_general) :: NUMERIC(10,2),
	product_id
FROM order_details
GROUP BY product_id
Order by product_id 



	
with total_general as (
	SELECT sum( order_details.quantity)
	FROM order_details
	)
SELECT sum (quantity),--:: NUMERIC(10,2)/(SELECT * FROM total_general) :: NUMERIC(10,2),
	product_id,
	'test' as test
FROM order_details
GROUP BY product_id
Order by product_id 



-----------------------------------------------------------------------
difference entre le OVER et group by

SELECT
    *,
    X.quantity / SUM(quantity) OVER ()
FROM
       (
        SELECT
        SUM(quantity) AS quantity,
        product_id
        FROM order_details
        GROUP BY product_id
       ) AS X

---------------------------fenetrage

	   SELECT 
	   product_id, 
	   product_name, 
	   units_in_stock,
	   category_id,
	   --(SELECT SUM(units_in_stock) FROM products)
	   ---SUM(units_in_stock) OVER () AS total_tale, 
	   SUM (units_in_stock) OVER (PARTITION BY category_id) as total_cat
	   FROM products


-----------------------sans fenetrage-------------------

WITH tot_by_cat AS (
	SELECT SUM(units_in_stock) as stock_total, category_id
	FROM products
	GROUP BY category_id
	)
SELECT 
	product_id,
	product_name,
	units_in_stock,
	p.category_id,
	t.stock_total
FROM products as p
Left JOIN tot_by_cat as T 
ON t. category_id = P.category_id


-----------------------------------------------------------------

SELECT *,

sum(quantity) OVER (PARTITION BY order_id) ,
sum(quantity) OVER (PARTITION BY product_id)

FROM order_details


SELECT *
FROM products
ORDER BY unit_price DESC


SELECT product_id, 
	product_name, 
	category_id, 
	unit_price,
	rank() OVER (ORDER BY unit_price DESC),
	rank() OVER (PARTITION by category_id ORDER BY unit_price DESC) as rank_par_cat
FROM products
--ORDER BY unit_price DESC
--WHERE rank() OVER (PARTITION by category_id ORDER BY unit_price DESC) as rank_par_cat >= 3
---the last line doe snot work a cause que it does not yet exists in the ranking of operatin of exection
-- we do it as an insertion


SELECT *
FROM (
SELECT product_id, 
	product_name, 
	category_id, 
	unit_price,
	rank() OVER (ORDER BY unit_price DESC),
	rank() OVER (PARTITION by category_id ORDER BY unit_price DESC) as rank_par_cat,
	row_number() over ()
FROM products
) AS X
WHERE x.rank_par_cat <= 3


----------------------------------------------------------------------------------

SELECT *
FROM orders
ORDER BY customer_id, order_date DESC


SELECT customer_id, order_id, order_date,
	LAG(order_date,1) OVER (PARTITION BY customer_id ORDER BY order_date aSC),
	order_date - MIN(order_date) OVER (PARTITION BY customer_id ORDER BY order_date aSC)
	
FROM orders
ORDER BY customer_id, order_date asc

-------------------------------------------------
WITH orders_enriched as
	(SELECT customer_id,
	order_id,
	order_date,
	LAG(order_date,1) OVER (PARTITION BY customer_id ORDER BY order_date aSC) AS prec_date,
	order_date - MIN(order_date) OVER (PARTITION BY customer_id ORDER BY order_date aSC) as first_date 
)	

SELECT customer_id, AVG(order_date - prec_date) as delai_moyen
FROM orders_enriched
WHERE prec_date is not null
GROUP BY customer_id


-------------------------cumul 

with total_par_jour as (

	SELECT sum(quantity) as total_jour, O.order_date
	FROM orders as o
	Left join order_details as d on o.order_id =d.order_id
	Group by o.order_date
	)
	SELECT order_date,
	total_jour,
	sum(total_jour) over (partition by EXTRACT(year from order_date) order by order_date asc),
	--avg(total_jour) over (order by order_date rows between 3 preceding and current row)
	avg(total_jour) over (order by order_date rows between 3 preceding and 1 following)
FROM total_par_jour
Order by order_date


-----------------------------------------------


-- ### Exercice 2 — Vue clients dynamique avec segmentation
-- Créer une vue `v_clients_segmentation` contenant : `customer_id`,
-- `company_name`, `contact_name`, le nombre de commandes passées par le
-- client, et un flag `segment` valant `'Top client'` si le client a passé
-- plus de commandes que la moyenne des autres clients, sinon
-- `'Client standard'`. Ajouter une colonne `anciennete_jours` correspondant
-- au nombre de jours entre la date de sa première commande et aujourd'hui.
	
-- with total_general as (
	SELECT sum( order_details.quantity)
	FROM order_details
-- 	)
-- SELECT sum (quantity),--:: NUMERIC(10,2)/(SELECT * FROM total_general) :: NUMERIC(10,2),
-- 	product_id,
-- 	'test' as test
-- FROM order_details
-- GROUP BY product_id
-- Order by product_id 

SELECT * --count(order_id)
FRom order_details
-- group by customer_id

SELECT *
FROM customers

SELECT customer_id,
max(order_date)-min(order_date) as num_days
FROM orders
group by customer_id


SELECT count (order_id), customer_id
from orders
group by customer_id
order by count (order_id) asc


SELECT *
FROM orders
--------------------------------------------------------------------------------------
-----------------------------TIME------------------------------------------------------------

SELECT customer_id,
max(order_date)-min(order_date) as num_days
FROM orders
group by customer_id
---------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------

WITH avg_calculated AS
(
	Select AVG(count_orders)::numeric(10,2) as avg_count_orders
	FROM ( SELECT customer_id, count(*) as count_orders
	FROM orders
	Group by customer_id)
)

SELECT 
c.customer_id, 
company_name, 
contact_name, 
-- count(*),
-- (SELECT * FROM avg_calculated),
-- count(*) - (SELECT * FROM avg_calculated),
-- max(order_date),
CASE
	WHEN count(*) - (SELECT * FROM avg_calculated) >0
	THEN 'Top client'
	ELSE 'Ordinary client'
END as flag,
max(order_date)-min(order_date) as num_days

FROM customers as c
LEFT join orders as o on c.customer_id = o.customer_id
GROUP BY c.customer_id
order by num_days asc


-- ----------------------------------AVG------------------------------------------------------


-- Exercice 3 — Produits : prix catalogue vs dernier prix pratiqué
-- Récupérer tous les produits distincts avec :
-- a. leur id, nom et catégorie (si NULL, remplacer par `'NA'`) — adaptation :
-- Northwind n'ayant pas de sous-catégorie, on ne garde qu'un seul niveau de
-- catégorie.
-- b. leur `unit_price` (prix catalogue actuel).
-- c. le dernier prix pratiqué pour ce produit dans `order_details` (celui de
-- la commande la plus récente) — adaptation : à défaut de table
-- `ProductCostHistory`, on utilise l'historique des prix effectivement
-- facturés dans les commandes.
-- d. une colonne calculant la différence entre les deux, pour vérifier s'il y
-- en a une.

SELECT *
FROM 
products
-------------------------
SELECT *
FROM 
order_details

-------------------------------------
SELECT *
FROM 
orders
--------------------------------------------------------------
SELECT *
FROM categories

----------------------------------prix_pratique---------------------------------------
SELECT 
DISTINCT product_id,
--order_date,
--max(order_date),
 DISTINCT od.unit_price,
max(order_date) OVER (PARTITION BY product_id) as max_order_date
--,*
FROM 
order_details od
JOIN orders as o on o.order_id = od.order_id
--GROUP by product_id, od.unit_price, order_date



-------------------------------------------------------------------------

SELECT 
od.product_id,
p.product_name,
COALESCE(c.category_name, 'NA') AS category_name,
 -- o.order_id,
p.unit_price as prix_catalogue
--order_price as prix_pratique
--diference
FROM 
order_details as od
JOIN products as p on p.product_id = od.product_id
JOIN orders as o on o.order_id = od.order_id
JOIN categories c on c.category_id = p.category_id
order by c.category_name


---------------------------------------------


--28-07-2026
CREATE OR REPLACE VIEW order_consolidate as
SELECT d.*,
o.order_date,
p.product_name
p.category_id
FROM order_details as d
LEFT JOIN orders as o on d.order_id = o.order_id
LEFT join products as p on p.product_id = d.product_id

CREATE MATERIALIZED VIEW order_consolidate_mat as
SELECT d.*,
o.order_date,
p.product_name

FROM order_details as d
LEFT JOIN orders as o on d.order_id = o.order_id
LEFT join products as p on p.product_id = d.product_id

select
*
from
order_consolidate_mat

select
*
from
order_consolidate


---------------------------------------------------

WITH last_price AS (
    SELECT DISTINCT *
    FROM (SELECT product_id,
                 unit_price AS last_price,
                 rank() OVER (PARTITION BY product_id ORDER BY O.order_date DESC) AS rank
          FROM order_details AS D
                   LEFT JOIN orders AS O ON D.order_id = O.order_id) AS X
    WHERE rank = 1)
SELECT *,
       unit_price - last_price AS diff
FROM products AS P
LEFT JOIN last_price AS LP ON LP.product_id = P.product_id


-------------------------------------------------------------

WITH qty_cat AS
(
    SELECT SUM(O.quantity) AS total, C.category_name
    FROM order_details AS O
    LEFT JOIN products AS P ON O.product_id = P.product_id
    LEFT JOIN categories AS C ON C.category_id = P.category_id
    GROUP BY C.category_name
    )
SELECT *,
       total / SUM(total) OVER () AS pct_ind,
       SUM(total) OVER (ORDER BY total DESC) / SUM(total) OVER () AS pct_cumulé
FROM qty_cat
ORDER BY total DESC