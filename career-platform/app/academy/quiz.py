"""The daily quiz: rotation, serving, answering, and question generation.

Rotation is the interesting part (spec 2.3). Questions rotate across all five
modules regardless of what Jeff happens to be reading, weighted by the gap
engine so most days lean toward the weakest areas, with a deliberate slice
drawn uniformly so the stronger modules stay warm.

Selection is seeded by the date, so opening the app twice in one day shows the
same quiz rather than reshuffling, while different days differ.
"""

from __future__ import annotations

import json
import random
import sqlite3
from typing import Optional

import config
from app import db
from app.academy.modules import MODULE_KEYS, MODULES_BY_KEY
from app.gap import engine as gap_engine
from app.jobs import scoring
from app.research.client import ResearchClient, get_client


# ---------------------------------------------------------------------------
# Building the day's quiz
# ---------------------------------------------------------------------------

def get_or_build_daily(
    conn: sqlite3.Connection, quiz_date: Optional[str] = None
) -> list[dict]:
    """Return today's questions, building the set on first request of the day."""
    day = quiz_date or db.today()
    existing = _attempts_for(conn, day)
    if existing:
        return existing
    _build_daily(conn, day)
    return _attempts_for(conn, day)


def _build_daily(conn: sqlite3.Connection, day: str) -> None:
    modules = choose_modules(gap_engine.priorities(conn), day)
    now = db.utcnow()
    used: set[int] = set()

    for module_key in modules:
        question = pick_question(conn, module_key, exclude=used)
        if question is None:
            # This module has no usable question; fall back to any module that
            # does, so the day is never short.
            question = pick_question(conn, None, exclude=used)
        if question is None:
            continue
        used.add(int(question["id"]))
        db.insert(
            conn,
            "quiz_attempts",
            {
                "question_id": question["id"],
                "module_key": question["module_key"],
                "quiz_date": day,
                "served_at": now,
            },
        )


def choose_modules(priorities: dict[str, float], day: str) -> list[str]:
    """Pick which modules today's questions come from.

    Most slots are sampled in proportion to gap priority. A fixed share is drawn
    uniformly instead, which is what keeps a strong module from disappearing
    entirely and losing retention.
    """
    total = config.QUESTIONS_PER_DAY
    uniform_slots = max(1, round(total * config.RETENTION_MIX)) if total > 1 else 0
    weighted_slots = total - uniform_slots

    rng = random.Random(f"quiz-{day}")
    keys = [key for key in MODULE_KEYS if key in priorities] or list(MODULE_KEYS)
    weights = [max(priorities.get(key, 0.0), 0.001) for key in keys]

    chosen = rng.choices(keys, weights=weights, k=weighted_slots)
    chosen += rng.choices(keys, k=uniform_slots)
    rng.shuffle(chosen)
    return chosen


def pick_question(
    conn: sqlite3.Connection, module_key: Optional[str], exclude: set[int]
) -> Optional[sqlite3.Row]:
    """Choose a question, preferring ones Jeff has not seen recently.

    Order of preference: never served, then served longest ago outside the
    cooldown, then anything at all rather than serving a short day.
    """
    cutoff = scoring.cutoff_date(config.QUESTION_COOLDOWN_DAYS)
    params: list = []
    module_clause = ""
    if module_key:
        module_clause = "AND q.module_key = ?"
        params.append(module_key)

    # A question's recency is the most recent time it was served.
    sql = f"""
        SELECT q.*, MAX(a.served_at) AS last_served
        FROM quiz_questions q
        LEFT JOIN quiz_attempts a ON a.question_id = q.id
        WHERE q.status = 'active' {module_clause}
        GROUP BY q.id
        ORDER BY
            CASE WHEN MAX(a.served_at) IS NULL THEN 0
                 WHEN MAX(a.served_at) < ? THEN 1
                 ELSE 2 END,
            MAX(a.served_at) ASC,
            q.id ASC
    """
    params.append(cutoff)
    for row in db.query(conn, sql, params):
        if int(row["id"]) not in exclude:
            return row
    return None


