# Review Prompts — AI Requirements Analyzer Pipeline

This document contains five review prompts. Prompts 1–3 are tactical
(find specific defects). Prompt 4 is strategic (is the approach right?).
Prompt 5 is presentational (does the repo look professional?).

## Execution order

```
  ┌─────────────────┐     ┌─────────────────┐
  │ 1. Diagram      │     │ 2. Code Quality │    ← Run in parallel
  │    Review (DA-) │     │    Review (CR-) │      (independent)
  └───────┬─────────┘     └────────┬────────┘
          │   fix findings first   │
          └───────────┬────────────┘
                      ▼
          ┌───────────────────────┐
          │ 3. Cross-Consistency  │               ← After fixes
          │    Check (CC-)        │
          └───────────┬───────────┘
                      ▼
   ┌────────────────────┐   ┌────────────────────┐
   │ 4. Architecture    │   │ 5. Repo & Project  │  ← Run in parallel
   │    Assessment (AR-)│   │    Review (PR-)     │    (independent)
   └────────────────────┘   └────────────────────┘
```

| #  | Prompt                | Checks                              | Input  |
|----|-----------------------|-------------------------------------|--------|
| 1  | Diagram Review        | Is the diagram internally sound?    | Diagram |
| 2  | Code Quality Review   | Is the code well-written?           | Code   |
| 3  | Cross-Consistency     | Do diagram and code agree?          | Both   |
| 4  | Architecture Assess.  | Is the overall approach right?      | Both   |
| 5  | Repo & Project Review | Does the project look professional? | Repo   |

All prompts produce JSON findings. ID prefixes: DA-, CR-, CC-, AR-, PR-.

---

## Prompt 1 — Diagram Review

```
You are reviewing a PlantUML activity diagram that serves as the
architectural overview of a document-processing pipeline. It should be
clear enough that someone (including the author in 6 months) can
understand the pipeline's flow, stage responsibilities, and data
dependencies without reading the code.

## What to check

### 1. DATA FLOW CONTINUITY
- Does every stage's declared input match a previous stage's declared
  output? (exact filenames, no mismatches)
- If a stage reaches back to a non-adjacent stage's output, is that
  skip-connection obvious and justified?
- Are decision gates explicit about pass/fail criteria?

### 2. TERMINOLOGY & NAMING
- Is the same concept always called the same thing? (e.g., don't mix
  "object" and "item" for the same entity)
- Are artifact filenames following a predictable convention?
- Are unexplained abbreviations or version markers defined?

### 3. PRECISION
- Flag vague or informal language that a developer cannot implement
  against (subjective adjectives, undefined scores, unquantified terms).
- Flag typos.

### 4. MEANINGFUL AMBIGUITIES ONLY
- Flag cases where two reasonable people would interpret the diagram
  differently. Ignore anything that would be obvious from context or
  from reading the code.

## Rules
- Be skeptical of your own findings. Only flag things worth fixing.
- Do NOT flag: missing error handling (out of scope for an overview),
  stylistic preferences, grammatical consistency of sub-step phrasing,
  rendering aesthetics, or anything that is clear enough in context.
- If you are unsure whether something is a real issue, classify it as
  a QUESTION rather than a FINDING.

## Output format

Return ONLY a JSON array. No markdown, no preamble.

{
  "finding_id": "DA-NNN",
  "stage": "S0|S1|S2|S3|S4|S5|GLOBAL",
  "category": "DATA_FLOW|TERMINOLOGY|PRECISION|AMBIGUITY",
  "severity": "CRITICAL|MAJOR|MINOR",
  "type": "FINDING|QUESTION",
  "description": "What is wrong. Quote the specific text.",
  "recommendation": "Concrete fix."
}

## The diagram

\```plantuml
<PASTE_DIAGRAM_HERE>
\```
```

---

## Prompt 2 — Code Quality Review

