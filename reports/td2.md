# TD 2 - Le quorum, puis la règle de routage

Compte rendu du sous-groupe, séance du 18 novembre 2026.

Tout ce TD est fait à partir des traces stockées du TD 1 ([traces-td1.csv](../td1/traces-td1.csv), 100 lignes `real`, une par cellule) et de [reference-td1.csv](../td1/reference-td1.csv). Aucun nouvel appel réseau n'a été lancé.

## 1. Étape 1 - Le vote k-sur-n (binôme A)

### 1.1 La méthode

On a complété `Orchestrateur.vote_k_sur_n` dans [skeleton-multi-llm-en.py](../td1/skeleton-multi-llm-en.py). Dans l'ordre :

1. On vérifie que k est une majorité stricte (`n // 2 < k <= n`), sinon `ValueError`. Si on acceptait k = 1 sur n = 3, deux valeurs différentes pourraient chacune « gagner » et le vote ne trancherait plus rien.
2. On refuse les doublons `(provider, model_requested)` avec `ValueError`. Le même modèle interrogé deux fois n'est pas un deuxième avis.
3. Seules les propositions `executed` avec une valeur votent. Une erreur (429, SQL invalide, SQL rejeté) reste comptée dans n mais ne vote pas. Conséquence : une panne rend le quorum plus difficile à atteindre, jamais plus facile.
4. On compte les voix par valeur. Si la valeur la plus soutenue atteint k, on la renvoie avec la liste des modèles d'accord. Sinon on s'abstient : `value = None`, `votes` = le plus grand nombre de voix obtenu, `models = []`.

Comme k est une majorité stricte, il ne peut y avoir au plus qu'une seule valeur à k voix, donc pas d'ambiguïté quand il y a consensus. En cas d'égalité sous le seuil (C10 en 3-sur-5, 2 contre 2), on s'abstient de toute façon, le choix entre les ex aequo n'a pas d'effet.

La méthode ne reçoit jamais la référence : la comparaison avec `reference-td1.csv` se fait après la décision.

### 1.2 Les quatre exemples synthétiques

`python3 atelier-vote.py` (valeurs synthétiques, pas des résultats sur la base) :

| Exemple | Valeurs | Décision 2-sur-3 | = réf. (100) |
|---|---|---|:-:|
| agreement | 100, 100, 120 | consensus 100 (2 voix) | oui |
| disagreement | 100, 110, 120 | abstention (max 1) | - |
| unavailable | 100, erreur, erreur | abstention (max 1) | - |
| wrong consensus | 0, 0, 100 | consensus 0 (2 voix) | **non** |

Le dernier exemple montre la limite du vote : deux modèles d'accord sur une mauvaise valeur gagnent quand même. Le vote ne vérifie pas la justesse, il mesure seulement l'accord.

On a aussi testé à la main les cas de refus : k = 1 et k = 4 sur n = 3 lèvent `ValueError`, un doublon aussi, trois erreurs donnent une abstention à 0 voix, et une proposition `error` qui porte quand même une valeur n'est pas comptée.

Sur les vraies traces, `python3 atelier-vote.py --traces traces-td1.csv --case C02` donne un consensus sur 590320 avec gpt-oss-120b et qwen3.8-27b (cohere répond 321340), ce qui correspond à la référence.

### 1.3 Comparaison 2-sur-3 / 3-sur-5 sur les 20 questions

Le tableau est produit par [compare_quorum.py](../td2/A-quorum/compare_quorum.py) (export CSV : [comparaison-2sur3-3sur5.csv](../td2/A-quorum/comparaison-2sur3-3sur5.csv)). Le script réutilise `proposals_for` d'`atelier-vote.py` : dernière tentative de chaque membre, un verdict autre que `correct`/`incorrect` devient une `error` sans voix.

- **2-sur-3** : panel fixe `groq:openai/gpt-oss-120b`, `openrouter:cohere/north-mini-code:free`, `groq:qwen/qwen3.8-27b`, k = 2.
- **3-sur-5** : les cinq modèles du TD 1 (les trois du panel + `groq:openai/gpt-oss-20b` et `openrouter:dots-studio/dots-3-note-preview:free`), k = 3.

