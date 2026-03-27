# Review Contract

This file defines the shared review-file contract and the
behavior for `/review <path>`.

## Review file contract

Every review file uses this top-level shape:

```json
{
  "meta": {
    "schema_version": "1.0",
    "status": "OPEN",
    "summary": "One honest sentence about what was reviewed and the key takeaway.",
    "counts": {
      "open": 0,
      "llm_fixed": 0,
      "human_fixed": 0,
      "skipped": 0,
      "obsolete": 0
    }
  },
  "findings": [
    {
      "_guide": {
        "status": "OPEN | LLM_FIXED | HUMAN_FIXED | SKIPPED | OBSOLETE",
        "human_command": "apply | skip | verify | ask",
        "severity": "CRITICAL | MAJOR | MINOR",
        "human_comment_or_question": "optional comment; question text when human_command is ask"
      }
    },
    { "finding object": "..." }
  ]
}
```

Shared rules:

- `meta.schema_version` is currently `"1.0"`.
- `meta.status` is LLM-managed:
  `OPEN`, `RESOLVED`, or `OBSOLETE`.
- Only set `meta.status` to `RESOLVED` when
  `meta.counts.open == 0`.
- `meta.counts` is recomputed every time the file is
  written.
- Count only real findings, not the `_guide` element.
- The `_guide` element is always the first entry in
  `findings`.

## Finding lifecycle

Every finding has:

- `type: "FINDING"` or `type: "QUESTION"`
- `status`
- `how_it_stands`
- `human_command`
- `human_comment_or_question`

Status meanings:

- `OPEN`: not yet actioned
- `LLM_FIXED`: Claude applied the fix
- `HUMAN_FIXED`: human applied the fix and Claude verified
  it
- `SKIPPED`: intentionally not acted on
- `OBSOLETE`: context no longer exists

Human command meanings:

- `"apply"`: Claude applies the recommendation
- `"skip"`: mark as intentionally skipped
- `"verify"`: Claude checks whether a human fix resolves it
- `"ask"`: Claude answers the question in chat and updates
  `how_it_stands`

All new findings start with:

```json
{
  "status": "OPEN",
  "how_it_stands": "",
  "human_command": "",
  "human_comment_or_question": ""
}
```

## Schema versioning

All review files declare `meta.schema_version`.

Versioning rules:

- Breaking changes use a major bump:
  `1.0` -> `2.0`
- Additive changes use a minor bump:
  `1.0` -> `1.1`
- Old review files keep their declared version. Do not
  migrate them by hand unless explicitly asked.

If you introduce a breaking change:

1. Update the version in every review template.
2. Update this file.
3. Update the `/review` logic so old and new versions both
   remain readable.

## /review <path>

Model: `sonnet`

This command processes human commands in an existing review
file.

For each finding where `human_command` is set:

### apply

- State in one sentence what file will change and what will
  change.
- Apply only the requested recommendation.
- Set `status` to `LLM_FIXED`.
- Set `how_it_stands` to one sentence describing what was
  changed and where.
- Reset `human_command` and
  `human_comment_or_question` to `""`.

### skip

- Set `status` to `SKIPPED`.
- Set `how_it_stands` to `Author chose to skip.`
- If `human_comment_or_question` is present, append its
  content.
- Reset `human_command` and
  `human_comment_or_question` to `""`.

### verify

- Read the relevant source files or diagram.
- If the issue is resolved:
  set `status` to `HUMAN_FIXED` and explain what confirms
  the fix.
- If the issue is not resolved:
  leave `status` as `OPEN` and explain what is still
  missing.
- Reset `human_command` and
  `human_comment_or_question` to `""`.

### ask

- Read `human_comment_or_question` as the author question.
- Answer directly in chat.
- Update `how_it_stands` with the conclusion only.
- Do not change `status` or `recommendation`.
- Reset `human_command` and
  `human_comment_or_question` to `""`.

### Opportunistic obsolete check

If an `OPEN` finding references code, a file, or a diagram
element that clearly no longer exists, mark it
`OBSOLETE` and explain why.

After processing the file:

1. Recompute `meta.counts`.
2. Set `meta.status` to `RESOLVED` only if
   `meta.counts.open == 0`.
3. Otherwise leave `meta.status` as `OPEN`.
4. Write the JSON back to the same file.
5. Print this compact summary table:

| finding_id | command applied | new status | note |
| --- | --- | --- | --- |
