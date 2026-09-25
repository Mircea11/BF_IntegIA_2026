--1. Declaratio et affectation directe (explicatio du DO$$)

DO $$
DECLARE
-- 	v_nom text;
-- 	v_age INT;

	v_nom text := 'Dupont';
	v_age INT := 30;
BEGIN
	RAISE NOTICE 'test';
	RAISE NOTICE '%', v_nom;
	RAISE NOTICE 'le nom est % et l''age est % ans', v_nom , v_age;





END;


$$;


--2. Select INTO VARIABLES (recuperer le nom et le prix d'un produut)


--SELECT product_name, unit_price FROM products

DO $$
DECLARE
	v_nom text;
	v_price text;
BEGIN
	--SELECT product_name, unit_price FROM products LIMIT 1;
	--SELECT product_name, unit_price INTO v_nom, v_price FROM products LIMIT 1;
	SELECT product_name, unit_price INTO STRICT v_nom, v_price FROM products LIMIT 1;
	RAISE NOTICE 'le nom est % et l''age est % ans', v_nom , v_price;
	
END;
$$;


---- 3. %TYPE 5 REcuperer le prix d'un produit dans le type DB de ce produit


DO $$
DECLARE
	v_prix products.unit_price%type;
	--v_price text;
BEGIN
	--SELECT product_name, unit_price FROM products LIMIT 1;
	--SELECT product_name, unit_price INTO v_nom, v_price FROM products LIMIT 1;
	--SELECT product_name, unit_price INTO STRICT v_nom, v_price FROM products LIMIT 1;
	--RAISE NOTICE 'le nom est % et l''age est % ans', v_nom , v_price;

	SELECT unit_price into v_prix FROM products WHERE product_id = 1;
	RAISE NOTICE '%', v_prix;
	
END;
$$;


----4. %ROWTYPE et record recuperer tous les attributs d'une ligne de produit ou de'employe




DO $$
DECLARE
	v_customer customers%rowtype;
	v_product RECORD;
BEGIN
	--SELECT product_name, unit_price FROM products LIMIT 1;
	--SELECT product_name, unit_price INTO v_nom, v_price FROM products LIMIT 1;
	--SELECT product_name, unit_price INTO STRICT v_nom, v_price FROM products LIMIT 1;
	--RAISE NOTICE 'le nom est % et l''age est % ans', v_nom , v_price;
	--SELECT unit_price into v_prix FROM products WHERE product_id = 1;
	--RAISE NOTICE '%', v_prix;
	SELECT * into v_customer FROM customers LIMIT 1;
	SELECT * into v_product FROM products LIMIT 1;
	RAISE NOTICE 'Le client % est de ma ville %', v_customer.contact_name, v_customer.city;
	RAISE NOTICE 'Le product % coute %', v_product.product_name, v_product.uni  t_price;
	
END;
$$;

SELECT * FROM customers LIMIT 1;
	SELECT * FROM products LIMIT 1;

	-- 1. Variables
	-- 2. Conditionelles
	-- 3. Bucles
	-- 4. Functions
	-- 5. Procedures
	-- 6. Trigers


	-- 1a . IF ELSEIF ELSE prendre une produit et dire si rupture de stock
	

DO $$
DECLARE
	v_unit_stock INT;
	--v_product RECORD;
BEGIN
	
	SELECT units_in_stock into v_unit_stock FROM products where product_id = 1;
		IF v_unit_stock = 0 THEN
			RAISE NOTICE 'Le stock est %, c''est lq misere', v_unit_stock;
		Elseif v_unit_stock < 20 THEN
			RAISE NOTICE 'Le stock est %, Ca est tres bas', v_unit_stock;
		Elseif v_unit_stock > 20 THEN
			RAISE NOTICE 'Le stock est %, Ca est haut', v_unit_stock;
		ELSE
			RAISE NOTICE 'Stock est %, Ca est inconue', v_unit_stock;
		ENd IF;
			
END;
$$;

--1b. WHILE (affiche x et son caree)


DO $$
DECLARE
	v_i INT:=1;
BEGIN
	
	WHILE v_i <=20 LOOP
		--RAISE NOTICE '% -----%', v_i, v_i*v_i;
		RAISE NOTICE '% -----%', v_i, POWER(v_i,2);
		v_i=v_i+1;
	END LOOP;
				
END;
$$;

-- 2. LOOP + EXIT WHEN afficher le Xeme tour et les dates jusqu'en 1980

DO $$
DECLARE
	v_annee INT:= extract(YEAR FROM CURRENT_DATE);
BEGIN
	LOOP
		EXIT WHEN v_annee = 1980;
		RAISE NOTICE '%', v_annee;
		v_annee := v_annee - 1;
	END LOOP;
				
END;
$$;


--3. FOR numerique + REVERSE ( 1 a 5 pui 5 a 1)

DO $$
DECLARE
	v_i INT:= 1 ;
BEGIN
	FOR v_i IN 1..5 LOOP
		RAISE nOTICE '%', v_i;
	END LOOP;


	FOR v_i IN reverse 5..1 LOOP
	RAISE nOTICE '%', v_i;
	END LOOP;
	
END;
$$;


DO $$
DECLARE
	v_i INT:= 1 ;
BEGIN
	FOR v_i IN v_i..5 LOOP
		RAISE nOTICE '%', v_i;
	END LOOP;


	FOR v_i IN reverse 5..v_i LOOP
	RAISE nOTICE '%', v_i;
	END LOOP;
	
END;
$$;

-- 4. CONTINUER WHEN (print les modules de 3 jusque 20)


DO $$
DECLARE
	v_i INT:= 1 ;
BEGIN
	FOR v_i IN 1..20 LOOP
		CONTINUE WHEN v_i % 3 <> 0;
		RAISE nOTICE '%', v_i;
	END LOOP;


	-- FOR v_i IN reverse 5..v_i LOOP
	-- RAISE nOTICE '%', v_i;
	-- END LOOP;
	
END;
$$;


--5. FOR sur une reguete Print toutes les infos employes 
--nom prenom, hyperdate et iere dans une table


CREATE TABLE emp (
nom TEXT,
PRENOM TEXT,
EMBOCHE DATE
)


DO $$
DECLARE
	employee RECORD;
BEGIN
	FOR employee in SELECT first_name, last_name, hire_date FROM employees LOOP 
		INSERT INTO emp VALUES(employee.first_name, employee.last_name, employee.hire_date);
	END LOOP;


	-- FOR v_i IN reverse 5..v_i LOOP
	-- RAISE nOTICE '%', v_i;
	-- END LOOP;
	
END;
$$;

SELECT * FROM emp

----------------------------------------------------------------
DROP TABLE IF EXISTS dates_depui1980;
CREATE TABLE dates_depui1980 (
DATE_full DATE,
Date_YYYY_MM TEXT
);

DO $$
DECLARE
	v_date date:= CURRENT_DATE;
BEGIN
	LOOP
		
		EXIT WHEN v_date = '1980-01-01';
		--INSERT INTO dates_depui1980 VALUES(v_date, DATE_TRUNC('month', v_date)::text, 2 );
		INSERT INTO dates_depui1980 VALUES(v_date, to_char(v_date, 'YYYY-MM'));

		v_date := v_date - 1;
	END LOOP;
				
END;
$$;

SELECT * 
FROM dates_depui1980

-----------------------------------------------------------------------------------------------------------

WITH ventes_par_jour AS (
	SELECT SUM(quantity) as total, da.DATE_full as order_date
	FROM orders as o
	LEFT JOIN order_details as d on d.order_id = o.order_id
	right join dates_depui1980 as da on da.DATE_full = o.order_date
	--on D.order_id= O.order_id
	WHERE extract(YEAR FRom da.DATE_full) between 1997 and 1998
	GROUP BY order_date, DATE_full
	)
	
	SELECT *, 
	avg(total) over (order by order_date rows BETWEEN 3 preceding and 1 following) as MM
FROM ventes_par_jour

------------------------------------------------------------------function---------------------------------

SELECT generate_series('1980-01-01'::date, CURRENT_DATE, '1 day');

------------------------------------------------------------------------------------------

-- 1 fonction scalaire qui returne le 
---nombre total de produits vendue avec un id from details

CREATE OR REPLACE FUNCTION get_total_products(v_product_id INT)
RETURNS INT
AS $$
DECLARE V_total INT;
BEGIN
	SELECT sum(quantity) INTO v_total FROM order_details as D WHERE D.product_id = v_product_id;
	RETURN v_total;
end;
$$ LANGUAGE plpgsql;

SELECT sum(quantity) 
FROM order_details WHERE product_id = 8



SELECT get_total_products(8)

SELECT *, get_total_products(product_id) as total_vendu
FROM products;
-------------------------------------------------------------------------


--3. FONCTION tabulare (RETURN QUERY° qui donne les commandes detaillees en focntion 
---) d'une anee en parametres (get_orders_for_a_specific_year_and_category

CREATE OR REPLACE FUNCTION get_orders_for_year_and_cat_(v_annee INT, v_category INT DEFAULT 1)
RETURNS TABLE(
annee date,
product_id products.product_id%type,
quantite order_details.quantity%type
)
AS $$
BEGIN
	RETURN QUERY
	SELECT extract(year FROM order_date) as annee, d.product_id, d. quantity
	FROM orders as o
	join order_details as D on o.order_id =d.order_id
	join products as p on p.product_id = d.product_id
	WHERE
		extract(YEAR from order_date) = v_annee AND
		p.category_id = v_category;
END
$$ LANGUAGE plpgsql;


SELECT get_orders_for_year_and_cat_(1988, 1)
-- SELECT extract(year FROM order_date) as annee, d.product_id, d. quantity
-- FROM orders as o
-- join order_details as D on o.order_id =d.order_id
-- join products as p on p.product_id = d.product_id
-- WHERE
-- 	extract(YEAR from order_date) = 1998 AND

-------------------------------copy from Piu--------------------------------------------------

-- 1 fonction scalaire qui retourne le
-- nombre total de produits vendus avec un id from details
CREATE OR REPLACE FUNCTION get_total_products(v_product_id INT)
RETURNS INT
AS $$
DECLARE v_total INT;
BEGIN
    SELECT SUM(quantity) INTO v_total FROM order_details AS D WHERE D.product_id = v_product_id;
    RETURN v_total;
END;
$$ LANGUAGE plpgsql;

SELECT get_total_products(8);

SELECT , get_total_products(product_id) AS total_vendu
FROM products;

--3. Fonction tabulaire (RETURN QUERY) qui donne les commandes detaillées en fonction
-- d'une année en paramètres (get_orders_for_a_specific_year_and_category)
CREATE OR REPLACE FUNCTION get_orders_for_year_and_cat__(v_annee INT, v_category INT DEFAULT 1)
RETURNS TABLE(
    année INT,
    product_id products.product_id%type,
    quantité order_details.quantity%type
    )
AS $$
BEGIN

    RETURN QUERY
    SELECT extract(YEAR FROM order_date) :: INT AS année, D.product_id, D.quantity
    FROM orders AS O
    LEFT JOIN order_details AS D ON O.order_id = D.order_id
    LEFT JOIN products AS P ON P.product_id = D.product_id
    WHERE
        extract(YEAR FROM order_date) = v_annee AND
        P.category_id = v_category;
END
$$ LANGUAGE plpgsql;
SELECT * FROM get_orders_for_year_and_cat__(1998, 1)
-- 	p.category_id = 1;

    SELECT extract(YEAR FROM order_date) :: INT AS année, D.product_id, D.quantity
    FROM orders AS O
    LEFT JOIN order_details AS D ON O.order_id = D.order_id
    LEFT JOIN products AS P ON P.product_id = D.product_id