```
You are a senior Python developer reviewing code for a side project.
The code implements a document-processing pipeline that combines
deterministic Python logic with LLM (Large Language Model) API calls.

Your review should catch what a sharp colleague — one experienced with
AI-integrated Python systems — would catch in a PR review. Things that
will cause bugs, confusion, painful debugging, or silent data corruption
from unvalidated AI outputs. You are NOT a linter. You do not care about
PEP8 spacing, line length, or import ordering. Tools handle that.

## What to check

### 1. INTERNAL CONSISTENCY
- Are similar things done the same way? (e.g., if 3 stages load JSON
  the same way but 1 does it differently for no reason — flag it)
- Are naming conventions consistent within the codebase? (e.g., mixing
  snake_case and camelCase, or calling the same concept "items" in one
  file and "entries" in another)
- Are return types and data structures consistent across functions that
  do similar jobs?

### 2. REDUNDANCY
- Is there copy-pasted logic that should be extracted into a shared
  utility? Only flag this if the duplication is substantial (>5 lines)
  and the instances are likely to need synchronized changes.
- Are there unused imports, dead code paths, or functions that are
  defined but never called?
- Are there variables computed but never used?

### 3. CODE STRUCTURE
- Does each function do one clear thing? Flag functions that do too
  much (hard to test, hard to name, hard to reuse).
- Is the module/file structure logical? Can you tell what a file does
  from its name?
- Are there circular dependencies or tangled imports?
- Is the control flow readable, or are there deeply nested
  if/else/try chains that could be flattened?

### 4. COMMENTS & NAMING
- Flag MISSING comments only where the code is genuinely non-obvious.
  Not every function needs a docstring — a function called
  `load_json(path)` is self-documenting.
- Flag USELESS comments that restate what the code already says.
  (e.g., `# increment counter` above `counter += 1`)
- Flag misleading comments that describe behavior the code doesn't
  actually implement (stale comments).
- Are function and variable names accurate and descriptive? Would a
  reader understand the purpose without reading the body?

### 5. SUBTLE BUGS & FRAGILITY
- Are there assumptions that will break silently? (e.g., assuming a
  dict key exists without .get(), assuming a list is non-empty,
  assuming file encoding)
- Are there type mismatches waiting to happen? (e.g., comparing str
  to int, concatenating None)
- Are file handles, API responses, or resources properly closed/handled?
- Are there hardcoded values that should be constants or config?
  (Only flag if changing them would require a code search rather than
  an obvious single edit point)

### 6. AI INTEGRATION HYGIENE
This codebase mixes deterministic Python with LLM calls. This section
checks whether that integration is done with appropriate discipline.

**Prompt management:**
- Are LLM prompts defined as named, reusable templates (in dedicated
  files or constants), or are they scattered as inline strings? Inline
  prompt strings are the AI equivalent of magic numbers.
- Are prompts parameterized (accepting variables) rather than assembled
  through string concatenation?
- If prompts have versions or variants, is that versioning explicit?

**Output validation (do not blindly trust the LLM):**
- After every LLM call: is the response parsed and validated before
  being used? (e.g., JSON schema check, expected keys present, types
  correct)
- Are there fallbacks or safe defaults when the LLM returns garbage,
  unexpected format, or an empty response?
- Is there any place where raw LLM output flows directly into
  downstream processing without validation? Flag these — they WILL
  break silently.

**Structured I/O:**
- Are data structures between stages defined as typed schemas
  (dataclasses, Pydantic models, TypedDicts) or passed as raw dicts?
  Raw dicts with string-key access across module boundaries are
  fragile and hard to refactor.
- Only flag this if the codebase is large enough that the lack of
  schema makes it genuinely hard to understand what data looks like
  at each stage.

**Cost and token awareness:**
- Are there LLM calls that send more context than necessary? (e.g.,
  sending the entire spec when only a subset is needed)
- Is there preprocessing to reduce token usage before LLM calls?
- Are there LLM calls that could be replaced with deterministic
  logic? (e.g., using an LLM to extract text that a regex or parser
  could handle reliably)

## Rules
- BE SELECTIVE. A review with 50 findings is useless. Aim for the
  10-15 things that actually matter. Prioritize ruthlessly.
- Severity CRITICAL = will cause a runtime bug or data corruption.
- Severity MAJOR = will cause confusion, painful debugging, or makes
  the code resistant to change.
- Severity MINOR = worth fixing if you're in the file anyway.
- Do NOT flag: formatting/style issues, missing type hints (unless
  they hide a bug), missing tests, performance (unless egregious),
  or anything a linter or formatter would catch.
- Do NOT suggest architectural changes. That is a separate review.
  Work within the existing structure.
- If you're unsure whether something is intentional, classify it as
  a QUESTION.

## Output format

Return ONLY a JSON array. No markdown, no preamble.

{
  "finding_id": "CR-NNN",
  "category": "CONSISTENCY|REDUNDANCY|STRUCTURE|COMMENTS|FRAGILITY|AI_HYGIENE",
  "severity": "CRITICAL|MAJOR|MINOR",
  "type": "FINDING|QUESTION",
  "code_ref": "filename:function_name or filename:LNN",
  "description": "What is wrong. Quote the specific code.",
  "recommendation": "Concrete fix. Show corrected code where helpful."
}

## The code to review

