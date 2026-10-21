# AI assistance — reference calculation

Assistant: Codex. Date: 21 October 2026. Authoring context: Bertrand's branch.

## User request, verbatim

> Changement de plan. On fait les 20 quetsions ensuite on push
> Etnsuite on passera au role A

## Method and decisions

Read the supplied schema, protocol and all twenty questions. Wrote SQLite
SELECT queries, executed them read-only and independently recalculated each
amount by iterating over the distributed CSV data with Python. Preserved the
three-column reference format expected by the skeleton. Retained scripts,
computed evidence, and the outstanding human/instructor validation status.
No model API was called and no response from a model under evaluation was used.
No human cross-check is claimed. Students remain responsible for reviewing and
explaining the assisted code and the interpretation of the questions.
