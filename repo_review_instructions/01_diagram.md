# /review diagram

Model: `sonnet`

Read:

- `architecture/pipeline_overview_v1.puml`

Check:

1. Data flow continuity.
2. Terminology and naming consistency.
3. Precision and typos.
4. Ambiguities that would lead two readers to different
   interpretations.

Do not flag:

- stylistic preferences
- missing error handling
- things that are obvious from context

Output file:

- `repo_reviews/{ddmmyy}_diagram.json`

Finding fields:

- `finding_id`: `DA-NNN`
- `stage`: `S0-S5` or `GLOBAL`
- `category`:
  `DATA_FLOW`, `TERMINOLOGY`, `PRECISION`, `AMBIGUITY`
- `severity`
- `type`
- `description`
- `recommendation`
- shared lifecycle fields from `contract.md`
