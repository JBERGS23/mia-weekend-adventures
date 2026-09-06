"""Fit scoring, compensation handling, and dedupe fingerprints.

Scoring is deliberately part-deterministic. The model contributes a relevance
judgement, but the rest of the score comes from rules written here, so that a
score can always be explained in a sentence and tuned without re-running a scan.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

import config

# ---------------------------------------------------------------------------
# Normalisation and dedupe
# ---------------------------------------------------------------------------

_PUNCT = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")

# Suffixes that show up inconsistently and would otherwise split duplicates.
_COMPANY_NOISE = (
    " inc", " inc.", " llc", " ltd", " limited", " corp", " corporation",
    " co", " company", " plc", " gmbh", " sa", " ag", " nv", " group",
    " holdings", " technologies", " technology", " labs",
)

# Title decorations that vary between boards for the same role.
_TITLE_NOISE = (
    "senior", "sr", "global", "us", "usa", "north america", "emea",
    "remote", "hybrid", "full time", "full-time", "contract", "f/m/d", "m/f/d",
)


def normalise_company(value: str) -> str:
    text = _PUNCT.sub(" ", (value or "").lower())
    text = _SPACES.sub(" ", text).strip()
    changed = True
    while changed:
        changed = False
        for suffix in _COMPANY_NOISE:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                changed = True
    return text


def normalise_title(value: str) -> str:
    text = _PUNCT.sub(" ", (value or "").lower())
    tokens = [token for token in text.split() if token not in _TITLE_NOISE]
    # "vp of ai strategy" and "vice president ai strategy" should collapse.
    expanded: list[str] = []
    for token in tokens:
        if token in ("vice", "president") and "vp" not in expanded:
            if token == "president" and expanded and expanded[-1] == "vice":
                expanded[-1] = "vp"
                continue
        if token in ("of", "the", "and", "for", "a"):
            continue
        expanded.append(token)
    return " ".join(expanded).strip()


def fingerprint(company: str, title: str, location: str = "") -> str:
    """Stable identity for a posting, used to dedupe across sources and runs.

    Location is included only at city granularity, so the same role listed as
    "New York, NY" and "New York, NY (Hybrid)" collapses, while genuinely
    different postings of the same title in different cities do not.
    """
    # Split on the comma first: punctuation stripping would remove it, and then
    # "New York, NY (Hybrid)" would never collapse onto "New York, NY".
    city = (location or "").lower().split(",")[0]
    city = _SPACES.sub(" ", _PUNCT.sub(" ", city)).strip()
    raw = f"{normalise_company(company)}|{normalise_title(title)}|{city}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def hash_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    cleaned = url.split("?")[0].rstrip("/").lower()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------

VALID_CONFIDENCE = ("Confirmed", "Estimated", "Unknown")


def clean_compensation(posting: dict) -> dict:
    """Sanity-check what the model reported about pay.

    Spec 1.3: missing compensation is never a filter. This function only makes
    the confidence flag honest - if there are no numbers, the confidence is
    Unknown regardless of what the model claimed.
    """
    comp_min = _as_int(posting.get("comp_min"))
    comp_max = _as_int(posting.get("comp_max"))
    confidence = posting.get("comp_confidence") or "Unknown"
    note = (posting.get("comp_note") or "").strip()

    if confidence not in VALID_CONFIDENCE:
        confidence = "Unknown"

    # Guard against a stated hourly or thousands-denominated figure.
    for value in (comp_min, comp_max):
        if value is not None and 0 < value < 1000:
            comp_min = comp_max = None
            confidence = "Unknown"
            note = (note + " (discarded an implausible figure)").strip()
            break

    if comp_min is None and comp_max is None:
        confidence = "Unknown"
    elif comp_min is not None and comp_max is not None and comp_min > comp_max:
        comp_min, comp_max = comp_max, comp_min

    return {
        "comp_min": comp_min,
        "comp_max": comp_max,
        "comp_currency": (posting.get("comp_currency") or "USD")[:8],
        "comp_confidence": confidence,
        "comp_note": note,
    }


def comp_fit(comp: dict) -> float:
    """How well pay matches the target, on a 0..1 scale.

    Unknown scores 0.6 rather than 0, deliberately. A strong role with no stated
    compensation must not be scored out of the review queue, because most senior
    postings do not state compensation at all.
    """
    top = comp.get("comp_max") or comp.get("comp_min")
    if top is None:
        return 0.6
    if top >= config.COMP_TARGET:
        return 1.0
    if top >= config.COMP_FLOOR:
        return 0.85
    if top >= config.COMP_FLOOR * 0.8:
        return 0.5
    return 0.2


def comp_display(comp: dict) -> str:
    """A short human-readable pay string for the UI."""
    low, high = comp.get("comp_min"), comp.get("comp_max")
    currency = "$" if (comp.get("comp_currency") or "USD") == "USD" else ""
    if low and high:
        return f"{currency}{low:,} - {currency}{high:,}"
    if high:
        return f"up to {currency}{high:,}"
    if low:
        return f"{currency}{low:,}+"
    return "Not stated"


def below_floor(comp: dict) -> bool:
    top = comp.get("comp_max") or comp.get("comp_min")
    return top is not None and top < config.COMP_FLOOR


# ---------------------------------------------------------------------------
# Title and seniority matching
# ---------------------------------------------------------------------------

# Each signal is a set of tokens that must all be present in the normalised
# title, checked most specific first. Token matching rather than substring
# matching, so "Head of Global AI Strategy" and "VP, Corporate Strategy" both
# match rather than falling through to the weakest rule.
_TITLE_SIGNALS: tuple[tuple[tuple[str, ...], float], ...] = (
    (("chief", "ai", "officer"), 1.0),
    (("head", "ai", "strategy"), 1.0),
    (("head", "ai", "transformation"), 1.0),
    (("vp", "ai", "strategy"), 1.0),
    (("vp", "ai", "transformation"), 1.0),
    (("chief", "ai"), 0.95),
    (("chief", "artificial", "intelligence"), 0.95),
    (("head", "ai"), 0.85),
    (("vp", "ai"), 0.85),
    (("director", "ai", "strategy"), 0.85),
    (("ai", "strategy"), 0.80),
    (("ai", "transformation"), 0.80),
    (("chief", "strategy"), 0.62),
    (("head", "strategy"), 0.62),
    (("vp", "strategy"), 0.62),
    (("head", "digital", "transformation"), 0.58),
    (("vp", "digital", "transformation"), 0.58),
    (("head", "transformation"), 0.55),
    (("vp", "transformation"), 0.55),
    (("operating", "partner"), 0.50),
    (("value", "creation"), 0.50),
    (("strategy",), 0.35),
    (("transformation",), 0.35),
)

_SENIORITY_FIT = {
    "c_suite": 1.0,
    "head_vp": 1.0,
    "director": 0.55,
    "other": 0.3,
}


def title_match(title: str) -> float:
    """Score a title against the target list. First matching signal wins."""
    tokens = set(normalise_title(title).split())
    for required, score in _TITLE_SIGNALS:
        if all(token in tokens for token in required):
            return score
    return 0.2


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------

def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def freshness_factor(posted_at: Any, today: Optional[date] = None) -> float:
    """Multiplier that pushes stale postings out of the review queue.

    An undated posting is treated as neutral rather than penalised, because
    plenty of legitimate career pages do not show dates.
    """
    posted = parse_date(posted_at)
    if posted is None:
        return 0.95
    reference = today or date.today()
    age = (reference - posted).days
    if age < 0:
        return 1.0
    if age <= config.FRESHNESS_DAYS:
        return 1.0
    if age <= 30:
        return 0.9
    if age <= 60:
        return 0.75
    if age <= 120:
        return 0.55
    return 0.35


def is_fresh(posted_at: Any, first_seen_at: Any, today: Optional[date] = None) -> bool:
    """Does this belong in the "new this week" view?

    A posting counts as fresh if it was posted recently, or - when the source
    gave no date - if we only just saw it for the first time.
    """
    reference = today or date.today()
    posted = parse_date(posted_at)
    if posted is not None:
        return (reference - posted).days <= config.FRESHNESS_DAYS
    seen = parse_date(first_seen_at)
    if seen is None:
        return True
    return (reference - seen).days <= config.UNDATED_GRACE_DAYS


# ---------------------------------------------------------------------------
# The fit score
# ---------------------------------------------------------------------------

# Weights sum to 1.0. Model relevance carries the most weight but not a
# majority, so a posting cannot be carried by the model's opinion alone.
WEIGHTS = {
    "relevance": 0.42,
    "title": 0.20,
    "mandate": 0.16,
    "comp": 0.11,
    "seniority": 0.11,
}


def score_posting(posting: dict, comp: dict, today: Optional[date] = None) -> tuple[float, str]:
    """Return (fit_score, one-line rationale).

    The rationale is stored and shown in the UI, so a low score is never a
    mystery.
    """
    relevance = _clamp(_as_float(posting.get("relevance"), 0.5))
    title_score = title_match(posting.get("title", ""))
    mandate_score = 1.0 if posting.get("ai_mandate") else 0.35
    comp_score = comp_fit(comp)
    seniority_score = _SENIORITY_FIT.get(posting.get("seniority") or "other", 0.3)

    raw = (
        WEIGHTS["relevance"] * relevance
        + WEIGHTS["title"] * title_score
        + WEIGHTS["mandate"] * mandate_score
        + WEIGHTS["comp"] * comp_score
        + WEIGHTS["seniority"] * seniority_score
    )
    score = _clamp(raw * freshness_factor(posting.get("posted_at"), today))

    parts = [
        f"relevance {relevance:.2f}",
        f"title {title_score:.2f}",
        "explicit AI mandate" if posting.get("ai_mandate") else "no explicit AI mandate",
        f"comp {comp['comp_confidence'].lower()}",
    ]
    if below_floor(comp):
        parts.append("below comp floor")
    note = (posting.get("relevance_note") or "").strip()
    rationale = "; ".join(parts)
    if note:
        rationale = f"{rationale}. {note}"
    return round(score, 4), rationale


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def cutoff_date(days: int, today: Optional[date] = None) -> str:
    return ((today or date.today()) - timedelta(days=days)).isoformat()
