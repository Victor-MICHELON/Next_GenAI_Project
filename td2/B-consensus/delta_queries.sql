-- TD 2, étape 2 (binôme B) : requêtes de diagnostic delta sur td1/data/boutique.sqlite.
-- Lecture seule : uniquement des SELECT.
--   sqlite3 -readonly td1/data/boutique.sqlite < td2/B-consensus/delta_queries.sql

-- ---------------------------------------------------------------------------
-- C09 : clients qui ont exactement 25 ans le 2026-09-26, avec le CA HT de toutes
-- leurs commandes. Les deux requêtes fautives (qwen, cohere) renvoient 0 : le
-- delta est donc l'ensemble des lignes comptées par la référence.
-- Somme attendue = 487980 = référence C09 - 0.
-- ---------------------------------------------------------------------------
SELECT c.customer_id,
       c.birth_date,
       COUNT(*)                            AS nb_lignes_commande,
       SUM(o.quantity_product * p.price)   AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product   p ON o.product_id  = p.product_id
WHERE c.birth_date >  date('2026-09-26', '-26 years')   -- né après le 2000-09-26
  AND c.birth_date <= date('2026-09-26', '-25 years')   -- né au plus tard le 2001-09-26
GROUP BY c.customer_id, c.birth_date
ORDER BY c.birth_date;

-- Contrôle : somme du delta, et écart en centimes avec la valeur fausse partagée (0).
SELECT SUM(o.quantity_product * p.price)       AS delta_cents,
       487980 - SUM(o.quantity_product * p.price) AS ecart_restant
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product   p ON o.product_id  = p.product_id
WHERE c.birth_date >  date('2026-09-26', '-26 years')
  AND c.birth_date <= date('2026-09-26', '-25 years');

-- ---------------------------------------------------------------------------
-- C10 (cas secondaire) : lignes de commande où le client a exactement 25 ans à la
-- date de la commande (référence) MAIS que la requête fautive partagée par qwen et
-- dots (écart d'années civiles = 25 ET anniversaire déjà passé) ne compte pas.
-- Somme attendue = 558980 - 119410 = 439570.
-- ---------------------------------------------------------------------------
SELECT c.customer_id,
       c.birth_date,
       o.order_id,
       o.date,
       o.quantity_product * p.price AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product   p ON o.product_id  = p.product_id
WHERE c.birth_date <= date(o.date, '-25 years')          -- condition de référence
  AND c.birth_date >  date(o.date, '-26 years')
  AND NOT (                                              -- exclue par qwen / dots
        (CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER)) = 25
    AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)
  )
ORDER BY c.customer_id, o.date;
