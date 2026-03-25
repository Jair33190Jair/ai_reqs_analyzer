# Review System

This folder contains the instructions for running
structured reviews of this repo.

Use `llm_context.md` as the front door. Use these files when you
need to run or maintain the review system.

## Layout

Read these in this order:

1. `contract.md`
   Shared JSON contract, lifecycle rules, schema versioning,
   and `/review <path>` behavior.
2. `01_diagram.md`
   Instructions for `/review diagram`.
3. `02_code.md`
   Instructions for `/review code`.
4. `03_consistency.md`
   Instructions for `/review consistency`.
5. `04_architecture.md`
   Instructions for `/review architecture`.
6. `05_project.md`
   Instructions for `/review project`.

## Command index

| Command | Purpose | Output |
| --- | --- | --- |
| `/review diagram` | Review the architecture diagram on its own | `reviews/{ddmmyy}_diagram.json` |
| `/review code` | Review Python code quality | `reviews/{ddmmyy}_code.json` |
| `/review consistency` | Cross-check diagram vs code | `reviews/{ddmmyy}_consistency.json` |
| `/review architecture` | Assess overall architecture | `reviews/{ddmmyy}_architecture.json` |
| `/review project` | Review repo presentation and navigability | `reviews/{ddmmyy}_project.json` |
| `/review <path>` | Process human commands in an existing review file | update that file in place |
| `/review all` | Run all five reviews in sequence | five JSON files with one shared date prefix |

## Shared rules

- Be selective. A noisy review is a bad review.
- Prefer real defects, mismatches, and ambiguities over
  style opinions.
- When unsure, use `type: "QUESTION"` instead of forcing a
  `FINDING`.
- Write review files to `reviews/` using
  `{ddmmyy}_{type}.json`.
- Use the model named in the relevant review spec.
- If the client supports subagents, use one for standalone
  reviews. If not, run the same instructions inline.

## Execution order

Run reviews in this order when asked for `/review all`:

1. `diagram`
2. `code`
3. `consistency`
4. `architecture` and `project` in parallel

All outputs should share the same date prefix.