def _attempts_for(conn: sqlite3.Connection, day: str) -> list[dict]:
    rows = db.query(
        conn,
        """
        SELECT a.id AS attempt_id, a.chosen_index, a.is_correct, a.answered_at,
               q.id AS question_id, q.question, q.options_json, q.correct_index,
               q.explanation, q.style, q.module_key, m.name AS module_name
        FROM quiz_attempts a
        JOIN quiz_questions q ON q.id = a.question_id
        JOIN academy_modules m ON m.key = a.module_key
        WHERE a.quiz_date = ?
        ORDER BY a.id
        """,
        (day,),
    )
    return [
        {
            "attempt_id": row["attempt_id"],
            "question_id": row["question_id"],
            "module_key": row["module_key"],
            "module_name": row["module_name"],
            "question": row["question"],
            "options": json.loads(row["options_json"]),
            "correct_index": row["correct_index"],
            "explanation": row["explanation"],
            "style": row["style"],
            "chosen_index": row["chosen_index"],
            "is_correct": row["is_correct"],
            "answered": row["answered_at"] is not None,
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Answering
# ---------------------------------------------------------------------------

def answer(conn: sqlite3.Connection, attempt_id: int, chosen_index: int) -> Optional[dict]:
    """Record an answer. Returns the graded question, or None if already done."""
    row = db.query_one(
        conn,
        """
        SELECT a.id, a.answered_at, a.quiz_date, q.correct_index, q.explanation,
               q.options_json
        FROM quiz_attempts a
        JOIN quiz_questions q ON q.id = a.question_id
        WHERE a.id = ?
        """,
        (attempt_id,),
    )
    if row is None or row["answered_at"] is not None:
        return None

    options = json.loads(row["options_json"])
    if not 0 <= chosen_index < len(options):
        return None

    is_correct = 1 if chosen_index == row["correct_index"] else 0
    db.update(
        conn,
        "quiz_attempts",
        attempt_id,
        {
            "chosen_index": chosen_index,
            "is_correct": is_correct,
            "answered_at": db.utcnow(),
        },
    )

    # Once the day is fully answered, fold the new evidence into the gap
    # weights. Doing it here rather than per answer keeps the history readable.
    remaining = db.scalar(
        conn,
        "SELECT COUNT(*) FROM quiz_attempts WHERE quiz_date = ? AND answered_at IS NULL",
        (row["quiz_date"],),
        0,
    )
    if remaining == 0:
        gap_engine.recompute(conn, reason="daily quiz completed")

    return {
        "is_correct": bool(is_correct),
        "correct_index": row["correct_index"],
        "explanation": row["explanation"],
    }


# ---------------------------------------------------------------------------
# Progress, for the dashboard
# ---------------------------------------------------------------------------

def today_progress(conn: sqlite3.Connection, day: Optional[str] = None) -> dict:
    day = day or db.today()
    rows = db.query(
        conn,
        """
        SELECT is_correct, answered_at FROM quiz_attempts WHERE quiz_date = ?
        """,
        (day,),
    )
    answered = [row for row in rows if row["answered_at"]]
    return {
        "total": len(rows),
        "answered": len(answered),
        "correct": sum(1 for row in answered if row["is_correct"]),
        "complete": bool(rows) and len(answered) == len(rows),
    }


def streak(conn: sqlite3.Connection) -> int:
    """Consecutive days ending today (or yesterday) with a completed quiz."""
    from datetime import date, timedelta

    rows = db.query(
        conn,
        """
        SELECT quiz_date,
               COUNT(*) AS total,
               SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) AS done
        FROM quiz_attempts
        GROUP BY quiz_date
        HAVING done = total
        ORDER BY quiz_date DESC
        """,
    )
    completed = {row["quiz_date"] for row in rows}
    if not completed:
        return 0

    cursor = date.today()
    if cursor.isoformat() not in completed:
        cursor -= timedelta(days=1)

    count = 0
    while cursor.isoformat() in completed:
        count += 1
        cursor -= timedelta(days=1)
    return count


def module_performance(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = db.query(
        conn,
        """
        SELECT module_key, COUNT(*) AS attempts,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct
        FROM quiz_attempts WHERE answered_at IS NOT NULL
        GROUP BY module_key
        """,
    )
    return {
        row["module_key"]: {
            "attempts": int(row["attempts"]),
            "correct": int(row["correct"] or 0),
            "accuracy": (float(row["correct"] or 0) / int(row["attempts"]))
            if row["attempts"]
            else None,
        }
        for row in rows
    }


# ---------------------------------------------------------------------------
# Generating new questions from the primers
# ---------------------------------------------------------------------------

GENERATION_SYSTEM = """
You write multiple-choice questions that test whether a senior executive has
genuinely understood a topic, rather than whether they can recognise a phrase.

The reader is preparing to compete for Head of AI Strategy roles. Questions
should be the kind of thing that would come up in a serious interview or an
operating committee, not a certification exam.
""".strip()


GENERATION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exactly four options.",
                    },
                    "correct_index": {"type": "integer"},
                    "explanation": {
                        "type": "string",
                        "description": "Two to four sentences: why the answer is right and why the tempting wrong one is wrong.",
                    },
                    "style": {"type": "string", "enum": ["scenario", "recall"]},
                },
                "required": ["question", "options", "correct_index", "explanation", "style"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}


def generate_questions(
    module_key: str,
    count: int = 6,
    client: Optional[ResearchClient] = None,
) -> tuple[int, str]:
    """Write new questions from a module's primer. Returns (added, message).

    Questions come from the primer text specifically, not from the external
    links, so the quiz never assumes Jeff clicked through (spec 2.3).
    """
    research = client or get_client()
    if not research.available:
        return 0, (
            "Generating new questions needs an Anthropic API key. The built-in "
            "question bank still rotates without it."
        )

    module = MODULES_BY_KEY.get(module_key)
    if module is None:
        return 0, "Unknown module."

    with db.session() as conn:
        primer = db.query_one(
            conn,
            "SELECT body, version FROM primers WHERE module_key = ? AND is_current = 1",
            (module_key,),
        )
        existing = [
            row["question"]
            for row in db.query(
                conn,
                "SELECT question FROM quiz_questions WHERE module_key = ?",
                (module_key,),
            )
        ]

    if primer is None:
        return 0, "That module has no primer to generate from."

    already = "\n".join(f"  - {q}" for q in existing[:60])
    prompt = f"""Below is the full primer for the module "{module.name}".

Write {count} new multiple-choice questions drawn ONLY from this primer's
content. Every question must be answerable by someone who has read the primer
carefully and nothing else.

Requirements:
  - Exactly four options each, all genuinely plausible to someone who half-knows
    the material. No filler options, no joke answers, no "all of the above".
  - Favour scenario questions - a situation, then the judgement it calls for -
    over definition recall. Aim for at least two thirds scenario style.
  - Vary which position holds the correct answer.
  - The explanation should teach, not just assert: say why the right answer is
    right and why the most tempting wrong answer fails.
  - Do NOT duplicate or lightly reword any of the existing questions listed
    after the primer.

--- PRIMER ---

{primer['body']}

--- EXISTING QUESTIONS (do not repeat these) ---

{already or "  (none yet)"}
"""

    result = research.research(
        purpose=f"quiz:generate:{module_key}",
        system=GENERATION_SYSTEM,
        prompt=prompt,
        schema=GENERATION_SCHEMA,
        use_search=False,
    )
    if not result.ok:
        return 0, result.error or "Question generation failed."

    added = 0
    now = db.utcnow()
    with db.session() as conn:
        for item in result.items:
            options = item.get("options") or []
            correct = item.get("correct_index")
            question_text = (item.get("question") or "").strip()
            if (
                not question_text
                or len(options) < 2
                or not isinstance(correct, int)
                or not 0 <= correct < len(options)
            ):
                continue
            cur = conn.execute(
                """
                INSERT INTO quiz_questions
                    (module_key, question, options_json, correct_index, explanation,
                     style, difficulty, primer_version, source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'core', ?, 'generated', 'active', ?)
                ON CONFLICT(module_key, question) DO NOTHING
                """,
                (
                    module_key,
                    question_text,
                    json.dumps([str(option) for option in options]),
                    correct,
                    (item.get("explanation") or "").strip(),
                    item.get("style") or "scenario",
                    primer["version"],
                    now,
                ),
            )
            added += 1 if cur.rowcount else 0

    return added, f"Added {added} new questions to {module.name}."
