# TD 1 - Comparer cinq modèles sur les mêmes questions

Compte rendu du sous-groupe, séance du 21 octobre 2026.

## 1. Ce qu'on a fait

Le but était de voir quels modèles gratuits savent transformer une question de chiffre d'affaires en une requête SQLite correcte. On a posé les 20 questions C01 à C20 à cinq modèles : `openai/gpt-oss-120b`, `openai/gpt-oss-20b` et `qwen/qwen3.8-27b` sur Groq, `cohere/north-mini-code:free` et `dots-studio/dots-3-note-preview:free` sur OpenRouter. Ça fait 100 cellules, une par couple modèle/question.

On a utilisé `skeleton-multi-llm-en.py` sans changer le prompt : même message système et même template pour tous les modèles. Les 100 lignes de traces ont la même empreinte `prompt_sha256` pour une question donnée, quel que soit le modèle. Température 0, sortie plafonnée (1024 tokens, 1000 pour Qwen), un appel à la fois avec 3 secondes d'écart. Le SQL renvoyé est exécuté dans le bac à sable de `sandbox_sqlite.py`, sur la base ouverte en lecture seule, puis la valeur est comparée à notre référence.

## 2. La référence

On a calculé les 20 références avec [compute_references.py](../compute_references.py), qui fait le calcul de deux façons :

- une requête SQLite par question, exécutée sur `data/boutique.sqlite` en lecture seule ;
- un recalcul en Python pur à partir des trois CSV de `data/`, sans SQL.

Le script n'écrit [reference-td1.csv](../reference-td1.csv) que si les deux méthodes donnent la même valeur pour les 20 questions. Les 20 valeurs ont été confirmées par le corrigé du prof au premier essai.

Les conventions qu'on a appliquées :

- Période : borne de début incluse, borne de fin exclue (`date >= début AND date < fin`). Une commande passée pile à minuit le jour de fin ne compte pas.
- Âge : on prend l'âge révolu, calculé au mois et au jour près. Pour avoir 25 ans le jour D, il faut être né dans l'intervalle ]D - 26 ans, D - 25 ans]. La différence des années seule ne suffit pas : quelqu'un né en décembre 2000 n'a pas encore 25 ans le 25 septembre 2026. Pour C10 et C18, l'âge se calcule à la date de chaque commande et non à une date fixe.
- Produits : on ne garde que les lignes des produits cités (`product_id IN (...)`).
- Montant : `SUM(quantity_product * price)` en centimes HT. Quand rien ne correspond, on renvoie 0 et pas NULL (`COALESCE(..., 0)`). C'est le cas de C06 et C14.

## 3. Résultats

Le tableau croisé modèles x questions est dans [pivot-td1.md](../pivot-td1.md). Il est généré depuis [model-question-comparison-en.csv](../model-question-comparison-en.csv), qui contient une ligne finale par cellule.

| Modèle | Correct | incorrect | SQL invalide ou rejeté |
|---|---:|---:|---:|
| groq `openai/gpt-oss-120b` | 20/20 | 0 | 0 |
| groq `openai/gpt-oss-20b` | 18/20 | 2 | 0 |
| openrouter `dots-studio/dots-3-note-preview:free` | 14/20 | 6 | 0 |
| groq `qwen/qwen3.8-27b` | 13/20 | 6 | 1 |
| openrouter `cohere/north-mini-code:free` | 12/20 | 7 | 1 |

Au total, 77 cellules sur 100 sont correctes. Aucun accès n'a été refusé et aucune cellule n'est restée non exécutée. Ces scores viennent d'un seul passage de 20 questions sur une seule base : ce n'est pas un classement général des modèles.

