# Assessment: what is marked and how the mark is computed

Beta, pack 2026-10-14-students-1, 14 October 2026. This document is the sheet laid on each sub-group's table from TD 1, with the marking rules that go with it. The scale, the shared group mark, the size of the oral adjustment and the place of code are proposed by the teaching team; the school's written approval is pending, and any change is dated on this page.

The sheet is the whole rule: nine outcomes, three per session, each marked 0, 1 or 2 on what the sub-group shows during the session, plus two points on the hand-in. No range, no half point, no discretionary bonus. You can compute the mark from the sheet at any time; two instructors who see the same evidence read the same level.

The printable sheet is [assessment-en.pdf](assessment-en.pdf), A4 landscape, one copy per sub-group.

Sub-group: ............   Instructor: ............   Members: ............

This sheet stays on your table for the three sessions. Your instructor marks each outcome at the end of the session, on what has been shown.

## How your mark is built

- **9 outcomes, 2 points each, marked at the end of each session: 18 points.** Three outcomes per session, one mark per outcome: 0, 1 or 2. Nothing in between.
- **2 points on the hand-in**, checked once after TD 3: the repository and the video. They are the only points that the sessions do not carry.
- **Total out of 20**: the sum of the three session marks plus the hand-in points. Your mark is the sum of the levels, so you can compute it yourself at any time.
- **The oral presentation then adjusts this total by -1 to +1 point**, on the clarity of the presentation and on whether each figure put forward refers back to a line of your traces.
- **An outcome marked 2 whose evidence is absent from the final repository drops to 1. No session mark ever rises after the session: the repository confirms, it does not re-mark.**
- **The eight members of a sub-group receive the same mark.**

## TD 1 - 21 October 2026 - Comparing models on the same questions

| Outcome | What you show | 0 | 1 | 2 | Mark |
|---|---|---|---|---|---|
| **R1**. An independent, checked reference | `reference-td1.csv` on screen, twenty rows, each with the query that produced its value. | Fewer than twenty rows, or a value that comes from a model instead of the database. | Twenty runnable queries; a value still differs from the answer key, or the convention and independent check are not explained. | Twenty correct values, an explained convention and an independent check shown, on the first attempt or after a correction. |  |
| **R2**. One trace line per call | A trace selected by the instructor, its prompt fingerprint and its attempts. | No trace file, or lines written by hand after the calls, or one line per question instead of one per call. | One automatic row per call to the five models, all attempts retained; fallback cells are identified. | In addition: you explain the selected trace, the common fingerprint per question, and a missing measurement or a retry if present. Missing and zero differ; a retry is not required. |  |
| **R3**. The cause of a failure, read from the trace | A cell and its evidence; the instructor supplies an example if the batch has none. Historical real, replayed or simulated nature is explicit. | No cause, or an impression ("this model is weak"). | The cause of the cell pointed at, read from the returned SQL or from the HTTP status. | In addition: you explain a failed access and distinguish it from a wrong answer. A supplied example gives access to the same level; no failure is required in your batch. |  |

Evidence seen: ..............................................   Next fix: ..........................................   Session mark: ...... / 6

## TD 2 - 18 November 2026 - The quorum, then the routing rule

| Outcome | What you show | 0 | 1 | 2 | Mark |
|---|---|---|---|---|---|
| **Q1**. A vote that abstains | `atelier-vote.py` run in front of the instructor on one question where no value has a majority. | The vote does not run, or it keeps a value without a majority. | The vote runs, returns the value that reaches a strict majority and abstains when none does. | In addition: an unavailable member stays in n without voting, and two accesses to the same provider and model pair count as one vote. |  |
| **Q2**. A wrong consensus, explained | An identified batch case or instructor-supplied historical real or synthetic case: agreeing values, independent reference, declared panel and k-of-n threshold. | The available or supplied case is not explained, or it does not show a wrong agreement. | At least two models return the same wrong value; you show the reference and distinguish that agreement from the declared quorum result. | In addition: you explain the cause in the SQL and an independent check able to detect it. No wrong agreement in your own batch does not cap the mark. |  |
| **Q3**. A routing rule tied to the TD 1 table | The one-page rule; the instructor points at one line and asks which cell of the TD 1 table justifies it. | No written rule, or a rule that sends every question to the same model. | One line per question family, each with the first model called and the check retained. | In addition: the line pointed at cites the TD 1 cell that justifies it, and the rule says what to do when the first model is unavailable: next model, deferral, abstention. |  |

