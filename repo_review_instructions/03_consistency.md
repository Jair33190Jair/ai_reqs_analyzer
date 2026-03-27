# /review consistency

Model: `opus`

Read:

- `architecture/pipeline_overview_v1.puml`
- all files in `pipeline_root/src/`

Check:

1. Stage mapping between diagram and code.
2. I/O contracts and filenames.
3. Processing steps and hidden logic.
4. Decision gates and thresholds.
5. Terminology consistency.

Rules:

- Do not assume diagram or code is automatically correct.
- Flag intentional-looking evolution neutrally if the two
  sides still disagree.

Output file:

- `repo_reviews/{ddmmyy}_consistency.json`

Finding fields:

- `finding_id`: `CC-NNN`
- `stage`: `S0-S5`, `GLOBAL`, or `UNMAPPED`
- `category`:
  `STAGE_MAPPING`, `IO_CONTRACT`, `PROCESSING`,
  `CONTROL_FLOW`, `TERMINOLOGY`
- `severity`
- `type`
- `diagram_says`
- `code_says`
- `description`
- `recommendation`
- shared lifecycle fields from `contract.md`