Le résumé par modèle (index public, prix d'une route payante, résultats par famille) est dans [five-model-summary-en.csv](../five-model-summary-en.csv).

## 4. Échecs et causes

L'analyse cellule par cellule est dans [notes/echecs-td1.md](../notes/echecs-td1.md). Pour chaque échec, on y donne le SQL, la valeur, la référence et une cause qu'on peut lire dans le SQL ou dans le message d'erreur. Les traces brutes sont [traces-A.csv](../traces-A.csv) à [traces-E.csv](../traces-E.csv), les fichiers d'état `state-A.jsonl` à `state-E.jsonl`, et la fusion [traces-td1.csv](../traces-td1.csv) faite avec [merge_traces.py](../merge_traces.py).

Échecs par famille, sur les 5 modèles :

| Famille | Échecs |
|---|---:|
| période | 0 / 30 cellules |
| âge à une date de référence | 8 / 20 |
| âge au moment de la commande | 3 / 5 |
| liste de produits | 1 / 20 |
| combinées | 11 / 25 |

On a remarqué que presque tout se joue sur l'âge. Sur les 23 échecs, 21 viennent de la convention d'âge. Dans 7 cas, le modèle fait la différence des années au lieu de calculer l'âge révolu. Dans 2 cas, il calcule l'âge à la date de commande alors que la question donne une date de référence. Dans les autres, les bornes sur `birth_date` sont mal posées : par exemple, `gpt-oss-20b` sur C02 cherche des clients nés entre 2025 et 2026.

Les questions ratées par le plus de modèles sont C09, C10, C15 et C17, avec 3 modèles sur 5 en échec. Toutes contiennent un filtre d'âge. Les filtres de période et de produits passent presque partout, même quand ils sont combinés.

Les deux échecs qui ne viennent pas de l'âge :

- Qwen, C13, `sql_rejected` : la réponse commence par un bloc ```` ```sql ```` jamais refermé. L'extracteur ne le retire pas et le bac à sable refuse un texte qui ne commence pas par `SELECT`. Le SQL dans le bloc avait l'air correct, mais on ne peut pas le noter.
- Cohere, C10, `sql_invalid` : une parenthèse en trop (13 ouvrantes pour 12 fermantes), d'où une erreur de syntaxe SQLite. En plus, la requête faisait elle aussi la différence des années.

## 5. Limites

- Retries : aucun. Chaque cellule a une seule tentative (`attempts` = 1 partout).
- Accès refusés : aucun. Toutes les réponses sont en HTTP 200. On n'a donc pas d'exemple réel d'échec d'accès dans ce lot.
- Mesures manquantes :
  - `cost_native` est vide sur les 60 lignes Groq : Groq ne le renvoie pas, donc on n'a aucun coût mesuré pour ces trois modèles. Sur OpenRouter, il vaut 0 sur les 40 lignes, puisque ce sont des routes `:free`.
  - `tokens_reasoning` est vide sur les 20 lignes Qwen, lancé avec `reasoning_effort` à `none`.
  - On a laissé ces cases vides, sans les remplacer par 0.
- Natures :
  - les 100 lignes de [traces-td1.csv](../traces-td1.csv) sont `real` ;
  - il n'y a aucune ligne `replay` ;
  - les 60 lignes de [traces-demo.csv](../traces-demo.csv) sont `simulation`, elles restent dans un fichier à part et n'entrent dans aucun score.
- Trace C, cellule C18 : elle a d'abord été notée `incorrect` contre une référence erronée (286650). Le modèle renvoyait 62480, la valeur de la référence validée. La ligne a été re-notée dans `traces-C.csv` et `state-C.jsonl` (commit 33a097d), sans nouvel appel. La valeur d'origine reste dans l'historique git.
- Index publics et prix :
  - Les prix du résumé viennent de l'étape 2 de `methode-cout-en.md` : route Groq Developer vérifiée le 05/10/2026 pour les trois modèles Groq.
  - Cohere et Dots sont absents du portefeuille du 28/09/2026, donc leur index public est N/A. Leur prix est aussi N/A : `methode-cout-en.md` ne documente aucune route payante du même modèle exact.

## 6. Contributions

On était six pour huit rôles, donc les rôles F à H (contrôle des références, fusion des traces, résumés) ont été partagés entre Jean-Baptiste et Bertrand.

| Membre | Rôle | Ce qu'il a fait |
|---|---|---|
| Bertrand Maigre | A, puis F-H | Lot `groq:openai/gpt-oss-120b` (20/20) et [role-A-run.md](role-A-run.md) ; deuxième calcul des références ; analyse des échecs ([analyze_failures.py](../analyze_failures.py), [notes/echecs-td1.md](../notes/echecs-td1.md)), `model-question-comparison-en.csv` et tableau croisé ; re-notation de la cellule Cohere C18 |
| Victor Michelon | B | Création du dépôt ; lot `groq:openai/gpt-oss-20b` ([traces-B.csv](../traces-B.csv)) |
| Cyprien Avnel | C | Lot `openrouter:cohere/north-mini-code:free` ([traces-C.csv](../traces-C.csv)) |
| Oscar Dujardin | D | Lot `groq:qwen/qwen3.8-27b` ([traces-D.csv](../traces-D.csv)) ; tableau des membres et nettoyage du dépôt |
| Héloïse Moynot | E | Lot `openrouter:dots-studio/dots-3-note-preview:free` ([traces-E.csv](../traces-E.csv)) et premières causes d'échec ([model-question-comparison-E.csv](../model-question-comparison-E.csv)) |
| Jean-Baptiste Pasteau | F-H | Calcul des 20 références ([compute_references.py](../compute_references.py)) ; fusion des traces ([merge_traces.py](../merge_traces.py)) ; résumé des cinq modèles ([fill_summary.py](../fill_summary.py)) ; prompt, README et ce compte rendu |

## 7. Utilisation d'outils d'IA

On a utilisé des assistants de code (Claude Code et Codex) pour nous aider à écrire les scripts, par exemple `compute_references.py` et `merge_traces.py`. On a relu, lancé et vérifié chaque script nous-mêmes. Aucune valeur de référence ne vient d'un modèle : elles sont toutes calculées sur la base.

## 8. Pour le TD 2

- Lire [atelier-vote.py](../atelier-vote.py) et préparer la règle de vote k-sur-n à partir des traces qu'on a gardées, sans nouvel appel.
- Regarder en priorité C09, C10, C15 et C17. Plusieurs modèles s'y trompent, et il faut voir si deux d'entre eux tombent d'accord sur la même valeur fausse. Dans ce cas, le vote doit le signaler au lieu de choisir une valeur.
- Penser au routage : d'après ce lot, les questions de période et de produits passent avec tous les modèles, alors que les questions d'âge demandent `gpt-oss-120b` ou un contrôle en plus.
