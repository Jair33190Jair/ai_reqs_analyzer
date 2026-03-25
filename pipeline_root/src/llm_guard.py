"""Shared guard for any stage that can call an external LLM API."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic

_ALLOW_ENV_VAR = "ALLOW_LLM_EXECUTION"
_CONFIG_PATH = Path.home() / ".reqs_analyzer" / "llm_guard.json"


def _guard_enabled() -> bool:
    """Read the external guard config. Missing config defaults to enabled."""
    if not _CONFIG_PATH.exists():
        return True

    try:
        config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError(
            f"Failed to read LLM guard config at {_CONFIG_PATH}: {exc}. "
            "Refusing to call the LLM."
        ) from exc

    enabled = config.get("enabled")
    if not isinstance(enabled, bool):
        raise PermissionError(
            f"Invalid LLM guard config at {_CONFIG_PATH}: expected "
            '{"enabled": true} or {"enabled": false}. Refusing to call the LLM.'
        )
    return enabled


def ensure_llm_permission(stage_name: str, model_name: str) -> None:
    """Fail closed unless the user explicitly approves this LLM call."""
    if not _guard_enabled():
        return

    if os.getenv(_ALLOW_ENV_VAR) == "1":
        return

    if not sys.stdin.isatty():
        raise PermissionError(
            f"{stage_name} is about to call model '{model_name}', which may incur API cost. "
            f"Explicit approval is required for every run. "
            f"Re-run interactively and type 'yes', or set {_ALLOW_ENV_VAR}=1 for this command only. "
            f"Guard config: {_CONFIG_PATH}"
        )

    prompt = (
        f"{stage_name} is about to call model '{model_name}', which may incur API cost.\n"
        "Type 'yes' to continue: "
    )
    answer = input(prompt).strip().lower()
    if answer != "yes":
        raise PermissionError(
            f"LLM execution cancelled. Re-run {stage_name} and type 'yes' to approve."
        )


def get_anthropic_client(stage_name: str, model_name: str) -> anthropic.Anthropic:
    """Return an Anthropic client after explicit per-run approval."""
    ensure_llm_permission(stage_name, model_name)
    return anthropic.Anthropic()
