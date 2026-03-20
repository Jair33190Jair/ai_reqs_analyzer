# AI Requirements Analyzer — Project Instructions

## Project overview

Batch pipeline that processes PDF specifications through sequential stages
(S0 Extraction → S1 Normalization → S2 Preflight → S3 Structuring →
S4 Analysis → S5 Rendering), producing a quality review report. Mix of
deterministic Python and LLM calls.

Architecture diagram: `docs/architecture/pipeline_overview.puml`

## Code conventions

- Python 3.11+, no frameworks beyond anthropic SDK
- JSON artifacts between stages, numbered 00–05
- Stage code in `src/stages/`, prompts in `src/prompts/`
- "item" = a parsed spec element (requirement, heading, etc.). Never "object" or "entry".

## Review commands

When I say `/review diagram`, `/review code`, `/review consistency`,
or `/review architecture`, run the corresponding review below.
Output findings as JSON to `reviews/` directory with timestamp filename.

---

### /review diagram

Review the architecture diagram for internal quality.

Read `docs/architecture/pipeline_overview.puml`, then check:

1. **DATA FLOW CONTINUITY** — Every stage's declared input must match
   a previous stage's declared output (exact filenames). Flag
   skip-connections that aren't justified. Decision gates must have
   explicit pass/fail criteria.

2. **TERMINOLOGY & NAMING** — Same concept, same name everywhere.
   Artifact filenames must follow a predictable convention. No
   unexplained abbreviations.

3. **PRECISION** — Flag vague/informal language a developer can't
   implement against. Flag typos.

4. **MEANINGFUL AMBIGUITIES** — Only flag where two people would
   interpret the diagram differently. Skip anything obvious from context.

Rules: Be skeptical. Only flag things worth fixing. No stylistic
preferences, no error-handling gaps (out of scope for overview).

Output as JSON array to `reviews/{timestamp}_diagram.json`:
```json
{"finding_id": "DA-NNN", "stage": "S0-S5|GLOBAL",
 "category": "DATA_FLOW|TERMINOLOGY|PRECISION|AMBIGUITY",
 "severity": "CRITICAL|MAJOR|MINOR", "type": "FINDING|QUESTION",
 "description": "...", "recommendation": "..."}
```

---

### /review code

Review the Python source code for quality issues.

Read all files in `src/`, then check:

1. **INTERNAL CONSISTENCY** — Similar operations done the same way.
   Consistent naming. Consistent return types.

2. **REDUNDANCY** — Duplicated logic (>5 lines) that should be shared.
   Unused imports, dead code, unused variables.

3. **CODE STRUCTURE** — Each function does one thing. Logical module
   structure. Readable control flow (no deep nesting).

4. **COMMENTS & NAMING** — Flag missing comments only where code is
   non-obvious. Flag useless comments that restate code. Flag stale
   comments. Names should be accurate and descriptive.

5. **SUBTLE BUGS & FRAGILITY** — Silent assumptions (missing .get(),
   empty list access, encoding). Type mismatches. Unclosed resources.
   Magic numbers that should be config.

6. **AI INTEGRATION HYGIENE** — This is a hybrid Python+LLM codebase:
   - Prompts should be named reusable templates, not inline strings.
   - Every LLM response must be parsed and validated before use.
     Flag any raw LLM output flowing into downstream logic unvalidated.
   - Data between stages should use typed schemas (dataclasses/Pydantic)
     not raw dicts, if the codebase is large enough to warrant it.
   - Flag LLM calls that send more context than needed, or that could
     be replaced with deterministic logic.

Rules: BE SELECTIVE — aim for 10-15 findings max. No style/formatting
(linters handle that). No architectural suggestions (separate review).

Output as JSON array to `reviews/{timestamp}_code.json`:
```json
{"finding_id": "CR-NNN",
 "category": "CONSISTENCY|REDUNDANCY|STRUCTURE|COMMENTS|FRAGILITY|AI_HYGIENE",
 "severity": "CRITICAL|MAJOR|MINOR", "type": "FINDING|QUESTION",
 "code_ref": "filename:function_name or filename:LNN",
 "description": "...", "recommendation": "..."}
```

---

### /review consistency

Cross-check the architecture diagram against the code. Find mismatches.
Do NOT assume either side is correct.

Read `docs/architecture/pipeline_overview.puml` AND all files in `src/`.

1. **STAGE MAPPING** — Every diagram stage maps to code. Every code
   module maps to a diagram stage. Flag orphans in either direction.

2. **I/O CONTRACTS** — Filenames in code match diagram exactly. Data
   structures match what diagram implies. Data flow order matches.