Abréviations dans la dernière colonne : 120b, cohere, qwen, 20b, dots.

| Question | Référence | 2-sur-3 | = réf. | 3-sur-5 | = réf. | Décision change | Valeurs des 5 modèles |
|---|---:|---|:-:|---|:-:|:-:|---|
| C01 | 792800 | 792800 (3 voix) | oui | 792800 (5 voix) | oui |  | 120b=792800, cohere=792800, qwen=792800, 20b=792800, dots=792800 |
| C02 | 590320 | 590320 (2 voix) | oui | 590320 (3 voix) | oui |  | 120b=590320, cohere=321340, qwen=590320, 20b=0, dots=590320 |
| C03 | 936350 | 936350 (3 voix) | oui | 936350 (5 voix) | oui |  | 120b=936350, cohere=936350, qwen=936350, 20b=936350, dots=936350 |
| C04 | 2826250 | 2826250 (3 voix) | oui | 2826250 (5 voix) | oui |  | 120b=2826250, cohere=2826250, qwen=2826250, 20b=2826250, dots=2826250 |
| C05 | 38480 | 38480 (3 voix) | oui | 38480 (5 voix) | oui |  | 120b=38480, cohere=38480, qwen=38480, 20b=38480, dots=38480 |
| C06 | 0 | 0 (3 voix) | oui | 0 (5 voix) | oui |  | 120b=0, cohere=0, qwen=0, 20b=0, dots=0 |
| C07 | 13970 | 13970 (3 voix) | oui | 13970 (5 voix) | oui |  | 120b=13970, cohere=13970, qwen=13970, 20b=13970, dots=13970 |
| C08 | 605580 | 605580 (2 voix) | oui | 605580 (4 voix) | oui |  | 120b=605580, cohere=0, qwen=605580, 20b=605580, dots=605580 |
| C09 | 487980 | 0 (2 voix) | **NON** | abstention (max 2) | - | **oui** | 120b=487980, cohere=0, qwen=0, 20b=487980, dots=47900 |
| C10 | 558980 | abstention (max 1) | - | abstention (max 2) | - |  | 120b=558980, cohere=sql_invalid, qwen=119410, 20b=558980, dots=119410 |
| C11 | 446690 | 446690 (2 voix) | oui | 446690 (3 voix) | oui |  | 120b=446690, cohere=0, qwen=446690, 20b=322160, dots=446690 |
| C12 | 1666490 | 1666490 (3 voix) | oui | 1666490 (5 voix) | oui |  | 120b=1666490, cohere=1666490, qwen=1666490, 20b=1666490, dots=1666490 |
| C13 | 107740 | 107740 (2 voix) | oui | 107740 (4 voix) | oui |  | 120b=107740, cohere=107740, qwen=sql_rejected, 20b=107740, dots=107740 |
| C14 | 0 | 0 (3 voix) | oui | 0 (5 voix) | oui |  | 120b=0, cohere=0, qwen=0, 20b=0, dots=0 |
| C15 | 168680 | abstention (max 1) | - | abstention (max 2) | - |  | 120b=168680, cohere=314020, qwen=0, 20b=168680, dots=51810 |
| C16 | 376740 | 376740 (2 voix) | oui | 376740 (3 voix) | oui |  | 120b=376740, cohere=376740, qwen=367050, 20b=376740, dots=1447730 |
| C17 | 258180 | abstention (max 1) | - | abstention (max 2) | - |  | 120b=258180, cohere=371990, qwen=248490, 20b=258180, dots=80190 |
| C18 | 62480 | 62480 (3 voix) | oui | 62480 (4 voix) | oui |  | 120b=62480, cohere=62480, qwen=62480, 20b=62480, dots=39580 |
| C19 | 1990 | abstention (max 1) | - | 1990 (3 voix) | oui | **oui** | 120b=1990, cohere=13930, qwen=83580, 20b=1990, dots=1990 |
| C20 | 1106090 | 1106090 (3 voix) | oui | 1106090 (5 voix) | oui |  | 120b=1106090, cohere=1106090, qwen=1106090, 20b=1106090, dots=1106090 |

