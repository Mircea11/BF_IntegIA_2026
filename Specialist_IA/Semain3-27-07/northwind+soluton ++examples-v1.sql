CREATE TABLE etudiants (
	nom TEXT,
	id_vehicule int

);

CREATE TABLE vehicules (
	ref_voiture int,
	marque TEXT

)

INSERT INTO etudiants values ( 'David', 1), ('Nicolas', 2), ('Mike', NULL)
INSERT INTO vehicules values ( 1,' Porsche'), ( 2, 'Aston Martin'), (3, 'Ferrari');
SELECT * from etudiants
Select * from vehicules

Select * 
from etudiants as S
 full join vehicules as V on S.id_vehicule = v.ref_voiture

-------------------------------------------------------------------------------------------

SELECT
    current.*,
    previous.Total AS total_prec
FROM (SELECT D.product_id,
             EXTRACT(YEAR FROM O.order_date) AS year,
             SUM(D.quantity)                 AS Total
      FROM order_details AS D
               LEFT JOIN orders AS O ON O.order_id = D.order_id
      GROUP BY D.product_id, EXTRACT(YEAR FROM O.order_date)
      ) AS current
FULL JOIN (
    SELECT D.product_id,
             EXTRACT(YEAR FROM O.order_date) AS year,
             SUM(D.quantity)                 AS Total
      FROM order_details AS D
               LEFT JOIN orders AS O ON O.order_id = D.order_id
      GROUP BY D.product_id, EXTRACT(YEAR FROM O.order_date)


    ) AS previous
ON previous.product_id = current.product_id AND current.year = previous.year + 1
ORDER BY current.year, product_id


--------------------------------------------------------------------


Select * 
from etudiants as S
 full join vehicules as V on S.id_vehicule = v.ref_voiture
 
 SELECT 



 ------------------------------------------------------
WITH prod_agg as
(
SELECT D.product_id,
             EXTRACT(YEAR FROM O.order_date) AS year,
             SUM(D.quantity)                 AS Total
      FROM order_details AS D
               LEFT JOIN orders AS O ON O.order_id = D.order_id
      GROUP BY D.product_id, EXTRACT(YEAR FROM O.order_date
),
moy_prod_agg as 
(
SELECT avg(total)
from prod_agg
)
 SELECT
    current.*,
    COALESCE(previous.TotaL,0 ) AS total_prec
FROM prod_agg AS current
FULL JOIN 
prod_agg as previous 
on previous.product_id = current.product_id AND current/year = previous.year
			--(
			--     SELECT D.product_id,
			--              EXTRACT(YEAR FROM O.order_date) AS year,
			--              SUM(D.quantity)                 AS Total
			--       FROM order_details AS D
			--                LEFT JOIN orders AS O ON O.order_id = D.order_id
			--       GROUP BY D.product_id, EXTRACT(YEAR FROM O.order_date)
			
			
			--     ) AS previous
			-- ON previous.product_id = current.product_id AND current.year = previous.year + 1
ORDER BY current.year, product_id


--------------------------------------------------------------------



WITH
prod_agg AS
    (
    SELECT D.product_id,
             EXTRACT(YEAR FROM O.order_date) AS year,
             SUM(D.quantity)                 AS Total
    FROM order_details AS D
               LEFT JOIN orders AS O ON O.order_id = D.order_id
    GROUP BY D.product_id, EXTRACT(YEAR FROM O.order_date)
    ),
--moy_prod_agg AS (
    SELECT AVG(Total)
    FROM prod_agg
    )
SELECT
    current.*,
    COALESCE(previous.Total, (SELECT * FROM moy_prod_agg)) AS total_prec
FROM prod_agg AS current
LEFT JOIN prod_agg AS previous
ON previous.product_id = current.product_id AND current.year = previous.year + 1
ORDER BY current.year, product_id;



