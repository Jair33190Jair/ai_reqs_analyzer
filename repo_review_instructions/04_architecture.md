# /review architecture

Model: `opus`

Read:

- `architecture/pipeline_overview_v1.puml`
- all files in `pipeline_root/src/`

Assess:

1. Clarity of intent.
2. Separation of concerns.
3. Interfaces and contracts.
4. Trade-off awareness.
5. Evolvability.
6. Testability.
7. Coherence.
8. Diagram fitness.

Rules:

- This is a side project. Good enough and clearly reasoned
  beats theoretical perfection.
- Max 10 findings.
- Include 2-3 positive observations in the summary.
- Every finding needs an effort estimate:
  `TRIVIAL`, `SMALL`, or `MEDIUM`.
- Do not suggest patterns for their own sake.

Output file:

- `repo_reviews/{ddmmyy}_architecture.json`

Finding fields:

- `finding_id`: `AR-NNN`
- `category`:
  `CLARITY`, `SEPARATION`, `INTERFACES`, `TRADEOFFS`,
  `EVOLVABILITY`, `TESTABILITY`, `COHERENCE`,
  `DIAGRAM_FITNESS`
- `severity`
- `type`
- `effort`
- `description`
- `recommendation`
- shared lifecycle fields from `contract.md`
