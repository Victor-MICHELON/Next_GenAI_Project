# Calcul des références du TD 1 - C01 à C20

## Résultat (21 octobre 2026)

On a écrit vingt requêtes SQLite et on les a exécutées sur la base fournie, ouverte en lecture seule. Les vingt résultats entiers sont égaux à un calcul Python séparé, fait directement sur les trois CSV fournis. Aucun appel à Groq ni à OpenRouter n'a été fait pour ce calcul.

Les vingt valeurs ont été validées par le corrigé du prof au premier essai.

- Calcul principal : [compute_references.py](../compute_references.py), une requête SQL par question et un recalcul Python sur les CSV.
- Deuxième calcul, fait de son côté par Bertrand : requêtes dans `scripts/reference_queries.sql`, recalcul CSV dans `scripts/verify_references.py`.
- Références rendues : `reference-td1.csv`, une requête et un montant par question.
- Preuve question par question : `reports/reference-verification.csv`.
- SHA-256 de la base : `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2`.

Les deux calculs donnent les mêmes vingt valeurs. Le texte SQL de `reference-td1.csv` a été reformulé après coup (commit cc79a23). On a vérifié que ses vingt requêtes redonnent exactement les vingt valeurs validées. À cause de cette reformulation, `scripts/verify_references.py` s'arrête dès C01 avec le message « sql existant différent ». Il compare le texte des requêtes, pas les montants.

## Rejouer le calcul

À la racine du dépôt :

```bash
python3 compute_references.py --dry-run
```

Seule la bibliothèque standard est utilisée. Le script calcule chaque question en SQL et en Python, puis affiche OK ou DIFF. Sans `--dry-run`, il n'écrit `reference-td1.csv` que si les vingt questions concordent.

## Conventions et calcul indépendant

Le chiffre d'affaires est la somme de `quantity_product * price` sur les lignes de commande, en centimes d'euro HT, sous forme d'entier. Une commande avec plusieurs produits compte pour chacune de ses lignes. Une période va de `début <= date` à `date < fin`. Le SQL utilise `COALESCE(SUM(...), 0)` pour renvoyer 0 quand rien ne correspond.

Pour avoir 25 ans à une date fixe D, il faut être né dans l'intervalle ]D - 26 ans, D - 25 ans]. On prend toutes les commandes des clients retenus, sauf si la question ajoute une période ou une liste de produits. Pour l'âge au moment de la commande (C10, C18), on retire un an à la différence des années quand l'anniversaire n'est pas encore passé à la date de la commande. Le calcul Python travaille sur des dates du calendrier avec l'âge révolu. Il ne réutilise pas les conditions SQL. Aucun client de la base n'est né un 29 février. C06 et C14 ne sélectionnent aucune ligne et renvoient 0.

On a relu l'interprétation des questions dans `questions-td1.json` et dans la section 1 de `consigne-etudiante-en.md`. Les données sources n'ont pas été modifiées. Ce sont des références calculées : aucune valeur ne vient de la réponse d'un modèle.

## Aide d'IA et validation

Le deuxième calcul (`scripts/`) a été préparé sur la branche de Bertrand avec l'aide de Codex. La demande faite à l'assistant est gardée dans `reports/reference-ai-assistance.md`. Les deux calculs ont été relus et lancés par le groupe, et les vingt valeurs ont été validées par le corrigé du prof avant les lots des modèles.

Si une référence déjà utilisée dans un lot réel devait changer, il faudrait lancer une expérience séparée, avec de nouveaux fichiers d'état et de sortie, et garder les anciennes traces.
