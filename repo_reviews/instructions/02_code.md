# /review code

Model: `sonnet`

Read:

- all files in `pipeline_root/src/`

Check:

1. Internal consistency.
2. Redundancy and dead code.
3. Code structure and control flow.
4. Comments and naming.
5. Fragility and subtle bugs.
6. AI integration hygiene.

AI integration hygiene includes:

- prompts should be reusable, not scattered inline
- every LLM response must be parsed and validated before use
- flag raw LLM output flowing downstream unvalidated
- flag oversized prompts or LLM calls that should be
  deterministic instead
- only push for typed structures if the codebase is large
  enough for that to matter

Rules:

- Aim for 10-15 findings max.
- Do not flag lint or formatting issues.
- Do not make architecture recommendations here.

Output file:

- `repo_reviews/reviews/{ddmmyy}_code.json`

Finding fields:

- `finding_id`: `CR-NNN`
- `category`:
  `CONSISTENCY`, `REDUNDANCY`, `STRUCTURE`, `COMMENTS`,
  `FRAGILITY`, `AI_HYGIENE`
- `severity`
- `type`
- `code_ref`: `filename:function_name` or `filename:LNN`
- `description`
- `recommendation`
- shared lifecycle fields from `contract.md`
