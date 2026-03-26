#!/usr/bin/env python3
"""
Script purpose: LLM-based analyzer for individual requirement quality.
                Reviews each spec item against ASPICE/ISO 26262/ISO 29148 quality criteria.
Input:  03_llm_structured.json  (S3 output)
Output: 04_llm_analyzed.json
  - LLM response validated against 04_llm_analyzed.01_llm_response.schema.v1.json
  - Enriched artifact validated against 04_llm_analyzed.02_resolved.schema.v1.json
"""
# See: ../../architecture/architecture_v1.md

import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
from dotenv import load_dotenv
from llm_guard import get_anthropic_client
from llm_pricing import get_cost

load_dotenv()

_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
_LLM_RESPONSE_SCHEMA = json.loads((_SCHEMAS_DIR / "04_llm_analyzed.01_llm_response.schema.v1.json").read_text(encoding="utf-8"))
_ARTIFACT_SCHEMA = json.loads((_SCHEMAS_DIR / "04_llm_analyzed.02_resolved.schema.v1.json").read_text(encoding="utf-8"))

_LLM_MODEL = "claude-sonnet-4-6"
_LLM_MAX_TOKENS = 16000
_PROMPT_VERSION = "1"
_PASS = "INDIVIDUAL_ITEM_QUALITY"
USES_LLM = True

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_TEMPLATE = (
    _PROMPTS_DIR / f"S4_individual_quality.v{_PROMPT_VERSION}.txt"
).read_text(encoding="utf-8")


# --- Helpers ---

def _gen_flag_id(source_file: str, primary_item: dict, category: str) -> str:
    """Input: source_file string, primary affected_item dict, category string.
    Output: flag ID of the form GF-XXXXXX (6 hex uppercase).
    Uses spec_item_id when present (stable across content and position changes),
    falls back to gen_hierarchy_number for raw specs (stable across content changes only).
    NOTE: collides if same item has multiple flags in the same category — accepted for V1."""
    item_key = primary_item.get("spec_item_id") or primary_item["gen_hierarchy_number"]
    raw = f"{source_file}|{item_key}|{category}|{_PASS}"
    return "GF-" + hashlib.sha256(raw.encode()).hexdigest()[:6].upper()


def _log_usage(input_tokens: int, output_tokens: int, elapsed: float) -> None:
    try:
        cost = f"${get_cost(_LLM_MODEL, input_tokens, output_tokens):.6f}"
    except Exception:
        cost = "cost unknown"
    logging.info(f"[S4 LLM] {input_tokens} in / {output_tokens} out — {cost} — {elapsed:.1f}s")


def _call_llm(system_prompt: str, user_message: str) -> tuple[str, dict]:
    """Input: fully rendered system and user prompt strings.
    Output: (raw_response, parsed JSON dict).
    Raises ValueError on unparseable response."""
    try:
        client = get_anthropic_client("S4_llm_analyzer", _LLM_MODEL)
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
            f"LLM returned unparseable JSON: {exc}\nRaw response: {raw_response[:500]}"
        ) from exc


def preprocess_for_llm(structured: dict) -> list[dict]:
    """Input: S3 resolved artifact.
    Output: list of slim item dicts for the LLM prompt — only what it needs for quality review.
    Strips loc, extra_attrs, flags, source — the LLM does not need those for quality judgment."""
    section_lookup = {}
    for sec in structured.get("sections", []):
        section_lookup[sec["gen_hierarchy_number"]] = {
            "number": sec.get("spec_hierarchy_number"),
            "title": sec["title"],
        }

    items = []
    for item in structured.get("spec_items", []):
        parent_key = item["gen_hierarchy_number"].rsplit("-", 1)[0] if "-" in item["gen_hierarchy_number"] else None
        section_ctx = section_lookup.get(parent_key, {})

        # Strip the spec_item_id prefix line from content (it's redundant with the label)
        content = item["content"]
        if item.get("spec_item_id"):
            content = content.replace(item["spec_item_id"] + "\n", "").strip()

        items.append({
            "gen_uid": item["gen_uid"],
            "spec_item_id": item.get("spec_item_id"),
            "gen_hierarchy_number": item["gen_hierarchy_number"],
            "classification": item.get("classification"),
            "item_type": item.get("item_type"),
            "section_title": section_ctx.get("title", "Unknown"),
            "section_number": section_ctx.get("number", ""),
            "content": content,
        })
    return items


def build_user_prompt(items: list[dict]) -> str:
    """Input: preprocessed item list.
    Output: user prompt string listing all requirements for review."""
    parts = [
        f"Review the following {len(items)} requirements for quality issues.",
        "---",
    ]
    for item in items:
        label = item["spec_item_id"] or item["gen_hierarchy_number"]
        parts.append(
            f"[{label}] (gen_uid={item['gen_uid']}, gen_hierarchy_number={item['gen_hierarchy_number']}, "
            f"Section {item['section_number']} {item['section_title']}, "
            f"type: {item['item_type']}, classification: {item['classification']})\n"
            f"{item['content']}"
        )
    return "\n\n".join(parts)


# --- Mid-level ---

def run_analyzer(structured: dict) -> tuple[str, dict]:
    """Input: parsed 03_llm_structured JSON dict.
    Output: (raw_response, flags dict conforming to 04_llm_analyzed.01_llm_response)."""
    system_prompt = _SYSTEM_TEMPLATE.format(
        schema=json.dumps(_LLM_RESPONSE_SCHEMA, indent=2),
    )
    items = preprocess_for_llm(structured)
    user_prompt = build_user_prompt(items)
    return _call_llm(system_prompt, user_prompt)