Bilan :

| | Consensus | dont justes | dont faux | Abstentions |
|---|---:|---:|---:|---:|
| 2-sur-3 | 16 | 15 | 1 (C09) | 4 (C10, C15, C17, C19) |
| 3-sur-5 | 16 | 16 | 0 | 4 (C09, C10, C15, C17) |

Le nombre de réponses données est le même, mais le 3-sur-5 n'en donne aucune fausse : il échange le faux consensus de C09 contre une bonne réponse sur C19.

### 1.4 Les questions où la décision change

**C09 : faux consensus en 2-sur-3, abstention en 3-sur-5.** Référence 487980 (clients ayant exactement 25 ans le 2026-09-26). Dans le panel, cohere et qwen répondent tous les deux 0 (verdict `incorrect`, HTTP 200) et battent gpt-oss-120b (487980, `correct`). Le vote rend donc 0 avec 2 voix, une valeur fausse avec l'apparence d'un accord. En regardant le SQL, les deux modèles ne font même pas la même erreur :
- cohere calcule un « âge » égal à l'année de naissance plus un ajustement (`CAST(SUBSTR(c.birth_date,1,4) AS INTEGER) + CASE ... END = 25`), ce qui ne peut jamais valoir 25, et en plus il ajoute un filtre `o.date >= '2026-09-26'` qui n'est pas dans la question ;
- qwen calcule l'âge à la date de chaque commande (`strftime('%Y', o.date) - strftime('%Y', c.birth_date) = 25`) au lieu de la date de référence.

Les deux filtres ne gardent aucune ligne, et `COALESCE(..., 0)` transforme ce vide en 0. Le 0 est une valeur « attracteur » : deux requêtes fausses de manières différentes tombent dessus. En 3-sur-5, gpt-oss-20b répond aussi 487980 (bornes `birth_date > '2000-09-26' AND <= '2001-09-26'`, `correct`) et dots répond 47900. On a donc 2 voix pour 487980, 2 voix pour 0, 1 pour 47900 : personne n'atteint 3, abstention. Le 3-sur-5 ne trouve pas la bonne réponse, mais il évite de livrer une valeur fausse.

**C19 : abstention en 2-sur-3, consensus juste en 3-sur-5.** Référence 1990 (produit d, septembre 2026, clients de 25 ans le 2026-09-25). Dans le panel, les trois valeurs sont différentes : gpt-oss-120b 1990 (`correct`), cohere 13930 (`incorrect`, il compare le jour et le mois avec des `substr` mal placés), qwen 83580 (`incorrect`, il compare une année avec une date complète, `strftime('%Y', ...) <= '2026-09-25'`). Max 1 voix, donc abstention. En 3-sur-5, gpt-oss-20b (bornes sur `birth_date`) et dots (comparaison année + mois-jour) trouvent aussi 1990, avec deux SQL différents de celui de 120b. On atteint 3 voix sur 5 : consensus sur la bonne valeur.

### 1.5 Les questions où seule la marge change

La décision reste la même, mais le passage à 5 modèles modifie le nombre de voix :