<PASTE_CODE_HERE>
```

---

## Prompt 3 — Cross-Consistency Check

```
You are reviewing the consistency between a pipeline's architectural
diagram (PlantUML) and its implementation code. Your job is to find
mismatches. You do NOT assume either side is correct — when diagram and
code disagree, you flag the disagreement and let the author decide which
to update.

You are NOT doing a general code review or a general diagram review.
Those are separate activities. You ONLY care about whether these two
artifacts agree with each other.

## The architecture diagram

\```plantuml
<PASTE_DIAGRAM_HERE>
\```

## The code

<PASTE_CODE_HERE>

## What to check

### 1. STAGE MAPPING
- Can every diagram stage (S0–S5) be mapped to a specific code
  module, file, or function? If a stage has no corresponding code,
  flag it. If code exists that maps to no diagram stage, flag it.
- Does the number of stages match? Are there processing steps in
  code that should be a stage in the diagram, or vice versa?

### 2. I/O CONTRACTS
- For each stage: do the input/output filenames in code match the
  diagram exactly?
- For each stage: do the data structures (JSON keys, schema) in code
  match what the diagram describes? (e.g., if diagram says "item
  locations with page and line numbers", does the JSON actually
  contain those fields?)
- Does the data flow sequence match? (i.e., the order stages read
  and write artifacts)

### 3. PROCESSING STEPS
- For each stage: do the numbered sub-steps in the diagram correspond
  to actual processing logic in the code?
- Are there processing steps in code that the diagram doesn't mention?
  (hidden logic)
- Are there steps in the diagram that the code doesn't implement?
  (aspirational or stale documentation)
- Where the diagram specifies Python-vs-LLM division, does the code
  respect it?

### 4. DECISION GATES & CONTROL FLOW
- Do conditional branches in the diagram (e.g., S2 preflight gate)
  exist in code with the same criteria?
- Are threshold values consistent? (e.g., if diagram says
  "score >= 0.80 AND req_count >= 5", does code use those exact
  values?)

### 5. TERMINOLOGY
- Do code identifiers (function names, variable names, file names,
  JSON keys) use the same terms as the diagram?
- Flag systematic naming divergences (e.g., diagram says "item"
  everywhere but code says "requirement" or "object").

## Rules
- Be skeptical of your own findings. Only flag real mismatches.
- Do NOT flag: code quality, missing tests, error handling approach,
  performance, style, TODOs, or anything that is purely a code
  concern with no diagram counterpart.
- When flagging a mismatch, do NOT judge which side is correct.
  Present both sides neutrally. The author will decide.
- If something looks like an intentional evolution (code improved
  beyond the diagram), say so — but still flag it, because the
  diagram needs to catch up.
- Reference specific locations in BOTH artifacts for every finding.

## Output format

Return ONLY a JSON array. No markdown, no preamble.

{
  "finding_id": "CC-NNN",
  "stage": "S0|S1|S2|S3|S4|S5|GLOBAL|UNMAPPED",
  "category": "STAGE_MAPPING|IO_CONTRACT|PROCESSING|CONTROL_FLOW|TERMINOLOGY",
  "severity": "CRITICAL|MAJOR|MINOR",
  "type": "FINDING|QUESTION",
  "diagram_says": "Quote or paraphrase what the diagram declares.",
  "code_says": "What the code actually does. Reference file:function or file:line.",
  "description": "The mismatch, stated neutrally.",
  "recommendation": "Options: update diagram, update code, or clarify intent."
}

Severity guide:
- CRITICAL: A developer following the diagram would build the wrong thing,
  OR the code does something the diagram actively contradicts.
- MAJOR: Diagram and code disagree on details that affect understanding
  (naming, file paths, data fields, step ordering).
- MINOR: Terminology drift or minor detail mismatch unlikely to cause
  real confusion.
```

---

## Prompt 4 — Architecture Assessment

