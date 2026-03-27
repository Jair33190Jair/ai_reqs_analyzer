# /review project

Model: `sonnet`

Read:

- repo root listing
- folder tree to depth 2
- `README.md`
- `LICENSE`
- `.gitignore`
- `pyproject.toml` or `requirements.txt`
- any `docs/`

Assess:

1. First impression.
2. Folder structure.
3. File naming.
4. Documentation usefulness.
5. Hygiene.
6. Professional signals.

Rules:

- Max 12 findings.
- Include 2-3 positive observations in the summary.
- Do not flag missing CI/CD or contribution docs.
- Focus on whether the repo feels intentional and
  professional.

Output file:

- `repo_reviews/reviews/{ddmmyy}_project.json`

Finding fields:

- `finding_id`: `PR-NNN`
- `category`:
  `FIRST_IMPRESSION`, `FOLDER_STRUCTURE`, `FILE_NAMING`,
  `DOCUMENTATION`, `HYGIENE`, `PROFESSIONAL`
- `severity`
- `type`
- `effort`
- `path`
- `description`
- `recommendation`
- shared lifecycle fields from `contract.md`
