import logging
from pathlib import Path

_LOG_PATH = Path(__file__).parent.parent / "logs" / "pipeline.log"


def setup_logging() -> None:
    """Configure root logger: INFO to console, INFO to file."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    file_handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(module)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console, file_handler],
    )
