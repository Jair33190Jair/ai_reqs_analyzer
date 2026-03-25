# reqs_analyzer

AI-powered review pipeline for embedded software and systems requirements documents.

Accepts a born-digital PDF specification, runs it through a deterministic preprocessing pipeline, then uses Claude (Anthropic) to structure its content and flag quality issues — producing a structured JSON output and (planned) an HTML report.

---

## Pipeline Overview

![Pipeline Overview](architecture/pipeline_overview.svg)

> Source: [`pipeline_overview_v1.puml`](architecture/pipeline_overview_v1.puml)

---

## Input Constraints (v1)

| Constraint     | Value                  |
|----------------|------------------------|
| Format         | Born-digital PDF       |
| Max pages + Max Characters| See MAX_PAGES and MAX_CHARS at `pipeline_root/src/S0_extractor.py` |

---

## Pipeline Stages & Artifacts

See the [stage map in CLAUDE.md](CLAUDE.md) for the
authoritative stage-to-artifact mapping, and
[`architecture/pipeline_overview_v1.puml`](architecture/pipeline_overview_v1.puml)
for the visual flow.

Artifacts land in `pipeline_root/artifacts/<project>/<spec>/`.

---

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com)

---

## Setup

```bash
git clone <repo-url>
cd reqs_analyzer

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## Usage

```bash
source venv/bin/activate

make s0   # through s4, or:
make pipeline

# Custom input:
SPEC_NAME=myfile.pdf INPUT_TO_SPEC_PARENT=mydir/ make s0
```

See [CLAUDE.md](CLAUDE.md) for the full run command
reference and stage details.

---

## Project Structure

```
reqs_analyzer/
  architecture/           Architecture diagrams and design docs (PlantUML)
  pipeline_root/
    src/
      S0_extractor.py     Stage 0 — PDF text extraction
      S1_normalizer.py    Stage 1 — Text normalization
      S2_preflight.py     Stage 2 — Preflight gate
      S3_llm_structurer.py  Stage 3 — LLM structuring + content resolution
      S5_llm_analyzer.py  Stage 5 — LLM analysis (planned)
      S5_renderer.py      Stage 6 — Report rendering (planned)
      prompts/            LLM prompt definitions
    artifacts/            Intermediate JSON outputs (gitignored in production)
    input/                Input PDF specs — see input/arvms_specs/ for examples
    tests/                Test plans and test inputs
  requirements.txt
  .env.example
```

---

## Status

| Stage | Name           | Status   |
|-------|----------------|----------|
| S0    | Extractor      | Complete |
| S1    | Normalizer     | Complete |
| S2    | Preflight      | Complete |
| S3    | LLM Structurer | Complete |
| S4    | LLM Analyzer   | Complete |
| S5    | Renderer       | Planned  |

---

## Domain Context

This tool is designed for embedded systems and safety-critical engineering, targeting documents that follow standards such as ISO 26262 and ASPICE. The LLM analysis prompt is scoped to flag:

V1.0: 
- Requirements quality including:
  - Ambiguity, testability, atomicity, overconstraint, completeness and terminology.
Future:
- Ambiguity and underspecification
- Missing safety or ASIL context
- Traceability gaps
- Consistency problems across requirements

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

This project was developed by Jair Jimenez, Systems & Software Architect 
specialized in AI-augmented embedded and safety-critical system development with ADAS expertise.

For consulting, customization, or enterprise integration inquiries:
📩 jairjimenezv@gmail.com
🌐 linkedin.com/in/jairjimenezv