"""
app/utils/helpers.py

General-purpose utility helpers used across the application.

Keep functions pure (no side-effects, no I/O) unless explicitly documented.
"""

import hashlib
import math
import uuid
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Identifier helpers
# ---------------------------------------------------------------------------

def generate_uuid() -> str:
    """Return a new random UUID v4 as a string."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    Return a compact, URL-safe unique identifier.

    The ID is derived from the first `length` characters of a random UUID
    with hyphens stripped.

    Args:
        length: Desired length (max 32).

    Returns:
        Short alphanumeric identifier string.
    """
    return uuid.uuid4().hex[:max(1, min(length, 32))]


# ---------------------------------------------------------------------------
# Date / time helpers
# ---------------------------------------------------------------------------

def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """
    Format a datetime object as a string.

    Args:
        dt: The datetime to format.
        fmt: strftime-compatible format string.

    Returns:
        Formatted date-time string.
    """
    return dt.strftime(fmt)


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------

def calculate_offset(page: int, page_size: int) -> int:
    """
    Calculate the SQL OFFSET for a given page number.

    Args:
        page: 1-indexed page number.
        page_size: Number of items per page.

    Returns:
        Zero-based row offset.
    """
    return (max(1, page) - 1) * page_size


def total_pages(total_items: int, page_size: int) -> int:
    """
    Return the total number of pages.

    Args:
        total_items: Total record count.
        page_size: Number of items per page.

    Returns:
        Total page count (minimum 1).
    """
    if page_size <= 0:
        return 1
    return max(1, math.ceil(total_items / page_size))


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.

    Example:
        "Major Flood Event" → "major-flood-event"

    Args:
        text: Input string.

    Returns:
        Lowercase, hyphen-separated slug.
    """
    return "-".join(text.lower().split())


def md5_hash(value: str) -> str:
    """
    Return the MD5 hex digest of a string.

    Intended for non-security uses such as cache keys or ETags.

    Args:
        value: Input string.

    Returns:
        32-character hex digest.
    """
    return hashlib.md5(value.encode("utf-8")).hexdigest()
