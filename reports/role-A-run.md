# TD1 role A run: `groq:openai/gpt-oss-120b` on C01-C20

Operator: Bertrand Maigre (member A). Date: 21 October 2026. Branch: `bertrand`.

## Preconditions

- Database and CSV hashes identical to `data/manifest.json` (`verify-data.py`,
  `check_access.py --no-network`).
- `python3 scripts/verify_references.py`: 20/20 SQLite and CSV computations agree.
  The twenty values are also identical to the separate computation committed on
  `main` by Jean-Baptiste Pasteau (`c398d9b`, `compute_references.py`).
- Before the calls, the operator confirmed that the references had been
  cross-checked and validated, that it was the sub-group's turn, and that the
  account allowance covered the run.
- Kit files unchanged: skeleton, `modeles-autorises.json`, `schema.sql`,
  `questions-td1.json`.

## Effective parameters

Read from `modeles-autorises.json` and the skeleton, unchanged:

| Item | Value |
|---|---|
| Endpoint | `https://api.groq.com/openai/v1/chat/completions` |
| Body | `model=openai/gpt-oss-120b`, `temperature=0`, `max_completion_tokens=1024`, `reasoning_effort=low` |
| Batch rules | 3 s between requests, 45 s timeout, at most one retry per cell |
| Prompt | `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` of `skeleton-multi-llm-en.py`, unmodified |

Command, run by the operator in their own terminal (key loaded with
`read -gsx`, never written to a file):

```fish
python3 skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --cases C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20 --state state-A.jsonl --out traces-A.csv
```

## Counters

| Counter | Value |
|---|---:|
| Initial calls (cells) | 20 |
| Retries | 0 |
| Access errors | 0 |
| Access checks in this run | 0 (earlier `check_access.py` runs counted separately) |
| Groq allowance before / after | `<TODO: read from Groq console>` |

## Results

20/20 `correct` on the first attempt, all `nature = real`, HTTP 200,
`model_returned = openai/gpt-oss-120b`. Calls from 12:40:18 to 12:41:33 UTC.
Each trace carries the prompt fingerprint recomputed from the kit prompt and
the reference from `reference-td1.csv`; `traces-A.csv` and `state-A.jsonl`
agree field by field.

| Family | Correct / evaluated |
|---|---:|
| Period only (C01 C04 C05 C06 C07 C20) | 6/6 |
| Age on a reference date (C02 C08 C09 C11) | 4/4 |
| Age at the time of the order (C10) | 1/1 |
| Product list (C03 C12 C13 C14) | 4/4 |
| Combined (C15-C19) | 5/5 |

The SQL was read, not only scored. Completed age is computed from month and
day, through `date(D, '-25 years')` / `date(D, '-26 years')` bounds or a
year difference corrected by `strftime('%m-%d')`. Age at order time compares
the order date with `birth_date + 25 years` and `+ 26 years`. Periods use
`>=` / `<`. Empty cases (C06, C14) return 0 through `COALESCE`.

Latency: median 907 ms, range 488-1888 ms.

## Tokens and cost

| Quantity | Value |
|---|---|
| Input tokens | 12,814 |
| Output tokens | 5,157 (max 513 per call; cap 1,024 never reached) |
| Reasoning tokens | 3,103, already included in output tokens (each call's reasoning count is below its completion count), not added |
| Native cost | Empty in every row: N/A |
| API-equivalent cost | (12,814 x 0.15 + 5,157 x 0.60) / 1,000,000 = 0.0050 USD excl. tax, Groq Developer prices of 5 October 2026 (`methode-cout-en.md`) |
| Real spend | 0 USD only once the Free plan without billing is evidenced (`<TODO: dated console evidence>`); N/A until then |

## Limitations

- One run of twenty questions on one database: no error rate, no general ranking.
- No customer is born on 29 February, so leap-day age handling is untested here.
- Temperature 0 does not guarantee identical output on a rerun.

## Files

`state-A.jsonl` (raw JSONL attempts), `traces-A.csv` (CSV export), the 20
role-A rows of `model-question-comparison-en.csv`, and the
`openai/gpt-oss-120b` row of `five-model-summary-en.csv`. The `traces-demo.*`
files are simulations and are not part of these results.

## AI assistance

Assistant: Claude Code (Claude Opus 5.5). It read the kit, ran the local
checks, computed the effective parameters and prompt fingerprints offline,
audited the traces and wrote these summaries. It made no model call: the
operator ran the batch. User requests, verbatim:

> C'est bien à nous. Là on doit faire le rôle A. On a encore des crédits pr API.

> oui. On lance !

> finalise tout ensuite on push
