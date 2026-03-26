#!/usr/bin/env python3
"""
Script purpose: LLM-based structurer for requirements specification documents.
                Identifies section headings and spec items by location (page + line range),
                then resolves loc coordinates to verbatim text via map_content().
Input:  01_normalized.json   (S1 output)
Output: 03_llm_structured.json
  - LLM response validated against 03_llm_structured.01_llm_response.schema.v1.json
  - Enriched artifact validated against 03_llm_structured.02_resolved.schema.v1.json
"""
# See: ../../architecture/architecture_v1.md

import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path

import jsonschema
from dotenv import load_dotenv
from llm_guard import get_anthropic_client
from llm_pricing import get_cost

load_dotenv()

_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
_LLM_RESPONSE_SCHEMA = json.loads((_SCHEMAS_DIR / "03_llm_structured.01_llm_response.schema.v1.json").read_text(encoding="utf-8"))
_ARTIFACT_SCHEMA = json.loads((_SCHEMAS_DIR / "03_llm_structured.02_resolved.schema.v1.json").read_text(encoding="utf-8"))

_LLM_MODEL = "claude-haiku-4-5-20251001"
_LLM_MAX_TOKENS = 8000
_PROMPT_VERSION = "1"
USES_LLM = True

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_TEMPLATE = (
    _PROMPTS_DIR / f"S3_structurer.v{_PROMPT_VERSION}.txt"
).read_text(encoding="utf-8")


# --- Helpers ---

def _heading_instruction(heading_pattern: str | None) -> str:
    """Input: heading regex from S1 normalization, or None for raw specs.
    Output: instruction string injected into the LLM system prompt."""
    preamble_rule = (
        "\nSection loc must cover the heading line(s) AND any preamble/description text "
        "that follows before the first spec_item or next heading. "
        "Set line_end to the last line of the preamble, not just the heading."
    )
    if heading_pattern:
        return (
            f"A heading line matches this regex: {heading_pattern}\n"
            "Emit a section entry for each line that matches. Do not emit sections for non-matching lines."
            + preamble_rule
        )
    return (
        "No heading pattern was detected in this document. Identify headings semantically:\n"
        "- Short line (typically ≤ 60 characters)\n"
        "- Title case, sentence case, or ALL CAPS\n"
        "When uncertain, prefer not emitting a section over emitting a false one."
        + preamble_rule
    )


def _item_instruction(item_id_pattern: str | None) -> str:
    """Input: item ID regex from S1 normalization, or None for raw specs.
    Output: instruction string injected into the LLM system prompt."""
    if item_id_pattern:
        return (
            f"Spec items have IDs matching this regex: {item_id_pattern}\n"
            "Each item starts at the line containing its ID and ends at the line immediately before the next item ID or heading."
        )
    return (
        "This is a raw specification — no formal requirement IDs exist.\n"
        "Identify spec items as contiguous blocks of text that express a distinct engineering statement:\n"
        "- A system capability or behavior (look for 'shall', 'must', 'will', 'should')\n"
        "- A constraint, assumption, or interface definition\n"
        "Each item must be a single logical statement. Do not split a sentence across items. "
        "Do not merge statements that address different topics. Set spec_item_id to null for all items."
    )


def _format_pages(pages: list[dict]) -> str:
    """Input: normalized pages list (each with 'page' and 'text' keys).
    Output: single string with all pages rendered as 1-based numbered lines for the LLM prompt."""
    parts = []
    for p in pages:
        lines = p["text"].split("\n")
        numbered = "\n".join(f"L{i + 1}: {line}" for i, line in enumerate(lines))
        parts.append(f"=== PAGE {p['page']} ===\n{numbered}")
    return "\n\n".join(parts)


def _log_usage(input_tokens: int, output_tokens: int, elapsed: float) -> None:
    try:
        cost = f"${get_cost(_LLM_MODEL, input_tokens, output_tokens):.6f}"
    except Exception:
        cost = "cost unknown"
    logging.info(f"[S3 LLM] {input_tokens} in / {output_tokens} out — {cost} — {elapsed:.1f}s")