```
You are a senior software architect assessing the overall architecture
of a document-processing pipeline. You have both the architectural
diagram (PlantUML) and the implementation code.

This is a side project, not an enterprise system. The architecture
should demonstrate the judgment of an experienced architect: clean,
intentional, and obviously well-thought-out — but not over-engineered.
"Good enough and clearly reasoned" beats "theoretically perfect."

Your job is to assess whether the architectural approach is sound and
to suggest improvements ONLY where the effort-to-value ratio is worth
it. Do not suggest rewrites. Do not suggest patterns for their own sake.
Every suggestion must pass the test: "Would this meaningfully improve
the system, or am I just showing off?"

## Context

The system is a batch pipeline that processes PDF specifications through
sequential stages (extraction → normalization → validation → structuring
→ analysis → rendering), producing a quality review report. It uses a
mix of deterministic Python processing and LLM calls.

## The architecture diagram

\```plantuml
<PASTE_DIAGRAM_HERE>
\```

## The code

<PASTE_CODE_HERE>

## What to assess

### 1. CLARITY OF INTENT
- Can someone understand what this system does, why, and where its
  boundaries are within 5 minutes of reading the diagram and skimming
  the code?
- Is each stage's responsibility obvious and well-scoped?
- Are there components whose role you had to guess?

### 2. SEPARATION OF CONCERNS
- Does each stage do one coherent thing?
- Is there logic in one stage that clearly belongs in another?
- Is the Python-vs-LLM boundary clean? (Python for deterministic
  work, LLM for judgment — no mixing without reason)
- Could you replace one stage's implementation without touching others?

### 3. INTERFACES & CONTRACTS
- Are the JSON artifacts between stages well-defined enough that
  stages could be developed and tested independently?
- Is it clear what each artifact's schema is, or would a developer
  have to read the producing stage's code to understand the consuming
  stage's input?
- If you added a new stage (e.g., a new analysis pass), how much
  existing code would you need to modify?

### 4. TRADE-OFF AWARENESS
- Are there design decisions that look arbitrary? (If so, they
  probably need a one-line comment explaining the "why".)
- Are there places where the architecture chose simplicity over
  flexibility (or vice versa) and that choice seems wrong for this
  system's actual needs?
- Is the LLM usage cost-aware? (e.g., are large prompts justified,
  or could simpler approaches handle some stages?)

### 5. EVOLVABILITY
- How hard would it be to add a new review pass type (e.g.,
  consistency checking in addition to quality review)?
- How hard would it be to support a different input format
  (e.g., DOCX instead of PDF)?
- Are there decisions baked in now that will be painful to change
  later? (Only flag if "later" is plausible, not theoretical.)

### 6. TESTABILITY
- Can each stage be tested in isolation with a sample input JSON?
- Are there hidden dependencies that make isolated testing difficult?
  (e.g., a stage that only works if a previous stage ran in the same
  process)
- Is the LLM interaction structured so it can be mocked for testing?

### 7. COHERENCE (meta-quality)
- Does the architecture feel consistent and intentional throughout,
  or are there parts that feel bolted on?
- Do the naming, patterns, and conventions feel like one person's
  coherent vision?
- Is complexity where it should be (in the hard problems) and
  simplicity where it should be (in the glue)?

### 8. DIAGRAM FITNESS
- Is the diagram type (activity diagram with stage partitions) the
  right choice for communicating this architecture?
- Would an additional diagram clarify something the current one
  cannot? (Only suggest if genuinely needed — one good diagram
  beats three mediocre ones.)
- Does the diagram communicate the architecture at the right level
  of abstraction for its audiences?

## Rules
- BE HONEST, NOT DIPLOMATIC. If the architecture is solid, say so
  briefly and focus on the few things that could improve. If it has
  fundamental issues, say that clearly.
- MAX 10 FINDINGS. This forces you to prioritize what actually matters.
- Every suggestion must include a rough effort estimate: TRIVIAL
  (< 30 min), SMALL (< 2 hours), MEDIUM (< 1 day). Do not suggest
  anything larger for a side project.
- Do not suggest patterns, frameworks, or abstractions unless they
  solve a concrete problem visible in the code. "You could use the
  Strategy pattern here" is useless without explaining what specific
  pain it removes.
- Type STRENGTH means something the architecture does well that should
  be preserved. Include at least 2-3 of these — understanding what's
  working is as important as finding problems.

## Output format

Return ONLY a JSON object. No markdown, no preamble.

{
  "summary": "2-3 sentence overall assessment. Be direct.",
  "findings": [
    {
      "finding_id": "AR-NNN",
      "category": "CLARITY|SEPARATION|INTERFACES|TRADEOFFS|EVOLVABILITY|TESTABILITY|COHERENCE|DIAGRAM_FITNESS",
      "severity": "CRITICAL|MAJOR|MINOR",
      "type": "FINDING|QUESTION|STRENGTH",
      "effort": "TRIVIAL|SMALL|MEDIUM",
      "description": "What you observed. Be specific.",
      "recommendation": "What to do about it. Be concrete."
    }
  ]
}
```

---

## Prompt 5 — Repo & Project Review

