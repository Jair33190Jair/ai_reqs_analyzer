#!/usr/bin/env python3
"""
Stage 6 — Renderer
Input:  04_llm_analyzed.json  (S4 output)
Output: 05_report.html
"""
# See: ../../architecture/architecture_v1.md

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


_SEVERITY_ORDER = ["CRITICAL", "MAJOR", "MINOR", "INFO"]

_SEVERITY_COLOR = {
    "CRITICAL": "#dc2626",
    "MAJOR":    "#d97706",
    "MINOR":    "#ca8a04",
    "INFO":     "#2563eb",
}

_TYPE_COLOR = {
    "FINDING":     "#374151",
    "QUESTION":    "#7c3aed",
    "OBSERVATION": "#6b7280",
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
  background: #f9fafb;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
h2 {
  font-size: 1.1rem;
  margin: 1.5rem 0 0.75rem;
  color: #374151;
}

/* meta */
header { margin-bottom: 2rem; }
.meta-grid {
  display: grid;
  grid-template-columns: 9rem 1fr;
  gap: 0.2rem 0.75rem;
}
.meta-grid dt { font-weight: 600; color: #6b7280; }

/* dashboard */
#dashboard {
  background: #fff;
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  color: #1f2937;
}
.total-count {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}
.stat-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.stat-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: #f3f4f6;
  min-width: 80px;
}
.stat-cell .count {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}
.stat-cell .label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  margin-top: 2px;
}
.sev-critical { background: #fef2f2; color: #dc2626; }
.sev-major    { background: #fffbeb; color: #d97706; }
.sev-minor    { background: #fefce8; color: #ca8a04; }
.sev-info     { background: #eff6ff; color: #2563eb; }

/* findings */
.finding-card {
  background: #fff;
  border-left: 4px solid #e5e7eb;
  border-radius: 0 6px 6px 0;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.finding-card.sev-critical { border-left-color: #dc2626; }
.finding-card.sev-major    { border-left-color: #d97706; }
.finding-card.sev-minor    { border-left-color: #ca8a04; }
.finding-card.sev-info     { border-left-color: #2563eb; }

.finding-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}
.finding-id {
  font-family: monospace;
  font-size: 0.8rem;
  color: #6b7280;
}
.badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.sev-badge { color: #fff; }
.type-badge, .cat-badge { background: #f3f4f6; }
.confidence {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-left: auto;
}
.affected-items {
  font-size: 0.85rem;
  margin-bottom: 0.4rem;
}
.description { margin-bottom: 0.5rem; }
.recommendation {
  font-size: 0.9rem;
  background: #f0fdf4;
  border-left: 3px solid #22c55e;
  padding: 0.5rem 0.75rem;
  border-radius: 0 4px 4px 0;
  margin-bottom: 0.4rem;
}
.reference { font-size: 0.8rem; color: #6b7280; }
"""


# --- Helpers ---

def _esc(text) -> str:
    """HTML-escape a value; returns empty string for None."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# --- Section renderers ---

def _render_meta(data: dict) -> str:
    meta = data.get("analysis_meta", {})
    source_meta = data.get("source_meta", {})
    source = _esc(source_meta.get("filename", ""))
    ts = meta.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts)
        ts_display = dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        ts_display = _esc(ts)
    doc_ver = _esc(meta.get("doc_version") or "—")
    doc_date = _esc(source_meta.get("doc_last_modified") or "—")

    return f"""<header>
  <h1>Requirements Analysis Report</h1>
  <dl class="meta-grid">
    <dt>Source</dt>       <dd>{source}</dd>
    <dt>Document ver.</dt><dd>{doc_ver}</dd>
    <dt>Document date</dt><dd>{doc_date}</dd>
    <dt>Analyzed</dt>     <dd>{ts_display}</dd>
    <dt>Model</dt>        <dd>{_esc(meta.get("model", ""))}</dd>
    <dt>Pass</dt>         <dd>{_esc(meta.get("pass", ""))}</dd>
    <dt>Prompt ver.</dt>  <dd>{_esc(meta.get("prompt_version", ""))}</dd>
  </dl>
</header>"""


def _render_dashboard(stats: dict) -> str:
    sev = stats.get("by_severity", {})
    typ = stats.get("by_type", {})
    total = stats.get("total_flags", 0)
    word = "flag" if total == 1 else "flags"

    sev_cells = "".join(
        f'<div class="stat-cell sev-{s.lower()}">'
        f'<span class="count">{sev.get(s, 0)}</span>'
        f'<span class="label">{s}</span>'
        f'</div>'
        for s in _SEVERITY_ORDER
    )
    type_cells = "".join(
        f'<div class="stat-cell">'
        f'<span class="count">{typ.get(t, 0)}</span>'
        f'<span class="label">{t}</span>'
        f'</div>'
        for t in ["FINDING", "QUESTION", "OBSERVATION"]
    )

    return f"""<section id="dashboard">
  <h2>Summary</h2>
  <p class="total-count">{total} {word} total</p>
  <div class="stat-row">{sev_cells}</div>
  <div class="stat-row">{type_cells}</div>
</section>"""


def _render_finding(f: dict) -> str:
    fid = _esc(f.get("gen_flag_id", ""))
    ftype = f.get("type", "")
    category = _esc(f.get("category", ""))
    severity = f.get("severity", "INFO")
    description = _esc(f.get("description", ""))
    recommendation = f.get("recommendation")
    reference = f.get("reference")
    confidence = f.get("confidence")

    affected = f.get("affected_items", [])
    items_parts = []
    for ai in affected:
        label = _esc(
            ai.get("spec_item_id") or ai.get("gen_hierarchy_number", "?")
        )
        role = ai.get("role", "")
        if role != "primary":
            label = f'{label} <small>({_esc(role)})</small>'
        items_parts.append(label)
    items_label = ", ".join(items_parts)

    sev_color = _SEVERITY_COLOR.get(severity, "#374151")
    type_color = _TYPE_COLOR.get(ftype, "#374151")

    rec_html = (
        f'<p class="recommendation">'
        f'<strong>Recommendation:</strong> {_esc(recommendation)}</p>'
        if recommendation else ""
    )
    ref_html = (
        f'<p class="reference">'
        f'<strong>Reference:</strong> {_esc(reference)}</p>'
        if reference else ""
    )
    conf_html = (
        f'<span class="confidence">confidence {confidence:.0%}</span>'
        if confidence is not None else ""
    )

    return (
        f'<div class="finding-card sev-{severity.lower()}">'
        f'<div class="finding-header">'
        f'<span class="finding-id">{fid}</span>'
        f'<span class="badge sev-badge" style="background:{sev_color}">'
        f'{_esc(severity)}</span>'
        f'<span class="badge type-badge" style="color:{type_color}">'
        f'{_esc(ftype)}</span>'
        f'<span class="badge cat-badge">{category}</span>'
        f'{conf_html}'
        f'</div>'
        f'<p class="affected-items"><strong>Item:</strong> {items_label}</p>'
        f'<p class="description">{description}</p>'
        f'{rec_html}'
        f'{ref_html}'
        f'</div>'
    )


def _render_findings(findings: list) -> str:
    if not findings:
        return (
            '<section id="findings">'
            '<h2>Findings</h2>'
            '<p>No findings.</p>'
            '</section>'
        )
    sev_rank = {s: i for i, s in enumerate(_SEVERITY_ORDER)}
    sorted_findings = sorted(
        findings,
        key=lambda f: (
            sev_rank.get(f.get("severity", "INFO"), 99),
            f.get("gen_flag_id", ""),
        ),
    )
    cards = "".join(_render_finding(f) for f in sorted_findings)
    return f'<section id="findings"><h2>Findings</h2>{cards}</section>'


# --- Top-level ---

def render(data: dict) -> str:
    """Input: parsed 04_llm_analyzed dict.
    Output: self-contained HTML string."""
    stats = data.get("stats", {})
    total = stats.get("total_flags", 0)
    title = f"Requirements Analysis — {total} flags"

    return (
        f"<!DOCTYPE html>\n"
        f'<html lang="en">\n'
        f"<head>\n"
        f'  <meta charset="utf-8">\n'
        f'  <meta name="viewport" '
        f'content="width=device-width, initial-scale=1">\n'
        f"  <title>{_esc(title)}</title>\n"
        f"  <style>{_CSS}</style>\n"
        f"</head>\n"
        f"<body>\n"
        f"{_render_meta(data)}\n"
        f"{_render_dashboard(stats)}\n"
        f"{_render_findings(data.get('flags', []))}\n"
        f"</body>\n"
        f"</html>"
    )


def save_result(input_path: Path) -> Path:
    """Input: path to 04_llm_analyzed.json.
    Output: path to the written 05_report.html.
    Raises FileNotFoundError or ValueError on any failure."""
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    if "flags" not in data:
        raise ValueError(
            f"Expected 04_llm_analyzed.json (S4 output), "
            f"got: {input_path.name}\n"
            "Usage: python S5_renderer.py "
            "<path_to_04_llm_analyzed.json>"
        )
    html = render(data)
    output_path = input_path.parent / "05_report.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    if len(sys.argv) < 2:
        logging.error(
            "Usage: python S5_renderer.py "
            "<path_to_04_llm_analyzed.json>"
        )
        sys.exit(1)
    try:
        out = save_result(Path(sys.argv[1]))
        logging.info(f"Saved to {out}")
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
