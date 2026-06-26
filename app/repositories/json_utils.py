import json
from typing import Any


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(value: str | None, default: Any) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)
