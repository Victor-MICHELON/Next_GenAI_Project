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

<TODO binôme B>

## 3. Étape 3 - La règle de routage (binôme C)

<TODO binôme C>

## 4. Contributions

<TODO>

## 5. Suites

<TODO>
