# TD 1, lot du rôle A : `groq:openai/gpt-oss-120b` sur C01 à C20

Opérateur : Bertrand Maigre (membre A). Date : 21 octobre 2026. Branche : `bertrand`.

## Avant le lancement

- Les hash de la base et des CSV sont identiques à `data/manifest.json` (`verify-data.py`, `check_access.py --no-network`).
- Les vingt références sont celles de `reference-td1.csv`, calculées par deux méthodes (SQL et recalcul Python sur les CSV) et validées par le corrigé du prof.
- Avant les appels, l'opérateur a vérifié que les références étaient validées, que c'était le tour du sous-groupe et que le quota du compte couvrait le lot.
- Fichiers du kit non modifiés : squelette, `modeles-autorises.json`, `schema.sql`, `questions-td1.json`.

## Paramètres utilisés

Lus dans `modeles-autorises.json` et dans le squelette, sans changement :

| Élément | Valeur |
|---|---|
| Endpoint | `https://api.groq.com/openai/v1/chat/completions` |
| Corps | `model=openai/gpt-oss-120b`, `temperature=0`, `max_completion_tokens=1024`, `reasoning_effort=low` |
| Règles du lot | 3 s entre deux requêtes, timeout de 45 s, au plus un retry par cellule |
| Prompt | `SYSTEM_PROMPT` et `USER_PROMPT_TEMPLATE` de `skeleton-multi-llm-en.py`, non modifiés (voir `prompts/prompt-experience-td1.md`) |

Commande lancée par l'opérateur dans son terminal. La clé est chargée avec `read -gsx` et n'est jamais écrite dans un fichier.

```fish
python3 skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-A.jsonl --out traces-A.csv
```

## Compteurs

| Compteur | Valeur |
|---|---:|
| Appels initiaux (cellules) | 20 |
| Retries | 0 |
| Erreurs d'accès | 0 |
| Contrôles d'accès pendant ce lot | 0 (les lancements de `check_access.py` sont comptés à part) |
| Quota Groq avant le lot | Non relevé |
| Usage de la clé Groq après le lot | 23 appels sur 24 h sur la clé `my-API` (console, 21 octobre 2026 à 14:53 heure locale : [capture](evidence/role-A/groq-api-keys-2026-10-21.png)). Ce compteur couvre tous les modèles appelés avec cette clé, contrôles d'accès compris : ce n'est pas un chiffre propre au 120B |
| Limites Groq du modèle (RPD, TPD, RPM, TPM) | Non relevées |

## Résultats

20/20 `correct` à la première tentative, toutes les lignes en `nature = real`, HTTP 200, `model_returned = openai/gpt-oss-120b`. Appels de 12:40:18 à 12:41:33 UTC. Chaque trace porte l'empreinte du prompt du kit et la référence de `reference-td1.csv`. `traces-A.csv` et `state-A.jsonl` concordent champ par champ.

| Famille | Correct / évalué |
|---|---:|
| Période seule (C01 C04 C05 C06 C07 C20) | 6/6 |
| Âge à une date de référence (C02 C08 C09 C11) | 4/4 |
| Âge au moment de la commande (C10) | 1/1 |
| Liste de produits (C03 C12 C13 C14) | 4/4 |
| Combinées (C15 à C19) | 5/5 |

On a lu le SQL, pas seulement le verdict. L'âge révolu est calculé au mois et au jour, soit avec des bornes `date(D, '-25 years')` / `date(D, '-26 years')`, soit avec une différence d'années corrigée par `strftime('%m-%d')`. Pour l'âge à la commande, la date de commande est comparée à `birth_date + 25 years` et `+ 26 years`. Les périodes utilisent `>=` / `<`. Les cas vides (C06, C14) renvoient 0 grâce à `COALESCE`.

Latence : médiane 907 ms, de 488 à 1888 ms.

## Tokens et coût

| Quantité | Valeur |
|---|---|
| Tokens en entrée | 12 814 |
| Tokens en sortie | 5 157 (au plus 513 par appel, le plafond de 1 024 n'est jamais atteint) |
| Tokens de raisonnement | 3 103, déjà inclus dans les tokens de sortie (pour chaque appel, le raisonnement est inférieur à la sortie), donc pas ajoutés |
| Coût natif | Vide sur toutes les lignes : N/A |
| Coût équivalent API | (12 814 x 0,15 + 5 157 x 0,60) / 1 000 000 = 0,0050 USD HT, prix Groq Developer du 5 octobre 2026 (`methode-cout-en.md`) |
| Dépense réelle | N/A : l'opérateur n'a rien payé, mais aucune capture datée du plan ou de la facturation n'est jointe, et la capture de la clé ne montre aucun montant Groq. Passera à 0 USD avec une capture Billing/Plan montrant le plan Free sans moyen de paiement |

## Limites

- Un seul passage de vingt questions sur une seule base : pas de taux d'erreur général ni de classement.
- Aucun client n'est né un 29 février, donc le cas des années bissextiles n'est pas testé ici.
- La température 0 ne garantit pas une sortie identique si on relance.

## Fichiers

`state-A.jsonl` (tentatives brutes en JSONL), `traces-A.csv` (export CSV), les 20 lignes du rôle A dans `model-question-comparison-en.csv` et la ligne `openai/gpt-oss-120b` de `five-model-summary-en.csv`. Les fichiers `traces-demo.*` sont des simulations et ne font pas partie de ces résultats.

## Aide d'IA

Assistant : Claude Code. Il a lu le kit, lancé les vérifications locales, calculé hors ligne les paramètres et les empreintes de prompt, relu les traces et rédigé ce résumé. Il n'a fait aucun appel à un modèle : c'est l'opérateur qui a lancé le lot. Demandes faites, mot pour mot :

> C'est bien à nous. Là on doit faire le rôle A. On a encore des crédits pr API.

> oui. On lance !

> finalise tout ensuite on push
