# IA générative de confiance - TD ESILV, sous-groupe

Dépôt de notre sous-groupe pour les trois TD du module « Trustworthy generative AI » (ESILV, A4) : TD 1 le 21 octobre, TD 2 le 18 novembre et TD 3 le 11 décembre 2026. Il part du kit `kit-td1` du 14 octobre 2026. La base et les vingt questions sont les mêmes pour tous les sous-groupes.

Les documents fournis par le prof (énoncés, consigne, guide, portefeuille, méthode de coût) restent dans leur version d'origine en anglais. Tout ce qu'on a produit est en français.

## Membres

| Membre | GitHub | Contributions principales (TD 1) |
|---|---|---|
| Victor Michelon | `Victor-MICHELON` | Création du dépôt ; opérateur B : lot `groq:openai/gpt-oss-20b` (`traces-B.csv`, `state-B.jsonl`) |
| Bertrand Maigre | `BertrandM78` | Opérateur A : lot `groq:openai/gpt-oss-120b` et [reports/role-A-run.md](reports/role-A-run.md) ; deuxième calcul des références (`scripts/`) ; analyse des échecs (`analyze_failures.py`, `notes/echecs-td1.md`), `model-question-comparison-en.csv` et tableau croisé (`pivot.py`) |
| Jean-Baptiste Pasteau | - | Références C01 à C20 (`compute_references.py`) ; fusion des traces (`merge_traces.py`) ; résumé des cinq modèles (`fill_summary.py`) ; prompt, README et [reports/td1.md](reports/td1.md) |
| Oscar Dujardin | `OscarDjr` | Opérateur D : lot `groq:qwen/qwen3.8-27b` (`traces-D.csv`, `state-D.jsonl`) ; tableau des membres et nettoyage du dépôt |
| Cyprien Avnel | `cyp44avenel-droid` | Opérateur C : lot `openrouter:cohere/north-mini-code:free` (`traces-C.csv`, `state-C.jsonl`) |
| Héloïse Moynot | - | Opératrice E : lot `openrouter:dots-studio/dots-3-note-preview:free` (`traces-E.csv`, `state-E.jsonl`) et premières causes d'échec (`model-question-comparison-E.csv`) |

Le partage du travail est détaillé dans le compte rendu de chaque TD.

## Environnement

- Pack de cours : `2026-10-14-students-1` (14 octobre 2026).
- Python 3.10 ou plus, uniquement la bibliothèque standard, dans un environnement virtuel local (`.venv/`, non versionné).
- Base : `data/boutique.sqlite`, jamais modifiée. SHA-256 `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2`, identique à `data/manifest.json`. Contenu : 5 produits, 59 clients, 397 lignes de commande.
- Modèles autorisés (`modeles-autorises.json`) : `openai/gpt-oss-120b`, `openai/gpt-oss-20b` et `qwen/qwen3.8-27b` sur Groq, `cohere/north-mini-code:free` et `dots-studio/dots-3-note-preview:free` sur OpenRouter.

## Les clés API

Les clés se mettent dans des variables d'environnement, sur sa propre machine. Elles ne vont jamais dans le dépôt : ni dans un fichier, ni dans un notebook, ni dans un commit. Le `.gitignore` exclut les fichiers `.env`, `.venv/`, `__pycache__/` et `.idea/`.

