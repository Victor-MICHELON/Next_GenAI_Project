# TD1 reference calculation — C01 to C20

## Observed result (21 October 2026)

Twenty SQLite queries executed on the supplied database opened read-only.
All twenty integer results agree with a separate Python computation over the
three supplied CSV files. No Groq or OpenRouter call was made.

- Queries: `scripts/reference_queries.sql`.
- Consolidated reference: `reference-td1.csv` (one query and one amount per case).
- CSV cross-check and SQL runner: `scripts/verify_references.py`.
- Per-case evidence: `reports/reference-verification.csv`.
- Database SHA-256: `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2`.

## Reproduce from the repository root

```fish
python3 scripts/verify_references.py
```

Only the standard library is needed. The command verifies database/CSV hashes,
runs each SQL query read-only, recalculates from CSV and checks the stored
reference. It exits unsuccessfully on any discrepancy. `--write` fills blank
reference cells only after all comparisons succeed; differing existing values
are rejected rather than silently overwritten.

## Conventions and independent computations

Revenue is the sum of order-line quantity multiplied by product price, in
integer euro cents excluding VAT. Do not count an order once when it contains
multiple product lines. Periods use `start <= order_timestamp < end`.
SQL uses `COALESCE(SUM(...), 0)` for an empty selection.

For age 25 on a fixed reference date D, SQL selects birth dates in the interval
`(D minus 26 years, D minus 25 years]`. It includes all orders for the selected
customers unless the question separately supplies a period or product filter.
For age at order time (C10/C18), SQL subtracts one from the year difference if
the birthday has not yet occurred. The independent CSV computation uses Python
calendar dates and completed-year arithmetic, with separate case conditions;
it does not execute, parse or reuse the SQL predicates. The supplied data
excludes leap-day birthdays. C06 and C14 select no lines and return integer zero.

Question interpretations were checked against `questions-td1.json` and section 1
of `consigne-etudiante-en.md`. Source data were not modified. These are computed
references, not model numerical answers adopted as truth.

## Contributions, AI assistance and remaining validation

Prepared on Bertrand's branch with Codex assistance. Both implementations and
the interpretation of the questions were assisted by the same AI; agreement
between them is a computational cross-check, not an independent human review.
No other member's review or instructor answer-key validation has yet been
observed. Record the reviewer, cases reviewed, date and any corrections here
after that review. Do not label these references instructor-validated yet.
The code-assistance request is retained in `reports/reference-ai-assistance.md`.

Before the model batches, another member should inspect the boundary cases,
age predicates and amounts, and the group should show the twenty values to the
instructor. Any later change to a reference already used in a real batch starts
a separate experiment with new state/output files, preserving the old traces.
