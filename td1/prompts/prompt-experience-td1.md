# Prompt de l'expérience TD 1

Copie exacte de `SYSTEM_PROMPT` et `USER_PROMPT_TEMPLATE` de [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py), extraite directement du script.

On n'a pas modifié le prompt. Il est identique pour les 5 modèles (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` sur Groq, `cohere/north-mini-code:free`, `dots-studio/dots-3-note-preview:free` sur OpenRouter).

Comment on l'a vérifié :

- `skeleton-multi-llm-en.py` n'a pas changé depuis le premier commit du dépôt (500bfc6).
- On a recalculé l'empreinte avec `build_prompt` du squelette pour chaque ligne de [traces-td1.csv](../traces-td1.csv) : 100 empreintes sur 100 sont égales à la colonne `prompt_sha256`. Pour une question donnée, les 5 modèles ont donc reçu exactement le même texte.

Le squelette remplace `{schema}` par le contenu de [schema.sql](../schema.sql) (sans les espaces de début et de fin) et `{question}` par le texte de la question dans `questions-td1.json`. L'empreinte est le SHA-256 de `SYSTEM_PROMPT + "
" + message utilisateur`.

## SYSTEM_PROMPT

```text
You write SQLite queries for a small e-commerce database. Reply with exactly one SQLite SELECT statement and nothing else: no explanation, no comments, no markdown other than an optional ```sql fence.
```

## USER_PROMPT_TEMPLATE

```text
Schema (SQLite):
{schema}

Conventions (binding):
- product.price is the unit price in euro cents, excluding VAT (an integer). Revenue excluding VAT is SUM(quantity_product * price), an integer number of cents.
- orders holds order lines: one row per (order_id, product_id). All lines of an order share the same customer_id and the same date.
- orders.date and customers.insert_date are UTC timestamps stored as text 'YYYY-MM-DD HH:MM:SS'. customers.birth_date is a date stored as text 'YYYY-MM-DD'. Compare them as text or with SQLite date functions.
- A period "from S to E" is closed on the left and open on the right: date >= S AND date < E.
- A customer's age on a day D is the number of completed years: someone born on B is N years old on D when the N-th anniversary of B is on or before D and the (N+1)-th anniversary is after D. "Exactly 25 years old" means completed age 25 on that day, computed from month and day, never from the year difference alone.
- Unless the question says "at the time of the order", ages are computed on the reference date given in the question.
- The query must return exactly one row and one column named revenue_cents. When no order line matches, return 0 (use COALESCE), not NULL.
- Use only the tables above. One SELECT statement, nothing else.

Question: {question}
```

## Paramètres d'appel

Ils viennent de `modeles-autorises.json` et du squelette : température 0, `reasoning_effort` à `low` pour les deux gpt-oss et `none` pour Qwen avec `max_completion_tokens` 1024 (1000 pour Qwen), `reasoning` désactivé et `max_tokens` 1024 sur OpenRouter, timeout de 45 s, 3 s entre deux requêtes.
