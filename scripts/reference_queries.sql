-- Requêtes de référence C01 à C20. Le chiffre d'affaires est un entier en centimes d'euro HT.
-- Les périodes incluent la borne de début et excluent la borne de fin.
-- Intervalle de naissance pour avoir 25 ans le jour D : ]D - 26 ans, D - 25 ans].
-- C01
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00';
-- C02
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25';
-- C03
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.product_id IN ('a','b','c') AND o.date >= '2026-01-01 00:00:00' AND o.date < '2026-07-01 00:00:00';
-- C04
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2026-01-01 00:00:00' AND o.date < '2026-10-01 00:00:00';
-- C05
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2026-06-01 00:00:00' AND o.date < '2026-06-02 00:00:00';
-- C06
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2025-01-01 00:00:00' AND o.date < '2026-01-01 00:00:00';
-- C07
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2026-05-31 00:00:00' AND o.date < '2026-06-01 00:00:00';
-- C08
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE c.birth_date > '2000-09-24' AND c.birth_date <= '2001-09-24';
-- C09
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE c.birth_date > '2000-09-26' AND c.birth_date <= '2001-09-26';
-- C10
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE CAST(strftime('%Y',o.date) AS INTEGER) - CAST(strftime('%Y',c.birth_date) AS INTEGER) - (strftime('%m-%d',o.date) < strftime('%m-%d',c.birth_date)) = 25;
-- C11
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE c.birth_date > '2000-12-01' AND c.birth_date <= '2001-12-01';
-- C12
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.product_id IN ('a','b','c');
-- C13
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.product_id IN ('a','c') AND o.date >= '2026-04-01 00:00:00' AND o.date < '2026-05-01 00:00:00';
-- C14
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.product_id IN ('a','b','c') AND o.date >= '2026-10-01 00:00:00' AND o.date < '2026-12-01 00:00:00';
-- C15
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00' AND c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25';
-- C16
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE o.product_id IN ('a','b','c') AND c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25';
-- C17
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE o.date >= '2026-01-01 00:00:00' AND o.date < '2026-07-01 00:00:00' AND o.product_id IN ('a','b','c') AND c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25';
-- C18
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE o.date >= '2026-05-01 00:00:00' AND o.date < '2026-06-01 00:00:00' AND CAST(strftime('%Y',o.date) AS INTEGER) - CAST(strftime('%Y',c.birth_date) AS INTEGER) - (strftime('%m-%d',o.date) < strftime('%m-%d',c.birth_date)) = 25;
-- C19
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) JOIN customers c USING(customer_id) WHERE o.date >= '2026-09-01 00:00:00' AND o.date < '2026-10-01 00:00:00' AND o.product_id = 'd' AND c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25';
-- C20
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents FROM orders o JOIN product p USING(product_id) WHERE o.date >= '2026-06-01 00:00:00' AND o.date < '2026-09-01 00:00:00';
