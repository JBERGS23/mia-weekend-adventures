"""Settings for the AI Career Platform.

Everything configurable lives here so there are no magic numbers buried in the
modules. Values can be overridden with environment variables, but the defaults
are what Jeff actually wants, so the app works with no setup beyond an API key.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

# The whole app is one SQLite file. Back it up by copying it.
DATABASE_PATH = Path(os.environ.get("CAREER_DB", BASE_DIR / "data" / "career.db"))


# ---------------------------------------------------------------------------
# Research layer (Anthropic API with server-side web search)
# ---------------------------------------------------------------------------

# The app degrades gracefully without this: browsing, quizzes on the built-in
# primers, shortlisting and networking review all still work. Only live
# scanning and content refresh need it.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

RESEARCH_MODEL = os.environ.get("CAREER_MODEL", "claude-opus-5")

# How hard the model works per research call. "high" is the sweet spot for
# this kind of read-and-extract work; raise to "xhigh" if results feel thin.
RESEARCH_EFFORT = os.environ.get("CAREER_EFFORT", "high")

# Cap on web searches per source query, to keep a scan bounded and cheap.
MAX_SEARCHES_PER_SOURCE = int(os.environ.get("CAREER_MAX_SEARCHES", "8"))

# Server-tool loops can pause after 10 internal iterations; this is how many
# times we resume before giving up on one source.
MAX_PAUSE_RESUMES = 3

# Per-call timeout in seconds. Web-search research calls are slow by nature.
RESEARCH_TIMEOUT = float(os.environ.get("CAREER_TIMEOUT", "600"))


# ---------------------------------------------------------------------------
# Module A: job scanner
# ---------------------------------------------------------------------------

# Spec 1.1 - target titles, roughly in priority order.
TARGET_TITLES = [
    "Head of AI Strategy",
    "Head of AI Transformation",
    "VP of AI Strategy",
    "Chief AI Officer",
    "VP Strategy / Head of Strategy with an explicit AI transformation mandate",
]

# Spec 1.3 - compensation. Never used as a hard filter.
COMP_FLOOR = 250_000
COMP_TARGET = 300_000

# Spec 1.5 - "genuinely new postings from roughly the past week".
FRESHNESS_DAYS = int(os.environ.get("CAREER_FRESHNESS_DAYS", "9"))

# Postings with no date at all are still surfaced if they are newly seen; this
# is how many days a dateless posting stays in the "new" view.
UNDATED_GRACE_DAYS = 7

# Below this fit score a posting is stored in the archive but kept out of the
# main review queue, so the queue stays readable.
MIN_FIT_TO_SURFACE = float(os.environ.get("CAREER_MIN_FIT", "0.45"))


# ---------------------------------------------------------------------------
# Module B: academy
# ---------------------------------------------------------------------------

QUESTIONS_PER_DAY = int(os.environ.get("CAREER_QUIZ_COUNT", "5"))

# Rotation is gap-weighted, but never purely so: this share of each day's
# questions is drawn uniformly across all five modules to maintain retention
# in the stronger ones (spec 2.3).
RETENTION_MIX = 0.2

# Don't repeat a question that was served within this many days, unless the
# module has run out of unseen questions.
QUESTION_COOLDOWN_DAYS = 21

# How many deeper-dive links to keep live per module (spec 2.2).
RESOURCES_PER_MODULE = 8

# Refresh external links at most this often, to avoid burning API calls.
RESOURCE_REFRESH_DAYS = 14


# ---------------------------------------------------------------------------
# Module C: networking
# ---------------------------------------------------------------------------

# Spec 3.1 - hard cap. This module fails if it ever feels like a task list.
NETWORKING_MIN_ACTIVE = 5
NETWORKING_MAX_ACTIVE = 10

# Spec 3.5 - latent-demand targets always keep a seat at the table.
LATENT_RESERVED_SLOTS = 2

# Targets older than this decay in score so the list keeps moving.
TARGET_STALE_DAYS = 30


# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("CAREER_SECRET_KEY", "local-single-user-not-a-secret")
HOST = os.environ.get("CAREER_HOST", "127.0.0.1")
PORT = int(os.environ.get("CAREER_PORT", "5001"))
DEBUG = os.environ.get("CAREER_DEBUG", "0") == "1"
