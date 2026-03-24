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
| `S4` | `pipeline_root/src/S4_llm_analyzer.py` | LLM (Sonnet) | `03_llm_structured.json` -> `04_llm_analyzed.json` |
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
- `S0_extractor.py` currently enforces
  `MAX_PAGES = 150` and `MAX_CHARS = 300_000`.
  Those are the code-authoritative limits.
- `S6_renderer.py` exists only as a placeholder. It is not
  implemented, and the stage numbering around the renderer
  is not fully consistent across repo docs yet.

## Pipeline-specific invariants

- `S2` exits with code `1` if `score < 0.70` or
  `unparseable_line_ratio >= 0.50`.
- `S2` score weights are:
  unparseable lines `60%`, duplicate IDs `30%`,
  duplicate sections `10%`.
- `S3` is two-phase:
  the LLM returns locations first, then Python resolves
  those locations to verbatim content and adds derived
  fields such as `gen_uid` and `gen_hierarchy_number`.
- `S4` uses deterministic flag IDs:
  `gen_flag_id` is derived from
  `source_ref + item_key + category`.

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
`guidelines/reviews/README.md`

## What good work looks like here

- Clear stage boundaries.
- Deterministic logic where it is sufficient.
- LLM use only where it adds clear value.
- JSON artifacts that are easy to inspect and diff.
- Docs that describe the repo as it exists today, not as it
  might exist later.