3. **PROCESSING STEPS** — Diagram sub-steps correspond to code logic.
   Flag hidden logic (code does something diagram doesn't mention) and
   aspirational docs (diagram says something code doesn't implement).
   Python-vs-LLM division must match.

4. **DECISION GATES** — Branches and thresholds in code match diagram.

5. **TERMINOLOGY** — Code identifiers use same terms as diagram.

Rules: Only flag real mismatches. Present both sides neutrally. If
something looks like intentional evolution, say so but still flag it.

Output as JSON array to `reviews/{timestamp}_consistency.json`:
```json
{"finding_id": "CC-NNN", "stage": "S0-S5|GLOBAL|UNMAPPED",
 "category": "STAGE_MAPPING|IO_CONTRACT|PROCESSING|CONTROL_FLOW|TERMINOLOGY",
 "severity": "CRITICAL|MAJOR|MINOR", "type": "FINDING|QUESTION",
 "diagram_says": "...", "code_says": "...",
 "description": "...", "recommendation": "..."}
```

---

### /review architecture

Holistic architecture assessment. Read the diagram AND the code.

This is a side project. "Good enough and clearly reasoned" beats
"theoretically perfect." Only suggest improvements where effort-to-value
is worth it. Every suggestion must pass: "Would this meaningfully
improve the system, or am I just showing off?"

1. **CLARITY OF INTENT** — Understandable in 5 minutes? Clear roles?
2. **SEPARATION OF CONCERNS** — Each stage does one thing? Clean
   Python-vs-LLM boundary? Stages replaceable independently?
3. **INTERFACES & CONTRACTS** — JSON artifacts well-defined enough for
   independent stage development? Schema clarity?
4. **TRADE-OFF AWARENESS** — Arbitrary decisions? Wrong simplicity/
   flexibility balance? LLM usage cost-aware?
5. **EVOLVABILITY** — How hard to add a review pass? New input format?
6. **TESTABILITY** — Stages testable in isolation? LLM calls mockable?
7. **COHERENCE** — Feels consistent and intentional? Complexity where
   it should be?
8. **DIAGRAM FITNESS** — Right diagram type? Additional diagram needed?
   Right abstraction level?

Rules: MAX 10 findings. Include effort estimates (TRIVIAL < 30min,
SMALL < 2hr, MEDIUM < 1 day). Include 2-3 STRENGTHs. No patterns for
their own sake.

Output as JSON object to `reviews/{timestamp}_architecture.json`:
```json
{"summary": "2-3 sentences, be direct.",
 "findings": [
   {"finding_id": "AR-NNN",
    "category": "CLARITY|SEPARATION|INTERFACES|TRADEOFFS|EVOLVABILITY|TESTABILITY|COHERENCE|DIAGRAM_FITNESS",
    "severity": "CRITICAL|MAJOR|MINOR",
    "type": "FINDING|QUESTION|STRENGTH",
    "effort": "TRIVIAL|SMALL|MEDIUM",
    "description": "...", "recommendation": "..."}
 ]}
```

---

### /review project

Review the repo's presentation, structure, and navigability. This is
NOT about code quality or architecture — it's about whether the project
looks like a professional built it.

Examine: repo root file listing, folder tree (2 levels), README.md,
LICENSE, .gitignore, pyproject.toml / requirements.txt, and any docs/.

1. **FIRST IMPRESSION** — Can you tell what this does from repo name +
   README first paragraph? Is there a clear quick-start? No broken
   links or TODO stubs?

2. **FOLDER STRUCTURE** — Predictable navigation? Descriptive, consistent
   folder names? Reasonable nesting depth? Clear separation of infra
   vs product code?

3. **FILE NAMING** — Consistent style? Names tell you what's inside?
   Related files grouped? No orphans in root?

4. **DOCUMENTATION** — README is useful, not a skeleton? LICENSE exists
   and matches intent? Setup steps reproducible from README alone?
   Design decisions documented somewhere? Nothing stale?

5. **HYGIENE** — .gitignore covers the basics? No committed secrets,
   binaries, or editor configs? Dependencies pinned? No empty
   placeholder files?

6. **PROFESSIONAL SIGNALS** — Consistent tone across docs. No visible
   TODOs in published docs. Entry point obvious. Repo feels intentional,
   nothing left over from experiments.

Rules: MAX 12 findings. Include 2-3 STRENGTHs. Don't flag missing CI/CD
or contribution guidelines — side project. Focus on: "Would this impress
someone reviewing my work?"

Output as JSON object to `reviews/{timestamp}_project.json`:
```json
{"first_impression": "One honest sentence.",
 "findings": [
   {"finding_id": "PR-NNN",
    "category": "FIRST_IMPRESSION|FOLDER_STRUCTURE|FILE_NAMING|DOCUMENTATION|HYGIENE|PROFESSIONAL",
    "severity": "CRITICAL|MAJOR|MINOR",
    "type": "FINDING|QUESTION|STRENGTH",
    "effort": "TRIVIAL|SMALL|MEDIUM",
    "path": "file or folder path, or REPO_ROOT",
    "description": "...", "recommendation": "..."}
 ]}
```

---

### /review all

Run all five reviews in sequence:
diagram → code → consistency → architecture + project (parallel).
Save all outputs to `reviews/` with shared timestamp prefix.
At the end, print a summary table of all findings across all five reviews.