def enrich_flags(raw_result: dict, source_meta: dict, structured: dict) -> dict:
    """Input: validated raw LLM result dict, source_meta dict, S3 structured artifact.
    Output: resolved artifact matching 04_llm_analyzed.02_resolved schema —
    gen_flag_id assigned, item_review built, stats computed."""
    filename = source_meta["filename"]
    flags = []
    for f in raw_result.get("flags", []):
        # Find the primary affected item for gen_flag_id computation
        primary = None
        for ai in f["affected_items"]:
            if ai["role"] == "primary":
                primary = ai
                break
        if primary is None:
            primary = f["affected_items"][0]

        gen_flag_id = _gen_flag_id(filename, primary, f["category"])

        flags.append({
            "gen_flag_id": gen_flag_id,
            "pass": _PASS,
            "type": f["type"],
            "category": f["category"],
            "severity": f["severity"],
            "affected_items": f["affected_items"],
            "description": f["description"],
            "recommendation": f.get("recommendation"),
            "reference": f.get("reference"),
            "confidence": f["confidence"],
        })

    # Build item_review from structured input + flags + reviewed_items
    reviewed_uids = set(raw_result.get("reviewed_items", []))
    all_items = structured.get("spec_items", [])

    # Map gen_uid → list of flag IDs
    uid_to_flag_ids: dict[str, list[str]] = {}
    for f in flags:
        for ai in f["affected_items"]:
            uid_to_flag_ids.setdefault(ai["gen_uid"], []).append(f["gen_flag_id"])

    item_review = []
    for item in all_items:
        uid = item["gen_uid"]
        fids = uid_to_flag_ids.get(uid, [])
        if uid in reviewed_uids:
            status = "FLAGGED" if fids else "PASSED"
        else:
            status = "SKIPPED"
        item_review.append({
            "gen_uid": uid,
            "spec_item_id": item.get("spec_item_id"),
            "status": status,
            "flag_ids": fids,
        })

    skipped_count = sum(1 for r in item_review if r["status"] == "SKIPPED")
    if skipped_count > 0:
        logging.warning(f"[S4] {skipped_count} item(s) were not reviewed by the LLM")

    flagged = sum(1 for r in item_review if r["status"] == "FLAGGED")
    passed = sum(1 for r in item_review if r["status"] == "PASSED")

    stats = {
        "total_items": len(all_items),
        "reviewed": len(reviewed_uids),
        "skipped": skipped_count,
        "flagged": flagged,
        "passed": passed,
        "total_flags": len(flags),
        "by_severity": {
            "CRITICAL": sum(1 for f in flags if f["severity"] == "CRITICAL"),
            "MAJOR": sum(1 for f in flags if f["severity"] == "MAJOR"),
            "MINOR": sum(1 for f in flags if f["severity"] == "MINOR"),
            "INFO": sum(1 for f in flags if f["severity"] == "INFO"),
        },
        "by_type": {
            "FINDING": sum(1 for f in flags if f["type"] == "FINDING"),
            "QUESTION": sum(1 for f in flags if f["type"] == "QUESTION"),
            "OBSERVATION": sum(1 for f in flags if f["type"] == "OBSERVATION"),
        },
    }

    return {
        "source_meta": source_meta,
        "analysis_meta": {
            "pass": _PASS,
            "model": _LLM_MODEL,
            "prompt_version": _PROMPT_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "doc_version": source_meta.get("doc_version"),
        },
        "flags": flags,
        "item_review": item_review,
        "stats": stats,
    }


def save_result(input_path: Path) -> Path:
    """Input: path to 03_llm_structured.json.
    Output: path to the written 04_llm_analyzed.json artifact.
    Always writes 04_llm_response.txt alongside for debugging.
    Raises FileNotFoundError or ValueError on any failure."""
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        structured = json.load(f)
    if "sections" not in structured or "spec_items" not in structured:
        raise ValueError(
            f"Expected a 03_llm_structured.json file (S3 output), got: {input_path.name}\n"
            "Usage: python S4_llm_analyzer.py <path_to_03_llm_structured.json>"
        )
    source_meta = structured.get("source_meta", {"filename": input_path.name})
    raw_path = input_path.parent / "04_llm_response.txt"

    raw_response, result = run_analyzer(structured)
    raw_path.write_text(raw_response, encoding="utf-8")

    # Wrap in {"flags": [...]} if LLM returned a bare array
    if isinstance(result, list):
        result = {"flags": result}

    try:
        jsonschema.validate(result, _LLM_RESPONSE_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            f"LLM response failed schema validation: {exc.message}\n"
            f"Raw LLM response saved to: {raw_path}"
        ) from exc

    enriched = enrich_flags(result, source_meta, structured)

    try:
        jsonschema.validate(enriched, _ARTIFACT_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            f"Enriched artifact failed schema validation: {exc.message}\n"
            f"Raw LLM response saved to: {raw_path}"
        ) from exc

    output_path = input_path.parent / "04_llm_analyzed.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    return output_path


# --- Top-level ---

def main() -> None:
    from log_setup import setup_logging
    setup_logging()
    if len(sys.argv) < 2:
        logging.error("Usage: python S4_llm_analyzer.py <path_to_03_llm_structured.json>")
        sys.exit(1)
    try:
        out = save_result(Path(sys.argv[1]))
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Saved to {out}")
        s = data["stats"]
        logging.info(
            f"Analyzed: {s['total_items']} items — "
            f"{s['reviewed']} reviewed, {s['skipped']} skipped, "
            f"{s['flagged']} flagged, {s['passed']} passed"
        )
        logging.info(
            f"Flags: {s['total_flags']} — "
            f"CRITICAL={s['by_severity']['CRITICAL']}, "
            f"MAJOR={s['by_severity']['MAJOR']}, "
            f"MINOR={s['by_severity']['MINOR']}"
        )
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
