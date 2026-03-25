#!/usr/bin/env python3
"""
Stage 6 — Renderer
Input:  04_llm_analyzed.json  (S4 output)
Output: <source_stem>_llm_analysis.html
"""
# See: ../../architecture/architecture_v1.md

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from report_config import (
    CSS,
    SEVERITY_COLOR,
    SEVERITY_ORDER,
    TYPE_COLOR,
)

ROOT_DIR      = Path(__file__).parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
OUTPUT_DIR    = ROOT_DIR / "output"


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
        for s in SEVERITY_ORDER
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


def _render_flag(f: dict) -> str:
    flag_id = _esc(f.get("gen_flag_id", ""))
    flag_type = f.get("type", "")
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

    sev_color = SEVERITY_COLOR.get(severity, "#374151")
    type_color = TYPE_COLOR.get(flag_type, "#374151")

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
        f'<div class="flag-card sev-{severity.lower()}">'
        f'<div class="flag-header">'
        f'<span class="flag-id">{flag_id}</span>'
        f'<span class="badge sev-badge" style="background:{sev_color}">'
        f'{_esc(severity)}</span>'
        f'<span class="badge type-badge" style="color:{type_color}">'
        f'{_esc(flag_type)}</span>'
        f'<span class="badge cat-badge">{category}</span>'
        f'{conf_html}'
        f'</div>'
        f'<p class="affected-items"><strong>Item:</strong> {items_label}</p>'
        f'<p class="description">{description}</p>'
        f'{rec_html}'
        f'{ref_html}'
        f'</div>'
    )


def _render_flags(flags: list) -> str:
    if not flags:
        return (
            '<section id="flags">'
            '<h2>Flags</h2>'
            '<p>No flags.</p>'
            '</section>'
        )
    sev_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    sorted_flags = sorted(
        flags,
        key=lambda f: (
            sev_rank.get(f.get("severity", "INFO"), 99),
            f.get("gen_flag_id", ""),
        ),
    )
    cards = "".join(_render_flag(f) for f in sorted_flags)
    return f'<section id="flags"><h2>Flags</h2>{cards}</section>'


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
        f"  <style>{CSS}</style>\n"
        f"</head>\n"
        f"<body>\n"
        f"{_render_meta(data)}\n"
        f"{_render_dashboard(stats)}\n"
        f"{_render_flags(data.get('flags', []))}\n"
        f"</body>\n"
        f"</html>"
    )


def _report_filename(data: dict) -> str:
    """Return the output HTML filename derived from the source PDF stem."""
    source_meta = data.get("source_meta", {})
    source_name = source_meta.get("filename") or "report.pdf"
    source_stem = Path(source_name).stem or "report"
    return f"{source_stem}_llm_analysis.html"


def save_result(input_path: Path) -> Path:
    """Input: path to 04_llm_analyzed.json.
    Output: path to the written <source_stem>_llm_analysis.html in output/.
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
    rel = input_path.relative_to(ARTIFACTS_DIR).parent
    output_dir = OUTPUT_DIR / rel
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / _report_filename(data)
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
