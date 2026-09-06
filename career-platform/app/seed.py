"""Seed the database with everything the app needs to be useful on first run.

Seeding is idempotent and additive: it inserts what is missing and leaves
existing rows (and Jeff's history) alone. Running it again after a code update
picks up new primer text or new starter questions without wiping progress.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from app import db
from app.academy import starter_questions
from app.academy.modules import LEVEL_SCORES, MODULES

PRIMER_DIR = Path(__file__).resolve().parent / "academy" / "primers"

# Matches "- **Term** - definition" or "- **Term**: definition" glossary lines.
GLOSSARY_LINE = re.compile(r"^\s*[-*]\s+\*\*(?P<term>[^*]+)\*\*\s*[-:—]\s*(?P<definition>.+)$")


def seed_all(conn: sqlite3.Connection) -> dict[str, int]:
    """Seed modules, gap baseline, primers, glossary and starter quizzes."""
    counts = {
        "modules": seed_modules(conn),
        "gap_baseline": seed_gap_baseline(conn),
        "primers": seed_primers(conn),
        "glossary": seed_glossary(conn),
        "questions": seed_starter_questions(conn),
    }
    # Put priorities on the normalised scale straight away. Without this a
    # freshly seeded database reports priorities that are not comparable with
    # the ones every later recompute produces.
    from app.gap import engine

    engine.recompute(conn, reason="seed")
    return counts


def seed_modules(conn: sqlite3.Connection) -> int:
    """Insert the five fixed modules. Names and blurbs are refreshed in place;
    the rows themselves are never deleted, so history keeps its foreign keys."""
    written = 0
    for module in MODULES:
        conn.execute(
            """
            INSERT INTO academy_modules (key, name, blurb, sort_order, weight_damping)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                name = excluded.name,
                blurb = excluded.blurb,
                sort_order = excluded.sort_order,
                weight_damping = excluded.weight_damping
            """,
            (module.key, module.name, module.blurb, module.sort_order, module.weight_damping),
        )
        written += 1
    return written


def seed_gap_baseline(conn: sqlite3.Connection) -> int:
    """Load the spec 2.5 diagnostic baseline.

    Only inserts. Once the gap engine has recomputed priorities from live job
    data, re-seeding must not reset them - the baseline is a starting point,
    not a permanent truth.
    """
    written = 0
    now = db.utcnow()
    for module in MODULES:
        exists = db.query_one(
            conn, "SELECT 1 FROM gap_state WHERE module_key = ?", (module.key,)
        )
        if exists:
            continue
        score = LEVEL_SCORES[module.baseline_level]
        db.insert(
            conn,
            "gap_state",
            {
                "module_key": module.key,
                "baseline_level": module.baseline_level,
                "baseline_score": score,
                "baseline_note": module.baseline_note,
                "demand_score": 0.0,
                "quiz_accuracy": None,
                "quiz_attempts": 0,
                "feedback_bias": 1.0,
                # Placeholder only - seed_all() recomputes and normalises these
                # before returning, so this value is never read as-is.
                "priority": 0.0,
                "updated_at": now,
            },
        )
        written += 1
    return written


def _split_primer(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (body, glossary_pairs).

    The glossary lives at the bottom of each primer file under a "## Glossary"
    heading so it is written and reviewed alongside the prose, then extracted
    into its own table for the glossary view.
    """
    parts = re.split(r"^##\s+Glossary\s*$", text, maxsplit=1, flags=re.MULTILINE)
    body = parts[0].rstrip()
    # Drop the file's leading H1: the module name is already shown as the page
    # heading, so keeping it would print the title twice.
    body = re.sub(r"\A#\s+.*\n+", "", body)
    glossary: list[tuple[str, str]] = []
    if len(parts) == 2:
        for line in parts[1].splitlines():
            match = GLOSSARY_LINE.match(line)
            if match:
                glossary.append(
                    (match.group("term").strip(), match.group("definition").strip())
                )
    return body, glossary


def seed_primers(conn: sqlite3.Connection) -> int:
    """Load built-in primer text, versioning up when the file has changed.

    Primers are "stable, substantial" (spec 2.2) - they change only when the
    text on disk changes, not on a refresh schedule.
    """
    written = 0
    now = db.utcnow()
    for module in MODULES:
        path = PRIMER_DIR / f"{module.key}.md"
        if not path.exists():
            continue
        body, _ = _split_primer(path.read_text(encoding="utf-8"))

        current = db.query_one(
            conn,
            "SELECT id, version, body FROM primers WHERE module_key = ? AND is_current = 1",
            (module.key,),
        )
        if current and current["body"] == body:
            continue

        next_version = (current["version"] + 1) if current else 1
        if current:
            conn.execute("UPDATE primers SET is_current = 0 WHERE id = ?", (current["id"],))
        db.insert(
            conn,
            "primers",
            {
                "module_key": module.key,
                "version": next_version,
                "body": body,
                "source": "builtin",
                "is_current": 1,
                "created_at": now,
            },
        )
        written += 1
    return written


def seed_glossary(conn: sqlite3.Connection) -> int:
    written = 0
    for module in MODULES:
        path = PRIMER_DIR / f"{module.key}.md"
        if not path.exists():
            continue
        _, glossary = _split_primer(path.read_text(encoding="utf-8"))
        for term, definition in glossary:
            conn.execute(
                """
                INSERT INTO glossary_terms (module_key, term, definition)
                VALUES (?, ?, ?)
                ON CONFLICT(module_key, term) DO UPDATE SET definition = excluded.definition
                """,
                (module.key, term, definition),
            )
            written += 1
    return written


def seed_starter_questions(conn: sqlite3.Connection) -> int:
    """Load the hand-written question bank.

    These are written from the primer text, so the daily quiz works on day one
    with no API key. The research layer adds generated questions on top of
    these; both live in the same table and rotate together.
    """
    written = 0
    now = db.utcnow()
    for module_key, questions in starter_questions.QUESTIONS.items():
        for question in questions:
            cur = conn.execute(
                """
                INSERT INTO quiz_questions
                    (module_key, question, options_json, correct_index, explanation,
                     style, difficulty, primer_version, source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'builtin', 'active', ?)
                ON CONFLICT(module_key, question) DO NOTHING
                """,
                (
                    module_key,
                    question["question"],
                    json.dumps(question["options"]),
                    question["correct_index"],
                    question["explanation"],
                    question.get("style", "scenario"),
                    question.get("difficulty", "core"),
                    1,
                    now,
                ),
            )
            written += cur.rowcount if cur.rowcount > 0 else 0
    return written