def _call_llm(system_prompt: str, user_message: str) -> tuple[str, dict]:
    """Input: fully rendered system and user prompt strings.
    Output: (raw_response, parsed JSON dict).
    Raises ValueError on unparseable response."""
    try:
        client = get_anthropic_client("S3_llm_structurer", _LLM_MODEL)
        t0 = time.monotonic()
        message = client.messages.create(
            model=_LLM_MODEL,
            max_tokens=_LLM_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        _log_usage(
            message.usage.input_tokens,
            message.usage.output_tokens,
            time.monotonic() - t0,
        )
        raw_response = message.content[0].text.strip()
        cleaned = re.sub(r"```json\s*([\s\S]*?)\s*```", r"\1", raw_response).strip()
        return raw_response, json.loads(cleaned)
    except PermissionError as exc:
        raise ValueError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned unparseable JSON: {exc}\n"
            f"Raw response: {raw_response[:500]}"
        ) from exc


# --- Mid-level ---

def run_structurer(normalized: dict) -> tuple[str, dict]:
    """Input: parsed 01_normalized JSON dict.
    Output: (raw_response, 03_llm_structured dict) — not yet schema-validated."""
    normalization = normalized.get("normalization", {})
    source_meta = normalized["source_meta"]

    system_prompt = _SYSTEM_TEMPLATE.format(
        heading_instruction=_heading_instruction(normalization.get("heading_pattern")),
        item_instruction=_item_instruction(normalization.get("item_id_pattern")),
        schema=json.dumps(_LLM_RESPONSE_SCHEMA, indent=2),
    )
    user_message = (
        f"source_file: {source_meta['filename']}\n\n"
        f"{_format_pages(normalized['pages'])}"
    )
    raw_response, result = _call_llm(system_prompt, user_message)
    result.pop("source_file", None)  # LLM may echo this back
    result["source_meta"] = source_meta  # enforce regardless of what the LLM produced
    return raw_response, result


def _resolve_loc(loc: dict, pages_with_lines: dict[int, list[str]]) -> str:
    """Input: a loc dict {page, line_start, line_end, page_end?} and a page→lines map.
    Output: the resolved verbatim text (1-based, inclusive line numbers).
    Supports multi-page items: line_start is on page, line_end is on page_end."""
    page_start = loc["page"]
    page_end = loc.get("page_end", page_start)
    if page_start == page_end:
        lines = pages_with_lines.get(page_start, [])
        return "\n".join(lines[loc["line_start"] - 1 : loc["line_end"]])
    parts = []
    for page_num in range(page_start, page_end + 1):
        page_lines = pages_with_lines.get(page_num, [])
        if page_num == page_start:
            parts.extend(page_lines[loc["line_start"] - 1 :])
        elif page_num == page_end:
            parts.extend(page_lines[: loc["line_end"]])
        else:
            parts.extend(page_lines)
    return "\n".join(parts)


def _gen_uid(content: str) -> str:
    """Input: verbatim content string.
    Output: GU-XXXXXX (6 hex uppercase) — sha256 of whitespace-normalised content."""
    normalised = " ".join(content.split())
    return "GU-" + hashlib.sha256(normalised.encode()).hexdigest()[:6].upper()


def _section_gen_hierarchy_number(section: dict, level_counters: dict[int, int]) -> str:
    """Input: a section dict and the running level-counter state (mutated in place).
    Output: gen_hierarchy_number string of the form 'G{n1}.{n2}...' derived from
    spec_hierarchy_number if present, otherwise computed from level and position."""
    spec_hierarchy_number = section.get("spec_hierarchy_number")
    if spec_hierarchy_number:
        return f"G{spec_hierarchy_number}"
    level = section.get("level") or 1
    level_counters[level] = level_counters.get(level, 0) + 1
    for l in list(level_counters):
        if l > level:
            del level_counters[l]
    return "G" + ".".join(str(level_counters.get(l, 1)) for l in range(1, level + 1))