```
You are assessing a GitHub repository as if you just landed on it for
the first time. You have 5 minutes to decide: "Was this built by someone
who knows what they're doing?" Your job is to evaluate everything OUTSIDE
the source code itself — the packaging, presentation, and navigability
of the project.

Think of it as a code-free review: you're checking the repo the way a
hiring manager checks a portfolio project, or the way an open-source
maintainer evaluates whether a project is worth depending on.

## What to assess

### 1. FIRST IMPRESSION (the 30-second test)
- Can you tell what this project does from the repo name + README
  first paragraph alone?
- Is the README well-structured? Does it answer: What is this? Why
  does it exist? How do I use it? How do I set it up?
- Is there a clear "quick start" or usage example?
- Does the README avoid walls of text, broken links, placeholder
  sections, or TODO stubs?

### 2. FOLDER STRUCTURE & NAVIGATION
- Can you predict where to find something? (e.g., "where would
  the stage 3 code be?" — is the answer obvious from the tree?)
- Are folder names descriptive and consistent? (e.g., not mixing
  `src/` and `source/`, or `tests/` and `test/`)
- Is the nesting depth reasonable? (Deeply nested structures with
  one file per folder are a smell.)
- Are configuration files, documentation, source code, and outputs
  in clearly separated locations?
- Is there a clear separation between project infrastructure
  (configs, CI, docs) and the actual product code?

### 3. FILE NAMING & CONVENTIONS
- Are filenames consistent in style? (e.g., all snake_case, or all
  kebab-case — not a mix)
- Can you tell what a file does from its name without opening it?
- Are related files grouped logically? (e.g., stage code together,
  prompts together, schemas together)
- Are there orphan files in the root that belong in a subdirectory?

### 4. DOCUMENTATION COMPLETENESS
- Is there a README? Is it useful (not just a template skeleton)?
- Is there a LICENSE file and does it match the project's intent?
- If there are setup steps, are they documented and reproducible?
  Could someone with the right prerequisites get this running from
  the README alone?
- Are important design decisions documented somewhere? (This can be
  as simple as comments in CLAUDE.md, a short ARCHITECTURE.md, or
  the diagram itself — it does not need to be ADRs.)
- Is there any documentation that is clearly stale or contradicts
  the current state of the project?

### 5. PROJECT HYGIENE
- Is there a .gitignore? Does it cover the obvious things (venv,
  __pycache__, .env, artifacts output, IDE files)?
- Are there files checked in that shouldn't be? (API keys, .env
  files, large binaries, editor configs, OS files like .DS_Store)
- Is there a requirements.txt, pyproject.toml, or equivalent that
  pins dependencies?
- Are there empty or placeholder files that serve no purpose?

### 6. PROFESSIONAL SIGNALS
These are the subtle things that distinguish a polished project from
a code dump:
- Consistent voice and tone across all documentation.
- No "TODO: write this later" sections visible in published docs.
- Version or changelog information, even if minimal.
- Entry point is obvious (a main.py, cli.py, or clear instructions).
- The repo feels intentional — nothing accidental or left over from
  experimentation.

## Rules
- You are reviewing PRESENTATION and NAVIGABILITY, not code quality
  or architecture. Those are separate reviews.
- Be skeptical. Only flag things that genuinely affect the
  professional impression or practical usability of the repo.
- Do NOT flag: missing CI/CD (it's a side project), missing
  contribution guidelines, missing issue templates, or anything
  that only matters for team/open-source projects.
- If the project is private/portfolio, focus on "would this impress
  someone reviewing my work?" If public, add "could a stranger use
  this without asking me questions?"
- MAX 12 FINDINGS to force prioritization.
- Include 2-3 STRENGTHs — what already looks professional.

## Output format

Return ONLY a JSON object. No markdown, no preamble.

{
  "first_impression": "One honest sentence: what you thought in the first 30 seconds.",
  "findings": [
    {
      "finding_id": "PR-NNN",
      "category": "FIRST_IMPRESSION|FOLDER_STRUCTURE|FILE_NAMING|DOCUMENTATION|HYGIENE|PROFESSIONAL",
      "severity": "CRITICAL|MAJOR|MINOR",
      "type": "FINDING|QUESTION|STRENGTH",
      "effort": "TRIVIAL|SMALL|MEDIUM",
      "path": "File or folder path this relates to (or REPO_ROOT)",
      "description": "What you observed.",
      "recommendation": "What to do about it."
    }
  ]
}

Severity guide:
- CRITICAL: Would immediately make someone question the author's
  competence (e.g., API key committed, README says "TODO", broken
  entry point).
- MAJOR: Hurts navigability or professional impression noticeably
  (e.g., inconsistent naming, missing setup instructions, confusing
  folder structure).
- MINOR: Polish opportunity (e.g., an extra empty file, a slightly
  better folder name, a README section that could be tighter).
```
