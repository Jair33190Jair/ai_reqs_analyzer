# 📄 AI Specification Analysis Pipeline — V1 Architecture & Interface Specification

**Version:** v1.0.0
**Owner:** Jair Jimenez
**Date:** 2026-02-23
**Scope:** Embedded / System / Software Requirements Specifications (SRS, SyRS, SWRS) with structured requirement IDs (e.g., `SYS-FUNC-001`)

---

# 1️⃣ Purpose

This document defines the complete **V1 production-ready pipeline specification** for:

PDF → Text Extraction → Normalization → Preflight → LLM Structuring → LLM Analysis → Human-Readable Report

The design prioritizes:

* ✅ Low testing cost
* ✅ Deterministic preprocessing
* ✅ Stable JSON contracts
* ✅ LLM usage only where necessary
* ✅ Sellable output (HTML report)
* ✅ Clear schema versioning.

---

# 2️⃣ High-Level Architecture

![Pipeline Overview](pipeline_overview.svg)

> Source: [`pipeline_overview_v1.puml`](pipeline_overview_v1.puml)
>
> The diagram is authoritative for pipeline flow, stage naming, and artifact filenames. This document extends with schemas, rules, and acceptance criteria.

### Design Philosophy

* Layers 0 and 2 are fully deterministic; Layer 1 uses LLM but with constrained output (regex of identified patterns).
* LLM is never used to compensate for broken extraction.
* All intermediate artifacts are stored for traceability.
* Each stage has a strict interface contract.

---

# 3️⃣ Directory & Artifact Structure

```
pipeline_run/
  input/
    spec.pdf
  artifacts/
    00_raw_extract.json
    01_normalized.json
    02_after_preflight.json  (logging/traceability only, not consumed downstream)
    03_llm_structured.json
    04_llm_analyzed.json
    05_flag_dashboard.html
  logs/
    pipeline.log
```

All stages must be reproducible from stored artifacts.

---

# 4️⃣ Stage (0) Extractor

## Purpose

Extract raw per-page text from PDF

## Input

* Born-digital PDF

## Output → `00_raw_extract.json`

@import "../pipeline_root/schemas/00_raw_extract.schema.v1.json"

## Acceptance Criteria

* Page order preserved
* No interleaved text from adjacent columns within a single extracted line
* Text non-empty for born-digital PDFs
* No requirement ID corruption

---

# 5️⃣ Stage (1) Normalizer

## Purpose

Reduce token waste and stabilize downstream parsing.

## Input

`00_raw_extract.json`

## Output → `01_normalized.json`

@import "../pipeline_root/schemas/01_normalized.schema.v1.json"

## Normalization Rules (V1)

### 1. Dehyphenation

Replace:

```
(\w)-\n(\w) → \1\2
```

### 2. Ligature Normalization

Replace:

* ﬀ → ff
* ﬁ → fi
* ﬂ → fl
* ﬃ → ffi
* ﬄ → ffl

### 3. LLM: Identify item ID and heading patterns

* LLM identifies the regex patterns for requirement IDs and section headings present in the document
* These patterns are used downstream by S2 (Preflight) for counting and validation. And later by S3 (Structurer) for identifying the document structure.

---

# 6️⃣ Stage (2) Preflight — Cost Protection Layer

## Purpose

Avoid wasting money on broken input.

## Input → `01_normalized.json`

## Output → `02_after_preflight.json`

@import "../pipeline_root/schemas/02_after_preflight.schema.v1.json"

## Deterministic Checks

* Count requirements with regex from normalizer
* Count duplicates
* Count sections with regex from normalizer
* Detect suspicious table patterns

## Gate Policy

LLM is called only if:

* Unparseable-line ratio ≥ 0.50
* Extraction-quality score ≥ 0.80 (Considers duplicate ratios, and unparseable line ratio)

Otherwise:

* Abort LLM call
* Emit guidance

---

# 7️⃣ Stage (3) LLM Structurer

## Purpose

Convert normalized text into structured specification JSON.

## Input → `01_normalized.json`

## Output → `03_llm_structured.json`

Schema: `spec.schema.v1`

@import "../pipeline_root/schemas/03_llm_structured.schema.v1.json"

## Structurer Rules

* One object per requirement ID
* Preserve thresholds, units, operators
* Evidence must include page reference
* Strict valid JSON only
* No modification of content of any type

---

# 8️⃣ Stage (4) LLM Analyzer

## Purpose

Assess quality, completeness, safety, and sellable insights.

## Input

* `03_llm_structured.json`
* `01_normalized.json` (full text for location resolution)

## Output → `04_llm_analyzed.json`

Schema: `analysis.schema.v1`

```json
{
  "meta": {
    "schema": "analysis.schema.v1",
    "doc_id": "arvms_srs_v1_2026-02-19",
    "analyzer_version": "v1",
    "timestamp": "2026-02-23T08:00:00+01:00"
  },
  "metrics": {
    "req_count": 42,
    "by_kind": {},
    "shall_ratio": 1.0
  },
  "issues": [
    {
      "issue_id": "ISS-0001",
      "item_id": "SYS-FUNC-002",
      "category": "verifiability",
      "severity": "medium",
      "message": "...",
      "suggested_fix": "..."
    }
  ]
}
```

## Categories

* verifiability
* ambiguity
* consistency
* completeness
* feasibility
* safety
* security
* performance
* traceability
* style

## Severity

* low
* medium
* high
* critical

## Analyzer Rules

* Each issue must reference an item_id or section_id
* Provide concrete suggested fix
* No generic advice
* Keep concise

---

# 9️⃣ Stage (5) Renderer — Sellable Output

## Purpose

Transform JSON into human-consumable report.

## Output

* `05_flag_dashboard.html`

## Report Sections

1. Metadata
2. Metrics Dashboard
3. Requirements Table (sortable/filterable)
4. Issues grouped by severity
5. Appendix with evidence excerpts

## Design Notes

* Use deterministic templating (e.g., Jinja2)
* No AI calls during rendering

---

# 🔟 Operational Controls

* Hard max token limit
* Chunk by section if too large (Using chapters as sections)
* Always store raw artifacts
* Log LLM cost per run

---

# 1️⃣1️⃣ Definition of Done (V1)

For born-digital PDFs:

* ≥ 95% requirement ID extraction accuracy
* ≥ 90% correct section assignment
* Valid schema-compliant JSON
* HTML report fully renderable

Scanned PDFs:

* Correctly detected and rejected with guidance.

---

# 🚀 Strategic Outcome

This V1 pipeline is:

* Deterministic where possible
* Controlled in cost
* Architecturally clean
* Scalable to enterprise use
* Sellable as an “AI Requirements Quality Auditor”