def generate_gen_ids(enriched: dict) -> dict:
    """Input: enriched dict (output of map_content — sections and spec_items have 'content').
    Output: copy with 'gen_hierarchy_number' and 'gen_uid' added to every section and spec_item.
    Section gen_hierarchy_number: G{spec_hierarchy_number} or G{inferred from level/position}.
    Spec item gen_hierarchy_number: G{parent_section_number}-{NNN} (3-digit, sequential per section)."""
    level_counters: dict[int, int] = {}
    sections_with_ids = []
    for s in enriched.get("sections", []):
        gen_hierarchy_number = _section_gen_hierarchy_number(s, level_counters)
        sections_with_ids.append(
            {
                **s,
                "gen_hierarchy_number": gen_hierarchy_number,
                "gen_uid": _gen_uid(s["content"]),
            }
        )

    # Build sorted (page, line_start, gen_hierarchy_number) for parent lookup — use start page
    section_positions = sorted(
        (s["loc"]["page"], s["loc"]["line_start"], s["gen_hierarchy_number"])
        for s in sections_with_ids
    )

    item_counters: dict[str, int] = {}
    spec_items_with_ids = []
    for item in enriched.get("spec_items", []):
        loc = item["loc"]
        page, line = loc["page"], loc["line_start"]  # start position for parent lookup
        parent_id = "G0"  # fallback: item appears before any section
        for s_page, s_line, s_id in section_positions:
            if (s_page, s_line) <= (page, line):
                parent_id = s_id
        item_counters[parent_id] = item_counters.get(parent_id, 0) + 1
        gen_hierarchy_number = f"{parent_id}-{item_counters[parent_id]:03d}"
        spec_items_with_ids.append(
            {
                **item,
                "gen_hierarchy_number": gen_hierarchy_number,
                "gen_uid": _gen_uid(item["content"]),
            }
        )

    return {**enriched, "sections": sections_with_ids, "spec_items": spec_items_with_ids}


def map_content(result: dict, pages_with_lines: dict[int, list[str]]) -> dict:
    """Input: validated 03_llm_structured dict and a page→lines map.
    Output: enriched copy of result where every section and spec_item gains a
    'content' field — the verbatim text resolved from its loc coordinates.
    extra_attrs locs are preserved as-is for downstream use."""
    enriched = dict(result)
    enriched["sections"] = [
        {**s, "content": _resolve_loc(s["loc"], pages_with_lines)}
        for s in result.get("sections", [])
    ]
    enriched["spec_items"] = [
        {**item, "content": _resolve_loc(item["loc"], pages_with_lines)}
        for item in result.get("spec_items", [])
    ]
    return enriched


