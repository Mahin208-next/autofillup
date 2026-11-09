"""
Validation and sanitation helpers for SurveyForge AI.
"""
import re
from urllib.parse import urlparse
from typing import Tuple


def validate_google_forms_url(url: str) -> Tuple[bool, str]:
    """
    Validate whether a URL looks like a public Google Forms link.
    Returns (is_valid, sanitized_url_or_reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False, "Invalid URL scheme. Must start with http:// or https://"

    if "docs.google.com" not in parsed.netloc:
        return False, "URL must be a Google Docs domain (docs.google.com)."

    if "/forms/" not in parsed.path:
        return False, "URL must be a Google Forms path (/forms/...)."

    # Normalize viewform URL
    clean_url = url
    if not clean_url.endswith("/viewform") and "/viewform" not in clean_url:
        if clean_url.endswith("/"):
            clean_url = clean_url + "viewform"
        elif not clean_url.endswith("/viewform"):
            # Check if it has params or ends at hash
            if "?" in clean_url:
                base, query = clean_url.split("?", 1)
                if not base.endswith("/viewform"):
                    clean_url = f"{base}/viewform?{query}"
            else:
                clean_url = f"{clean_url}/viewform"

    return True, clean_url


def validate_sample_size(size: int, min_val: int = 10, max_val: int = 100000) -> Tuple[bool, str]:
    """Validate requested sample size."""
    try:
        val = int(size)
        if val < min_val:
            return False, f"Sample size must be at least {min_val}."
        if val > max_val:
            return False, f"Sample size cannot exceed {max_val}."
        return True, ""
    except (ValueError, TypeError):
        return False, "Sample size must be a valid integer."