- **C13** : qwen a le verdict `sql_rejected` (HTTP 200, sa réponse commence par un bloc ```` ```sql ```` que le bac à sable refuse comme `not_select`). Il reste dans n sans voter. En 2-sur-3, le consensus tient à 2 voix sur 2 votants : une erreur de plus (un 429 sur cohere par exemple) et on passait à l'abstention. En 3-sur-5, 4 voix sur 4 votants, il y a de la marge.
- **C10** : cohere est en `sql_invalid` (`syntax_error near ")"`). En 2-sur-3, 120b (558980) et qwen (119410) sont seuls à voter : abstention à 1 voix. En 3-sur-5, c'est une égalité 2 contre 2 : 558980 (120b, 20b, juste) contre 119410 (qwen et dots, la même valeur fausse). Abstention dans les deux cas, mais le 3-sur-5 révèle un deuxième accord sur une valeur fausse : si dots et qwen avaient été rejoints par un troisième modèle, on aurait eu un faux consensus. C'est le genre de cas que le binôme B regarde.
- **C15 et C17** : gpt-oss-20b rejoint 120b sur la bonne valeur (168680, 258180), le max passe de 1 à 2 voix, ça reste sous le seuil de 3.
- **C02 et C11** : consensus juste dans les deux cas, mais à 3 voix sur 5 c'est le minimum. Sur C02, 20b répond 0 et cohere 321340 ; sur C11, cohere 0 et 20b 322160.
- **C08, C16, C18** : la marge augmente (C08 passe de 2 à 4 voix), pas de changement de décision.

Aucun HTTP 429 dans nos traces : les 100 lignes sont en HTTP 200. Les deux seules propositions sans vote viennent du SQL (`sql_invalid` sur C10, `sql_rejected` sur C13), pas d'une indisponibilité du fournisseur.

### 1.6 Ce qu'on en retient

- Le vote ne prouve pas la justesse. C09 en 2-sur-3 est un vrai faux consensus, sur nos propres traces, et la valeur fautive est 0, celle qu'on obtient dès qu'un filtre d'âge est trop restrictif.
- Le 3-sur-5 a été plus sûr ici (0 réponse fausse contre 1), sans perdre de couverture (16 réponses dans les deux cas). Mais il coûte deux appels de plus par question, et il n'est meilleur que parce que gpt-oss-20b est souvent juste. gpt-oss-120b et gpt-oss-20b sont de la même famille (OpenAI) : sur C09, C15, C17 et C19 ils sont d'accord entre eux. Si les deux s'étaient trompés ensemble, ils auraient apporté deux voix fausses d'un coup.
- Les questions à filtre d'âge (C09, C10, C15, C17, C19) sont celles où le vote hésite ou se trompe. Sur les questions de période et de produits, les deux quorums sont toujours d'accord avec la référence.
- Limite : 20 questions, une seule tentative par cellule, une seule base. On ne peut pas en tirer de taux d'erreur général du vote.

## 2. Étape 2 - Le faux consensus (binôme B)

Tout est rejouable sans réseau ; la base est ouverte en lecture seule :

```
python td2/B-consensus/consensus_errone.py          # recherche, votes, delta, DEMO-VOTE
sqlite3 -readonly td1/data/boutique.sqlite < td2/B-consensus/delta_queries.sql
```

Fichiers : [consensus_errone.py](../td2/B-consensus/consensus_errone.py), [delta_queries.sql](../td2/B-consensus/delta_queries.sql).

### 2.1 Recherche dans nos traces

On a pris la dernière tentative de chaque cellule de `td1/traces-td1.csv` (100 cellules réelles, 5 modèles × 20 questions), puis on a regroupé les verdicts `incorrect` par (question, valeur). Deux valeurs fausses sont partagées par au moins deux modèles. On a donc travaillé sur **nos propres traces**, et le cas historique DEMO-SQL-C11 n'a pas servi.

| Question | Valeur fausse partagée | Modèles d'accord | Référence (`reference-td1.csv`) | Panel fixe 2-sur-3 | Quorum 3-sur-5 |
|---|---|---|---|---|---|
| **C09** (cas principal) | 0 | qwen/qwen3.8-27b (Groq), cohere/north-mini-code:free (OpenRouter) | 487980 | **consensus 0, 2 voix : faux consensus** | abstention (2 voix pour 0, 2 pour 487980, 1 pour 47900) |
| C10 (cas secondaire) | 119410 | qwen/qwen3.8-27b (Groq), dots-studio/dots-3-note-preview:free (OpenRouter) | 558980 | abstention (max 1, cohere en `sql_invalid`) | abstention (2 contre 2) |

On a d'abord compté les voix à la main, puis on les a vérifiées avec le `vote_k_sur_n` du binôme A (script `consensus_errone.py`, qui reprend `proposals_for` d'`atelier-vote.py`). La référence n'est lue qu'après la décision.

### 2.2 C09 : le faux consensus qui gagne le 2-sur-3

Question C09 : CA HT, en centimes, de toutes les commandes des clients qui ont exactement 25 ans le 2026-09-26. Un client a 25 ans ce jour-là s'il est né entre le 2000-09-27 et le 2001-09-26 inclus, c'est-à-dire `birth_date > '2000-09-26' AND birth_date <= '2001-09-26'`. La référence vaut 487980, et on la retrouve en ré-exécutant la requête de `reference-td1.csv`.

Le panel fixe est {gpt-oss-120b, north-mini-code, qwen3.8-27b} avec k = 2. qwen et cohere répondent 0 (HTTP 200, `incorrect`), et 120b répond 487980 (`correct`). Le vote rend **0 avec 2 voix** : une valeur fausse qui a l'apparence d'un accord. En 3-sur-5, gpt-oss-20b rejoint 120b sur 487980 et dots répond 47900. Aucune valeur n'atteint 3 voix, donc le quorum s'abstient au lieu d'inventer une valeur.

**Les deux requêtes fautives, telles que renvoyées par les modèles :**

```sql
-- qwen/qwen3.8-27b (Groq) -> 0
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE (strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 25
  AND (strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date))
  AND (strftime('%m-%d', o.date) < strftime('%m-%d', date(c.birth_date, '+26 years')));

-- cohere/north-mini-code:free (OpenRouter) -> 0
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE
  (
    CAST(SUBSTR(c.birth_date, 1, 4) AS INTEGER) +
    CASE
      WHEN SUBSTR(c.birth_date, 6, 2) > '09' THEN -1
      WHEN SUBSTR(c.birth_date, 6, 2) = '09' AND SUBSTR(c.birth_date, 9, 2) > '26' THEN -1
      ELSE 0
    END
  ) = 25
  AND o.date >= '2026-09-26 00:00:00' AND o.date < '2026-10-01 00:00:00';
```

**Clauses fautives.** Les deux requêtes arrivent à 0 pour des raisons différentes, et chacune des deux causes suffit à vider l'ensemble des lignes. Nous avons vérifié chaque condition séparément sur `boutique.sqlite` :

- **qwen, avec deux erreurs.**
  1. L'âge est calculé à la date de chaque commande (`o.date`) au lieu de la date de référence 2026-09-26. Il répond donc à la question d'une autre famille (F2b, l'âge au moment de la commande, comme C10).
  2. Surtout, la troisième condition contredit la deuxième. `date(c.birth_date, '+26 years')` garde le même mois et le même jour que `birth_date`. Aucun client n'est né un 29 février : nous l'avons vérifié, avec 0 client sur 59 dont le jour-mois change. La conjonction `md(o) >= md(b) AND md(o) < md(b)` est donc toujours fausse. Mesure : la condition 1 seule garde 72 lignes, les conditions 1 et 2 en gardent 14, et les conditions 1, 2 et 3 n'en gardent **aucune**.
- **cohere, avec deux erreurs.**
  1. L'expression censée calculer l'âge oublie de soustraire l'année de naissance à 2026. `CAST(SUBSTR(birth_date,1,4) AS INTEGER) + ajustement` vaut l'année de naissance (de 1958 à 2006 dans la base), et ne peut jamais valoir 25. Avec `2026 - ...`, la seule condition d'âge donnerait exactement 487980.
  2. Le modèle ajoute un filtre de période qui n'est pas dans la question (`o.date >= '2026-09-26' AND o.date < '2026-10-01'`). La dernière commande de la base date du 2026-09-20 19:24:25, donc cette fenêtre contient 0 commande.
- **Le mécanisme commun est `COALESCE(SUM(...), 0)`.** Un filtre trop restrictif ne produit pas d'erreur : il produit un ensemble vide, et la somme de cet ensemble vide est convertie en 0. Le 0 est une valeur attracteur, sur laquelle des requêtes fausses de manières différentes finissent par se rejoindre. Le vote compte des valeurs, pas des raisonnements, donc deux erreurs indépendantes deviennent deux voix pour la même valeur.

**Requête delta sur `data/boutique.sqlite`.** Elle liste les clients comptés par la référence. Comme la valeur fausse est 0, toutes leurs lignes sont manquées par les requêtes fautives :

```sql
SELECT c.customer_id, c.birth_date,
       COUNT(*) AS nb_lignes_commande,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product   p ON o.product_id  = p.product_id
WHERE c.birth_date >  date('2026-09-26', '-26 years')
  AND c.birth_date <= date('2026-09-26', '-25 years')
GROUP BY c.customer_id, c.birth_date
ORDER BY c.birth_date;
```

| customer_id | birth_date | lignes | revenue_cents |
|---|---|---|---|
| C007 | 2000-11-30 | 18 | 118740 |
| C009 | 2001-03-10 | 9 | 61330 |
| C008 | 2001-05-15 | 11 | 99090 |
| C002 | 2001-09-24 | 6 | 25920 |
| C001 | 2001-09-25 | 18 | 135000 |
| C003 | 2001-09-26 | 6 | 47900 |
| **Total** | | **68** | **487980** |

Le total vaut 487980 − 0 = 487980 centimes : le delta explique **tout** l'écart. Le script le vérifie aussi ligne de commande par ligne de commande, de façon générique. Il remplace le `SUM` de chaque requête fautive par la liste de ses lignes `(order_id, product_id)` et fait la différence d'ensembles avec la référence. On obtient 68 lignes manquées pour 487980 centimes, et 0 ligne ajoutée à tort, pour chacun des deux modèles.

À noter : C003, né le 2001-09-26, a ses 25 ans pile le jour de référence. C'est le cas limite de la borne `<=`. La réponse de dots (47900) correspond exactement à ce seul client : son `strftime(birth_date, '25 years') = '2026-09-26'` ne garde que les clients dont c'est l'anniversaire ce jour-là.

### 2.3 C10 : le faux accord qui ne gagne pas (cas secondaire)

Question C10 : CA HT des commandes passées par des clients qui avaient exactement 25 ans au moment de la commande. La référence vaut 558980. qwen et dots renvoient tous les deux 119410 avec deux SQL différents, mais avec le même raisonnement : l'écart d'années civiles vaut 25 **et** l'anniversaire est déjà passé dans l'année. Cette clause ne couvre qu'une partie de la 25e année : la partie qui tombe dans l'année civile du 25e anniversaire. Elle oublie les commandes passées l'année civile suivante, avant le 26e anniversaire, où l'écart d'années vaut 26 et où le client a pourtant encore 25 ans. La branche `OR` de qwen (écart de 24 et anniversaire pas encore passé, donc 23 ans) n'ajoute aucune ligne.

La requête delta (`delta_queries.sql`, 3e requête) prend les lignes retenues par la référence et non retenues par la clause partagée. Elle renvoie **59 lignes pour 439570 centimes** = 558980 − 119410, sur 4 clients nés en 2000 : C022 (20330), C004 (150260), C005 (150240) et C007 (118740). Ces clients avaient 25 ans en 2026, avant leur anniversaire.

Le vote ne livre pas cette valeur fausse. En 2-sur-3, cohere est en `sql_invalid` et reste dans n sans voter, donc l'abstention se fait à 1 voix. En 3-sur-5, l'égalité est de 2 contre 2. Il manquait **une seule voix** pour que 119410 gagne le 3-sur-5.

### 2.4 Mécanisme illustré : DEMO-VOTE (exemple construit)

Exemple construit par l'énoncé, pas une sortie de modèle. La table jouet `sales` est créée en mémoire et contient une seule ligne (`2026-01-01`, 100). Avec `sale_date > '2026-01-01' AND sale_date < '2026-01-02'`, on obtient 0, parce que la borne de début est exclue et que la vente du 1er janvier disparaît. Avec `>=`, on obtient 100, ce qui est la référence. Le vote 2-sur-3 sur les propositions [0, 0, 100], exécuté avec notre `vote_k_sur_n`, rend un consensus 0 à 2 voix : c'est un faux consensus. On retrouve le même mécanisme que pour C09 : une borne ou un filtre trop strict, un ensemble vide, puis `COALESCE` qui renvoie 0.

### 2.5 Méthode de vérification indépendante et conséquences pour le contrôle

- **Vérification indépendante.** La référence est la requête de `reference-td1.csv`, écrite avec des bornes explicites sur `birth_date` et ré-exécutée sur la base, ce qui redonne 487980. Elle est recoupée par le delta, qui liste ligne par ligne les clients concernés : leur date de naissance permet de vérifier l'âge à la main. Elle est aussi confirmée par 120b et 20b, qui trouvent 487980 avec deux SQL différents.
- **Un accord ne prouve pas la justesse.** Sur C09, le panel 2-sur-3 livre un 0 faux avec deux voix. Le 3-sur-5 s'abstient ici, mais seulement parce que 20b est juste. Sur C10, il manquait une voix pour que le 3-sur-5 se trompe lui aussi.
- **Un 0 ou un ensemble vide doit déclencher un contrôle.** Une valeur 0 issue d'un `COALESCE(SUM(...),0)` doit être vérifiée de façon déterministe avant d'être livrée, par exemple avec un `COUNT(*)` des lignes filtrées, ou en la comparant à la référence. Ce contrôle est particulièrement nécessaire quand le chiffre est montré à un client ou qu'il conditionne un paiement.
- **Les questions d'âge (F2 et F2b) sont celles où les modèles gratuits se trompent ensemble.** Pour le binôme C, cela veut dire qu'aucun modèle gratuit seul ne suffit sur ces familles : la règle doit imposer un quorum et un contrôle déterministe.
- **Limite.** Ces conclusions reposent sur 20 questions, une seule base et une seule tentative par cellule. C'est une hypothèse propre à ce lot, pas un taux d'erreur général.

## 3. Étape 3 - La règle de routage (binôme C)

Ce qu'on a produit :

- la règle d'une page, [td2/C-routing/regle-routage.md](../td2/C-routing/regle-routage.md). Pour chaque famille, elle donne le score TD 1 de chaque modèle, le premier modèle, le contrôle selon l'usage et la conduite à tenir quand le premier modèle est indisponible ;
- le simulateur adapté, [td1/atelier-routage-regle.py](../td1/atelier-routage-regle.py). `RESOURCES` contient nos cinq modèles et les routes payantes Groq Developer. `choose` applique la règle et relit [model-question-comparison-en.csv](../td1/model-question-comparison-en.csv) à chaque lancement : chaque raison (`run`, `defer` ou `abstain`) cite les cellules TD 1 qui la justifient ;
- les sorties du simulateur fourni, [simulateur-avant.jsonl](../td2/C-routing/simulateur-avant.jsonl), et du simulateur adapté, [simulateur-apres.jsonl](../td2/C-routing/simulateur-apres.jsonl) ;
- le rejeu des panels de quorum sur les traces réelles du TD 1, [rejeu-panels-td1.jsonl](../td2/C-routing/rejeu-panels-td1.jsonl).

Les disponibilités, les délais de recharge et les budgets des scénarios sont **simulés**. Les scores et les cellules viennent du lot réel du TD 1. Les coûts sont des équivalents facturés : la dépense réelle du TD est de 0.

### 3.1 Ce que la règle retient

gpt-oss-20b est le premier modèle partout, sauf pour l'âge à une date, où il se trompe sur C02 et C11. Sur cette famille, seul gpt-oss-120b est à 4/4. Le rejeu des panels a guidé deux choix :

- le panel fixe de l'atelier {120b, cohere, qwen} rend un consensus faux sur C09 (0 au lieu de 487980). On en retire cohere, qui est à 0/4 sur l'âge à une date ;
- pour l'âge à la commande, {120b, qwen, dots} rend un consensus faux sur C10 (119410 au lieu de 558980). On passe donc directement au recalcul indépendant : aucun modèle gratuit ne suffit seul sur cette famille.

### 3.2 Pourquoi `choose` prend un abonnement disponible avant d'attendre une route gratuite

Les branches de `choose` dans [atelier-routage.py](../td1/atelier-routage.py) sont testées dans cet ordre :

1. **Capacité incluse disponible** : ressource éligible, `available` et `cash == 0`. On prend le minimum sur la clé `(allocation, level, id)`. `small-free` (allocation 0) passe donc avant `senior-subscription` (allocation 0,04) quand les deux sont libres.
2. **Attente** : ressource éligible, indisponible, `cash == 0`, avec `0 < reset_minutes <= deadline_minutes`. Cette branche n'est prise que si `can_wait` est vrai, et on choisit la recharge la plus proche.
3. **Route payante** : ressource disponible avec `cash <= budget`. On prend le minimum sur la clé `(cash, allocation, id)`.
4. **Abstention**.

Un abonnement disponible remplit la condition de la branche 1 (`cash == 0`), même si son `allocation` est positive. La branche 1 est testée avant la branche 2. L'abonnement passe donc avant toute attente, même quand la route gratuite épuisée se recharge avant l'échéance. On l'a vérifié avec le `choose` d'origine, non modifié ([atelier-routage-priorite.py](../td1/atelier-routage-priorite.py), sortie dans [priorite-abonnement.jsonl](../td2/C-routing/priorite-abonnement.jsonl)) :

| Scénario simulé (difficulté 1, `can_wait`, échéance 120 min) | Décision |
|---|---|
| `small-free` épuisé, recharge dans 30 min ; abonnement disponible | `run` sur `senior-subscription` (cash 0) |
| `small-free` et abonnement épuisés, recharge dans 30 min | `defer` sur `small-free` (réveil dans 30 min) |

Cette priorité se justifie de trois façons :

- l'allocation est déjà payée : l'utiliser n'ajoute aucune dépense (`cash` 0) ;
- la réponse arrive tout de suite, sans retard ;
- une heure de recharge ne prouve pas que la capacité sera revenue. Le docstring le dit lui-même : la disponibilité doit être mesurée à nouveau au réveil, donc attendre fait courir le risque de rater l'échéance.

Il faut inverser la priorité quand consommer l'allocation a un **coût d'opportunité ou un coût réel**. C'est le cas quand le quota d'abonnement est rare et doit être gardé pour les requêtes de niveau 3 que seule la ressource senior sait traiter, quand il est partagé par l'équipe, ou quand son dépassement est facturé. Dans ces situations, une requête de niveau 1 qui peut attendre, avec une recharge certaine bien avant l'échéance, devrait différer sur la route gratuite. Il faudrait alors ajouter au tri de la branche 1 le coût de l'allocation, ou réserver l'abonnement aux requêtes dont la difficulté l'exige.

Notre règle suit la même logique. Elle prend d'abord le modèle éligible suivant en capacité gratuite (gpt-oss-120b si gpt-oss-20b est épuisé), puis elle attend la recharge, puis elle passe par la route payante si un budget est autorisé, et sinon elle s'abstient. Nos routes n'ont pas d'abonnement : le Free de Groq et les routes `:free` d'OpenRouter ne coûtent rien et n'ont pas d'allocation prépayée.

### 3.3 Limites

La règle repose sur un seul passage de 20 questions sur une seule base. C'est une hypothèse de routage pour ce lot, pas un taux d'erreur, pas un classement durable, et pas une garantie du quorum. La famille « âge à la commande » ne repose que sur C10 (et C18 parmi les combinées).

Les sorties de l'étape 3 viennent de l'archive locale du kit (`2026-10-14-students-1`). L'énoncé en ligne est en version `2026-11-18-students-5`. Son `atelier-routage.py`, relu le 18/11/2026, est identique au nôtre.

## 4. Contributions

<TODO>

## 5. Suites

<TODO>