```bash
# Linux, macOS
export GROQ_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

```powershell
# Windows PowerShell
$env:GROQ_API_KEY = "..."
$env:OPENROUTER_API_KEY = "..."
```

## Rejouer le TD 1

Toutes les commandes se lancent à la racine du dépôt. Sous Windows, on remplace `python3` par `python`. Seules les étapes 1 (sans `--no-network`) et 3 ont besoin des clés et du réseau. Les autres travaillent sur les fichiers du dépôt.

### 1. Vérifier l'accès

```bash
python3 verify-data.py                 # intégrité de la base et des CSV
python3 check_access.py --no-network   # intégrité locale seulement : Python, hash de la base
python3 check_access.py                # + un appel par modèle autorisé (3 Groq, 2 OpenRouter)
```

### 2. Calculer les références

```bash
python3 compute_references.py --dry-run   # calcule et compare SQL / Python sans rien écrire
python3 compute_references.py             # écrit reference-td1.csv si les deux calculs sont d'accord
```

Les vingt valeurs de `reference-td1.csv` ont été validées par le corrigé du prof. La méthode et les conventions sont dans [reports/reference-method.md](reports/reference-method.md).

### 3. Les cinq lots, un par opérateur

Une requête à la fois pour tout le sous-groupe : on se passe la main entre opérateurs.

```bash
# A - Groq gpt-oss-120b
python3 skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-A.jsonl --out traces-A.csv
# B - Groq gpt-oss-20b
python3 skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-20b --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-B.jsonl --out traces-B.csv
# C - OpenRouter Cohere North Mini Code
python3 skeleton-multi-llm-en.py --run --models openrouter:cohere/north-mini-code:free --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-C.jsonl --out traces-C.csv
# D - Groq Qwen
python3 skeleton-multi-llm-en.py --run --models groq:qwen/qwen3.8-27b --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-D.jsonl --out traces-D.csv
# E - OpenRouter Dots
python3 skeleton-multi-llm-en.py --run --models openrouter:dots-studio/dots-3-note-preview:free --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-E.jsonl --out traces-E.csv
```

Attention : les fichiers `state-*.jsonl` du dépôt contiennent déjà nos 100 cellules vérifiées. Relancer ces commandes telles quelles ne fait aucun appel, parce que le squelette saute les cellules déjà vérifiées. Pour refaire une vraie expérience, il faut de nouveaux noms pour `--state` et `--out` : ça consomme du quota, et on garde nos fichiers d'origine.

Sans réseau, on peut tester toute la chaîne sur des modèles simulés avec `python3 skeleton-multi-llm-en.py --demo`. Les lignes produites sont en `simulation` et n'entrent dans aucun score.

### 4. Fusionner les traces

```bash
python3 merge_traces.py
```

Le script écrit `traces-td1.csv`, avec un seul en-tête et toutes les lignes de `traces-A.csv` à `traces-E.csv`. Il vérifie aussi le nombre de cellules par modèle, les retries, l'empreinte du prompt par question et la colonne `reference`.

### 5. Analyser les échecs

```bash
python3 analyze_failures.py
```

Le script écrit `notes/echecs-td1.md`, avec une cause par cellule ratée, lue dans le SQL ou dans l'erreur.

### 6. Tableau croisé modèles x questions

```bash
python3 pivot.py
```

Le script lit `model-question-comparison-en.csv` et écrit `pivot-td1.md` et `pivot-td1.html`.

### 7. Résumé des cinq modèles

```bash
python3 fill_summary.py
```

Le script remplit `five-model-summary-en.csv` :
- l'index public vient du portefeuille du 28/09/2026 ;
- les prix d'une route payante du même modèle viennent de `methode-cout-en.md`, étape 2 ;
- les résultats par famille sont lus dans `traces-td1.csv`.

### 8. Taux par modèle

Le squelette lit les taux dans un fichier d'état JSONL, donc on lance la commande une fois par opérateur :

```bash
python3 skeleton-multi-llm-en.py --rates --state state-A.jsonl
python3 skeleton-multi-llm-en.py --rates --state state-B.jsonl
python3 skeleton-multi-llm-en.py --rates --state state-C.jsonl
python3 skeleton-multi-llm-en.py --rates --state state-D.jsonl
python3 skeleton-multi-llm-en.py --rates --state state-E.jsonl
```

## Où sont les résultats du TD 1

| Fichier | Contenu |
|---|---|
| [reports/td1.md](reports/td1.md) | Le compte rendu du TD 1 |
| `reference-td1.csv` | Les 20 requêtes de référence et leur valeur, validées par le prof |
| `traces-A.csv` ... `traces-E.csv`, `state-A.jsonl` ... `state-E.jsonl` | Traces brutes de chaque opérateur, une ligne par appel |
| `traces-td1.csv` | Fusion des 100 lignes `real` |
| `traces-demo.csv`, `traces-demo.jsonl` | Lignes `simulation` du mode `--demo`, hors de tout score |
| `model-question-comparison-en.csv` | Une ligne finale par modèle et question, avec l'explication |
| `pivot-td1.md`, `pivot-td1.html` | Le tableau croisé modèles x questions |
| `notes/echecs-td1.md` | L'analyse des 23 cellules ratées |
| `five-model-summary-en.csv` | Le résumé des 5 modèles : index, prix, accès, résultats par famille |
| [prompts/prompt-experience-td1.md](prompts/prompt-experience-td1.md) | Le prompt utilisé, tel quel, identique pour les 5 modèles |
| `reports/role-A-run.md`, `reports/reference-method.md` | Détail du lot A et de la méthode des références |

## Nos scripts

| Fichier | Rôle |
|---|---|
| `compute_references.py` | Calcule les 20 références en SQL et les recalcule en Python sur les CSV |
| `scripts/reference_queries.sql`, `scripts/verify_references.py` | Deuxième calcul des références, fait de son côté |
| `merge_traces.py` | Fusionne les traces des opérateurs et fait les contrôles |
| `analyze_failures.py` | Propose une cause par cellule ratée |
| `pivot.py` | Construit le tableau croisé |
| `fill_summary.py` | Remplit le résumé des cinq modèles |

L'utilisation d'outils d'IA pour écrire ces scripts est décrite dans la section 7 de [reports/td1.md](reports/td1.md).

## Fichiers du kit

| Fichier | Rôle |
|---|---|
| `enonce-td1-en.md`, `enonce-td2-en.md`, `enonce-td3-en.md` | Les énoncés des trois TD |
| `consigne-etudiante-en.md` | Le protocole : tâche, schéma, conventions, comptes, règles d'appel, modèles, rendu, les vingt questions |
| `guide-environnement-etudiant-en.md` | Installer Python, créer les comptes et les clés, lancer `check_access.py` |
| `questions-td1-en.md`, `questions-td1.json` | Les vingt questions, sans réponses |
| `skeleton-multi-llm-en.py`, `sandbox_sqlite.py` | L'orchestrateur et son bac à sable SQLite en lecture seule |
| `check_access.py`, `verify-data.py`, `modeles-autorises.json` | Vérification de l'environnement et liste des modèles autorisés |
| `portefeuille-modeles-en.md`, `portefeuille-modeles-2026-09-28.csv` | Les soixante couples modèle/accès avec index public et prix |
| `methode-cout-en.md` | La méthode de calcul du coût et les prix de référence |
| `atelier-vote.py`, `atelier-routage.py` | Ateliers du TD 2 : vote k-sur-n et routage, sans réseau |
| `comparison-example-en.md` | Définition des colonnes des deux résumés et exemple fictif |
| `data/`, `schema.sql`, `manifest.json` | La base, ses CSV, le schéma et les empreintes SHA-256 du kit |
