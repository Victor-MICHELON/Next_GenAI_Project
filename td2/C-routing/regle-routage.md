# Règle de routage du sous-groupe (TD 2, étape 3)

Base : les 100 cellules réelles du TD 1 ([pivot](../../td1/pivot-td1.md), [CSV long](../../td1/model-question-comparison-en.csv)). Coût : équivalent facturé de la route payante du même modèle ([methode-cout-en.md](../../td3/methode-cout-en.md), étape 2, prix Groq du 05/10/2026), pour une enveloppe de 2 000 tokens en entrée et 1 024 en sortie. gpt-oss-20b coûte 0,000457 USD, gpt-oss-120b 0,000914 USD et qwen3.8-27b 0,005696 USD par requête. La dépense réelle au TD est de 0 (plan Free Groq, routes `:free`). Cohere et Dots ne sont pas dans le portefeuille et n'ont pas de route payante documentée. Ils ne sont donc jamais premier modèle, mais ils peuvent siéger dans un panel.

**Score TD 1 par famille** (corrects / cellules, dernière tentative ; les échecs sont entre parenthèses) :

| Famille (cellules) | gpt-oss-20b | gpt-oss-120b | qwen3.8-27b | cohere north-mini | dots-3-note |
|---|---|---|---|---|---|
| Période (C01 C04 C05 C06 C07 C20) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| Âge à une date (C02 C08 C09 C11) | 2/4 (C02, C11) | 4/4 | 3/4 (C09) | 0/4 (les quatre) | 3/4 (C09) |
| Âge à la commande (C10) | 1/1 | 1/1 | 0/1 (C10) | 0/1 (C10 SQL invalide) | 0/1 (C10) |
| Produits (C03 C12 C13 C14) | 4/4 | 4/4 | 3/4 (C13 rejeté) | 4/4 | 4/4 |
| Combinées (C15 à C19) | 5/5 | 5/5 | 1/5 (C15 C16 C17 C19) | 2/5 (C15 C17 C19) | 1/5 (C15 C16 C17 C18) |

**Premier modèle** : le moins cher parmi ceux qui sont corrects sur **toutes** les cellules TD 1 de la famille. Le contrôle « aucun » n'est retenu que pour le tableau de bord interne, et seulement sur une famille où le premier modèle a eu 100 % (période et produits, 20b à 6/6 et 4/4).

| Famille | Premier modèle | Si indisponible | Cellules TD 1 qui justifient |
|---|---|---|---|
| Période | gpt-oss-20b | gpt-oss-120b, puis attente de la recharge, puis abstention | 30/30 correct, les 5 modèles sur C01 C04 C05 C06 C07 C20 |
| Âge à une date | gpt-oss-120b | attente de la recharge, puis abstention (aucun autre modèle à 4/4) | 120b 4/4 (C02 C08 C09 C11) ; 20b se trompe sur C02 (0) et C11 (322160) ; qwen et dots sur C09 ; cohere 0/4 |
| Âge à la commande | gpt-oss-20b | gpt-oss-120b, puis attente, puis abstention | 20b et 120b corrects sur C10 et C18 ; cohere SQL invalide sur C10 ; qwen et dots 119410 sur C10 |
| Produits | gpt-oss-20b | gpt-oss-120b, puis attente, puis abstention | 20b, 120b, cohere, dots 4/4 (C03 C12 C13 C14) ; qwen rejeté sur C13 |
| Combinées | gpt-oss-20b | gpt-oss-120b, puis attente, puis abstention | 20b et 120b 5/5 (C15 à C19) ; cohere 2/5, qwen 1/5, dots 1/5 |

Si la capacité gratuite est épuisée et que la requête ne peut pas attendre, on prend la route payante Groq Developer du même modèle, mais seulement si un budget est autorisé. Sinon, on s'abstient. Au réveil d'un `defer`, la disponibilité est mesurée à nouveau.

**Contrôle selon le coût d'une erreur.** Pour un tableau de bord interne, une erreur est vue en interne et se corrige. Pour un chiffre montré au client, elle coûte de la crédibilité et peut ouvrir un litige. Pour un montant versé, l'argent est sorti et se récupère mal. « Référence » veut dire un recalcul indépendant sans LLM : requête SQL validée plus recalcul Python sur les CSV, la méthode de [compute_references.py](../../td1/compute_references.py).

| Famille | Tableau de bord | Client | Versement |
|---|---|---|---|
| Période | aucun | quorum 2 sur 3 {20b, qwen, dots} | référence + revue |
| Produits | aucun | quorum 2 sur 3 {20b, cohere, dots} | référence + revue |
| Âge à une date | quorum 2 sur 3 {120b, qwen, dots} | référence | référence + revue |
| Âge à la commande | référence | référence | référence + revue |
| Combinées | quorum 2 sur 3 {20b, qwen, dots} | référence | référence + revue |

Une abstention du quorum renvoie toujours vers la référence. Elle ne déclenche jamais un nouveau tirage jusqu'à obtenir un accord.

**Pourquoi ces panels.** On a rejoué chaque panel sur les traces TD 1 ([rejeu-panels-td1.jsonl](rejeu-panels-td1.jsonl)) :

- Période : 6/6 juste. Produits : 4/4 juste.
- Âge à une date : 3 justes et 1 abstention (C09), aucun consensus faux. Le panel fixe de l'atelier {120b, cohere, qwen} aurait rendu **0 sur C09**, un consensus faux de cohere et qwen (référence 487980). On en retire donc cohere, qui est à 0/4 sur la famille.
- Âge à la commande : aucun panel de trois familles distinctes ne tient. {120b, qwen, dots} rend **119410 sur C10**, un consensus faux de qwen et dots (référence 558980). Seuls les deux gpt-oss réussissent, et ils sont de la même famille. Pour cette famille, aucun modèle gratuit ne suffit seul : on passe directement à la référence.
- Combinées : 2 justes et 3 abstentions (C15 C16 C17), aucun faux. Le quorum protège mais il abstient souvent, et l'abstention coûte une référence.
- Pas de 3 sur 5 : nos cinq modèles ne couvrent que quatre familles (openai deux fois). Un 3 sur 5 compterait deux voix corrélées.

**Limites.** La règle repose sur un seul passage de 20 questions sur une seule base. C'est une hypothèse de routage pour ce lot, pas un taux d'erreur, pas un classement durable, et pas une garantie du quorum. « Âge à la commande » repose sur deux cellules (C10, C18). La référence n'existe d'office que pour ces 20 questions. Pour une question nouvelle, il faut écrire et vérifier une requête, ce qui demande un travail humain qu'on chiffre au TD 3.

Simulateur : [atelier-routage-regle.py](../../td1/atelier-routage-regle.py) ; sorties [avant](simulateur-avant.jsonl) et [après](simulateur-apres.jsonl) adaptation.
