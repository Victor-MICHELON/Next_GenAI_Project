# Trustworthy generative AI (Next Generation AI), ESILV: sub-group repository

This repository is shared by all members of our sub-group and is kept from TD 1 to TD 3.

## Sub-group and members

- **Sub-group:** `<TODO: sub-group name or number>`
- **Members:**

| Member | GitHub | Main contributions |
|---|---|---|
| Victor Michelon | `<TODO>` | `<TODO>` |
| `<TODO>` | `<TODO>` | `<TODO>` |

The per-member split of work is detailed in each session report and in `contributions` tables where applicable.

## Course pack and environment

- **Course pack:** `2026-10-14-students-1` (14 October 2026). Reference site: <https://storage.googleapis.com/docs.g.quanticfactory.io/ESILV/next-generation-ai/latest/index.html>
- **Sessions:** TD 1 (21 October 2026), TD 2 (18 November 2026), TD 3 (11 December 2026).
- **Python:** 3.14.0 (3.10 or later required), in a local virtual environment (`.venv/`, not versioned).
- **SQLite:** 3.50.4 (Python's `sqlite3` module).
- **Database:** `data/boutique.sqlite`, never modified. SHA-256 `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2` (seed 20260925), identical to `data/manifest.json`. Content: 5 products, 59 customers, 397 order lines.
- **Authorised models** (see `modeles-autorises.json`): `groq/openai/gpt-oss-120b`, `groq/openai/gpt-oss-20b`, `groq/qwen/qwen3.8-27b`, `openrouter/cohere/north-mini-code:free`, `openrouter/dots-studio/dots-3-note-preview:free`.
- **Secrets:** `GROQ_API_KEY` and `OPENROUTER_API_KEY` are read from environment variables only. No key or `.env` file is committed (see `.gitignore`).

## Reproducing our work

From a fresh clone:

```bash
python3 -m venv .venv && source .venv/bin/activate

export GROQ_API_KEY="..."            # your own key, never committed
export OPENROUTER_API_KEY="..."

python3 verify-data.py               # database integrity against data/manifest.json
python3 check_access.py              # Python, database hash, one probe per authorised model
python3 skeleton-multi-llm-en.py --demo   # whole chain on simulated models, no key, no network
python3 atelier-routage.py           # TD 2 routing scenarios, no network
```

Real TD 1 runs use `--models` / `--cases` as described in `enonce-td1-en.md` and `consigne-etudiante-en.md`:

```bash
# <TODO: add the exact commands used, per member, once the TD 1 batch is run>
```

## Repository layout

| Path | Content |
|---|---|
| `README.md` | This file |
| `README-kit.md` | The original README of the course kit |
| `reports/td1.md`, `td2.md`, `td3.md` | One Markdown report per session (added at the end of each TD) |
| `reference-td1.csv` | Reference queries and values for C01 to C20, with the member who checked each |
| `traces-td1.jsonl`, `traces-td1.csv` | Every attempt, including errors and retries |
| `model-question-comparison-en.csv`, `five-model-summary-en.csv` | TD 1 summaries |
| `prompts-en.md` | System message and user template exactly as used, plus the AI-coding prompts |
| `skeleton-multi-llm-en.py`, `sandbox_sqlite.py`, `atelier-*.py` | Kit code (the k-of-n vote is completed in TD 2) |
| `data/` | Database and CSV exports (read-only) |

Files not yet present are produced during the corresponding session.

## Status

| Session | Status | Report | Submitted commit |
|---|---|---|---|
| TD 1 | Environment ready (`check_access.py`: 5/5 models OK) | `reports/td1.md` (to come) | `<TODO>` |
| TD 2 | Not started | `reports/td2.md` | `<TODO>` |
| TD 3 | Not started | `reports/td3.md` | `<TODO>` |

Open blocks and known failures are listed in each session report; unsuccessful attempts, errors and retries are kept as evidence rather than removed.

## AI assistance

AI-assisted coding is used. The prompts are kept in `prompts-en.md` as they were used, and decisions are explained in the reports.
