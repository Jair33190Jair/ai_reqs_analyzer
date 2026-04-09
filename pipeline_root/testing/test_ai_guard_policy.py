from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
GUARD_PATH = SRC_DIR / "llm_guard.py"
DIRECT_CLIENT_CALL = "anthropic.Anthropic("


def test_direct_anthropic_client_creation_is_only_allowed_in_guard() -> None:
    violations: list[str] = []

    for path in SRC_DIR.glob("*.py"):
        if path == GUARD_PATH:
            continue

        text = path.read_text(encoding="utf-8")
        if DIRECT_CLIENT_CALL in text:
            violations.append(str(path.relative_to(ROOT_DIR)))

    assert not violations, (
        "Direct Anthropic client creation is only allowed in src/llm_guard.py. "
        f"Found violations in: {', '.join(violations)}"
    )
