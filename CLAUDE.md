# CLAUDE.md

This file is the front door for working in this repository.
Keep it practical. Keep it current. Prefer repo truths over
aspirational docs.

## Project overview

This repo is a batch pipeline for reviewing PDF requirements
specifications.

Current flow:

- `S0` extracts text from a born-digital PDF.
- `S1` normalizes the extracted content with an LLM.
- `S2` runs a deterministic preflight gate.
- `S3` structures the document with an LLM.
- `S4` analyzes requirement quality with an LLM.
- A renderer is planned, but not implemented yet.

Primary diagram:
`architecture/pipeline_overview_v1.puml`

## Run commands

```bash
source venv/bin/activate

make s0
make s1
make s2
make s3
make s4

make pipeline

SPEC_NAME=myfile.pdf INPUT_TO_SPEC_PARENT=mydir/ make s0
```

Artifacts land in:
`pipeline_root/artifacts/{project}/{spec}/`

Requires:
`ANTHROPIC_API_KEY` in `.env`

## Stage map

| Stage | File | Type | Current input -> output |
| --- | --- | --- | --- |
| `S0` | `pipeline_root/src/S0_extractor.py` | Deterministic | PDF -> `00_raw_extract.json` |
| `S1` | `pipeline_root/src/S1_normalizer.py` | LLM (Haiku) | `00_raw_extract.json` -> `01_normalized.json` |
| `S2` | `pipeline_root/src/S2_preflight.py` | Deterministic gate | `01_normalized.json` -> `02_after_preflight.json` |
| `S3` | `pipeline_root/src/S3_llm_structurer.py` | LLM (Haiku) | `01_normalized.json` -> `03_llm_structured.json` |
| `S4` | `pipeline_root/src/S4_llm_analyzer.py` | LLM (Sonnet) | `03_llm_structured.json` + `01_normalized.json` -> `04_llm_analyzed.json` |
| Planned renderer | `pipeline_root/src/S6_renderer.py` | Deterministic placeholder | `04_llm_analyzed.json` -> report output |

## Working rules

- Prefer the simplest change that preserves stage contracts.
- Treat schemas in `pipeline_root/schemas/` as hard
  contracts between stages.
- Stage code lives in `pipeline_root/src/`.
- Prompt code lives in `pipeline_root/src/prompts/`.
- Use "item" for parsed spec elements. Do not rename that
  concept to "object" or "entry".
- Every stage should validate its output before writing it.
- Keep LLM prompts reusable and explicit. Avoid scattering
  prompt strings inline unless there is a strong reason.

## Repo truths that matter - may be deleted in the future

- Trust `Makefile` and `pipeline_root/src/` over README or
  diagram text when they disagree.
- The current code path runs `S3` from
  `01_normalized.json`, not from `02_after_preflight.json`.
  Treat `S2` as a gate/reporting stage unless you are
  explicitly changing that contract.
- `S0` page and character limits: see `MAX_PAGES` and
  `MAX_CHARS` in `pipeline_root/src/S0_extractor.py`.
- `S6_renderer.py` exists only as a placeholder. It is not
  implemented, and the stage numbering around the renderer
  is not fully consistent across repo docs yet.

## Pipeline-specific invariants

Numeric thresholds and derived-field rules are
authoritative in source — do not maintain copies here.

- `S2` gate thresholds: see `MIN_SCORE` and
  `UNPARSEABLE_LINE_THRESHOLD` in
  `pipeline_root/src/S2_preflight.py`.
- `S2` score weights: see `_compute_score()` in
  `pipeline_root/src/S2_preflight.py`.
- `S3` is two-phase: the LLM returns locations first,
  then Python resolves those locations to verbatim
  content and adds derived fields (`gen_uid`,
  `gen_hierarchy_number`). See `S3_llm_structurer.py`.
- `S4` flag ID derivation: see `gen_flag_id` logic in
  `pipeline_root/src/S4_llm_analyzer.py`.

## Review commands

Use the review system when asked to run any of these:

- `/review diagram`
- `/review code`
- `/review consistency`
- `/review architecture`
- `/review project`
- `/review <path>`
- `/review all`

Detailed review workflow, output contract, lifecycle rules,
and per-review instructions live in:
`review_instructions/README.md`

## What good work looks like here

- Clear stage boundaries.
- Deterministic logic where it is sufficient.
- LLM use only where it adds clear value.
- JSON artifacts that are easy to inspect and diff.
- Docs that describe the repo as it exists today, not as it
  might exist later.