def validate_resolved(enriched: dict, pages_with_lines: dict[int, list[str]]) -> None:
    """Input: fully enriched artifact dict and page→lines map from the normalized source.
    Raises ValueError with the offending gen_hierarchy_number if any semantic check fails.
    Checks (in order):
      1. content non-empty for every section and spec_item
      2. loc.line_start ≤ loc.line_end for every loc (items, sections, extra_attrs)
      3. loc line numbers within actual page length
      4. spec_item_id present in content (when not null)
      5. extra_attrs locs fall within the parent item's loc range"""

    def _check_loc_bounds(loc: dict, ref: str) -> None:
        page_s = loc["page"]
        page_e = loc.get("page_end", page_s)
        if page_e < page_s:
            raise ValueError(f"{ref}: page_end ({page_e}) < page ({page_s})")
        start_page_lines = pages_with_lines.get(page_s)
        if start_page_lines is None:
            raise ValueError(f"{ref}: page {page_s} not found in normalized source")
        if loc["line_start"] > len(start_page_lines):
            raise ValueError(
                f"{ref}: line_start ({loc['line_start']}) exceeds page "
                f"{page_s} length ({len(start_page_lines)})"
            )
        end_page_lines = pages_with_lines.get(page_e)
        if end_page_lines is None:
            raise ValueError(f"{ref}: page_end {page_e} not found in normalized source")
        if loc["line_end"] > len(end_page_lines):
            raise ValueError(
                f"{ref}: line_end ({loc['line_end']}) exceeds page "
                f"{page_e} length ({len(end_page_lines)})"
            )
        if page_s == page_e and loc["line_start"] > loc["line_end"]:
            raise ValueError(
                f"{ref}: line_start ({loc['line_start']}) > "
                f"line_end ({loc['line_end']}) on same page"
            )

    for s in enriched.get("sections", []):
        ref = s.get("gen_hierarchy_number", "section?")
        if not s.get("content", "").strip():
            raise ValueError(f"{ref}: content is empty after loc resolution")
        _check_loc_bounds(s["loc"], ref)

    for item in enriched.get("spec_items", []):
        ref = item.get("gen_hierarchy_number", "item?")
        if not item.get("content", "").strip():
            raise ValueError(f"{ref}: content is empty after loc resolution")
        _check_loc_bounds(item["loc"], ref)

        spec_item_id = item.get("spec_item_id")
        if spec_item_id and spec_item_id not in item["content"]:
            raise ValueError(
                f"{ref}: spec_item_id '{spec_item_id}' not found in resolved content — "
                "loc boundary may be wrong"
            )

        item_loc = item["loc"]
        item_page_s = item_loc["page"]
        item_page_e = item_loc.get("page_end", item_page_s)
        for attr_name, attr_loc in (item.get("extra_attrs") or {}).items():
            attr_ref = f"{ref}.extra_attrs.{attr_name}"
            _check_loc_bounds(attr_loc, attr_ref)
            attr_page_s = attr_loc["page"]
            attr_page_e = attr_loc.get("page_end", attr_page_s)
            if attr_page_s < item_page_s or attr_page_e > item_page_e:
                raise ValueError(
                    f"{attr_ref}: pages {attr_page_s}–{attr_page_e} "
                    f"outside item page range {item_page_s}–{item_page_e}"
                )


def save_result(input_path: Path) -> Path:
    """Input: path to 01_normalized.json.
    Output: path to the written 03_llm_structured.json artifact.
    Always writes 03_llm_response.txt alongside for debugging.
    Raises FileNotFoundError or ValueError on any failure."""
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        normalized = json.load(f)
    if "pages" not in normalized or "normalization" not in normalized:
        raise ValueError(
            f"Expected a 01_normalized.json file (S1 output), got: {input_path.name}\n"
            "Usage: python S3_llm_structurer.py <path_to_01_normalized.json>"
        )
    raw_path = input_path.parent / "03_llm_response.txt"

    raw_response, result = run_structurer(normalized)
    raw_path.write_text(raw_response, encoding="utf-8")

    try:
        jsonschema.validate(result, _LLM_RESPONSE_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            f"LLM response failed schema validation: {exc.message}\n"
            f"Raw LLM response saved to: {raw_path}"
        ) from exc

    pages_with_lines: dict[int, list[str]] = {
        p["page"]: p["text"].split("\n") for p in normalized["pages"]
    }
    enriched = generate_gen_ids(map_content(result, pages_with_lines))

    try:
        validate_resolved(enriched, pages_with_lines)
    except ValueError as exc:
        raise ValueError(
            f"Resolved artifact failed semantic validation: {exc}\n"
            f"Raw LLM response saved to: {raw_path}"
        ) from exc

    try:
        jsonschema.validate(enriched, _ARTIFACT_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            f"Enriched artifact failed schema validation: {exc.message}\n"
            f"Raw LLM response saved to: {raw_path}"
        ) from exc

    output_path = input_path.parent / "03_llm_structured.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    return output_path


# --- Top-level ---

def main() -> None:
    from log_setup import setup_logging
    setup_logging()
    if len(sys.argv) < 2:
        logging.error("Usage: python S3_llm_structurer.py <path_to_normalized.json>")
        sys.exit(1)
    try:
        out = save_result(Path(sys.argv[1]))
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Saved to {out}")
        logging.info(
            f"Chunked: {len(data['sections'])} sections, "
            f"{len(data['spec_items'])} spec items, "
            f"skip_pages={data.get('skip_pages', [])}"
        )
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
