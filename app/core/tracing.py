import hashlib
import json
import logging
from pathlib import Path

from app.core.config import settings

log = logging.getLogger("trace")


def question_fingerprint(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]


def write_trace(record: dict) -> None:
    try:
        path = Path(settings.trace_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        log.exception("could not write trace")