Evidence seen: ..............................................   Next fix: ..........................................   Session mark: ...... / 6

## TD 3 - 11 December 2026 - Quantifying and deciding

| Outcome | What you show | 0 | 1 | 2 | Mark |
|---|---|---|---|---|---|
| **C1**. Two cost columns that do not mix | The configuration table on screen. | One cost column only, or a zero presented as a measurement. | Real spend and API equivalent separated for at least three configurations, costed or N/A with a documented reason. | In addition: dated, sourced prices for the same model, missing measurements preserved, coverage stated; a known subtotal is not presented as a complete total. |  |
| **C2**. A decision derived from the cost of an error | The named use case and the configuration you recommend. | No use case named, or the most capable model chosen without a reason. | A use case named, what an error costs in it, and a configuration recommended. | In addition: the recommendation cites cost per question or its justified unavailability, and the frequency observed in the batch. |  |
| **C3**. Written limits | The third slide. | No limits written. | What your twenty questions do not cover is written down. | In addition: simulator assumptions are explicit; twenty questions establish neither a general rate, a permanent ranking nor an error bound guaranteed by quorum. |  |

Evidence seen: ..............................................   Next fix: ..........................................   Session mark: ...... / 6

## Hand-in, after TD 3

| Point | What is checked | 0 | 1 | Mark |
|---|---|---|---|---|
| **H1**. A repository that can be replayed | The sub-group's GitHub repository, after TD 3. | The artefacts of one session are missing, or a figure presented cannot be found in any line. | The artefacts of the three sessions are there and every figure presented can be traced back to a line. |  |
| **H2**. A video that shows the chain | The recorded video attached to the repository. | No video, or a video that does not show the complete chain. | One call, the verdict, the vote. |  |

Total: ...... / 20   (TD 1 + TD 2 + TD 3 + Hand-in)

## Where code is marked

- How the system behaves is marked by Q1: 2 points out of 20. Observable evidence: the vote runs in front of the instructor, abstains without a majority, keeps the unavailable member in n.
- Reading and criticising code is marked by R3 and Q2: 4 points out of 20. Observable evidence: the cause of a failure and the cause of a wrong consensus, read from the returned SQL.
- Programming style carries no point in this proposal. The school says whether it wants points for it, with what weight and on what observable evidence.
- A language model's opinion on a repository opens no point: it says where to look, and the instructor decides on what was seen in the session.
- Coding assistance is proposed with disclosure, verification and explanation of the code; the policy awaits school approval. A reference value comes from SQL executed on the database and an independent check, never from adopting an LLM answer.

## Status

Teaching team proposal. The scale, the mark shared by the eight members, the size of the oral adjustment and the place of code are awaiting written approval from the module leader.

## How the levels are applied

The instructor marks what has been shown on screen, not what is announced or promised for later. Level 2 requires the evidence described for that outcome, including the supplied examples explicitly accepted by R3 and Q2. A doubt between two levels is settled by asking for the missing evidence before the end of the session; if it is not shown, the lower level applies.

A weak model result, an abstention or a negative gain from voting can still earn full marks: the outcomes reward the method, never the raw success rate of a model. Neither buying access nor using a more expensive model earns a point. An unavailable provider leads to a documented block and to the replay traces supplied by the instructor; a replay line is marked like a real line and loses no point.

R1 level 2 accepts twenty correct references on the first attempt, with an explained convention and independent check. R2 asks for an explanation of a selected trace, its common fingerprint and a missing measurement or retry if present; no retry is required. When a batch has no failure or wrong agreement, use an identified supplied case for R3 or Q2. Its nature stays separate from measured batch counts.

## Fictional worked example

A sub-group is marked 2, 1, 1 in TD 1 (four points), 2, 2, 1 in TD 2 (five points) and 1, 2, 2 in TD 3 (five points). Its repository holds the artefacts of the three sessions and its video shows a call, the verdict and the vote: two points. Total fourteen plus two, sixteen. One outcome marked 2 in TD 2 has no evidence in the repository: it drops to 1, so fifteen. The oral presentation traces every figure asked for back to a line: plus one. **Sixteen out of twenty**, the same mark for the eight members.

## Code and AI assistance

The code is not marked for itself; the outputs, the decisions and their explanation are. AI-assisted code is accepted, as is code written by hand. The prompts used, for the experiment as for the coding help, are kept in the repository as they were used.
