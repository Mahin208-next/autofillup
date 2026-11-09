"""
General helper functions for SurveyForge AI.
"""
import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


def slugify_variable_name(text: str, max_len: int = 30) -> str:
    """Convert question text or category into clean snake_case variable name."""
    if not text:
        return "var"
    # Take first sentence or up to max_len
    clean = re.sub(r"[^\w\s-]", "", text.split("\n")[0]).strip().lower()
    clean = re.sub(r"[-\s]+", "_", clean)
    tokens = clean.split("_")
    # Take first 4-5 meaningful tokens
    short = "_".join(tokens[:5])[:max_len].strip("_")
    return short or "var"


def format_timestamp(dt: datetime = None) -> str:
    """Format datetime in human-readable ISO-like format."""
    if not dt:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def safe_json_dumps(obj: Any) -> str:
    """Safely dump JSON with UTF-8 encoding."""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return "{}"


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback."""
    if not text:
        return default if default is not None else {}
    try:
        return json.loads(text)
    except Exception:
        return default if default is not None else {}
