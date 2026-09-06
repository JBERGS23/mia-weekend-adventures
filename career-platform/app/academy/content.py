"""Academy content: primers, glossary, deeper-dive links, and feedback.

Two layers per module (spec 2.2):

  * The **primer** is stable and substantial. It lives in the repository as
    markdown, is loaded at seed time, and changes only when the underlying
    concepts move - never on a refresh schedule.
  * The **deeper-dive links** are living. They are sourced by fresh web search
    each time rather than from a static library, and are added, reordered and
    retired as relevance changes.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

import config
from app import db
from app.academy.modules import MODULES, MODULES_BY_KEY
from app.research.client import ResearchClient, get_client


# ---------------------------------------------------------------------------
# Reading module content
# ---------------------------------------------------------------------------

def list_modules(conn: sqlite3.Connection) -> list[dict]:
    """Every module with its current priority and progress, in fixed order."""
    rows = db.query(
        conn,
        """
        SELECT m.*, g.priority, g.baseline_level, g.baseline_note, g.quiz_accuracy,
               g.quiz_attempts, g.demand_score
        FROM academy_modules m
        LEFT JOIN gap_state g ON g.module_key = m.key
        ORDER BY m.sort_order
        """,
    )
    modules = []
    for row in rows:
        modules.append(
            {
                **dict(row),
                "resource_count": db.scalar(
                    conn,
                    "SELECT COUNT(*) FROM resources WHERE module_key = ? AND status = 'active'",
                    (row["key"],),
                    0,
                ),
                "question_count": db.scalar(
                    conn,
                    "SELECT COUNT(*) FROM quiz_questions WHERE module_key = ? AND status = 'active'",
                    (row["key"],),
                    0,
                ),
            }
        )
    return modules


def get_module(conn: sqlite3.Connection, module_key: str) -> Optional[dict]:
    row = db.query_one(
        conn,
        """
        SELECT m.*, g.priority, g.baseline_level, g.baseline_note, g.quiz_accuracy,
               g.quiz_attempts, g.demand_score
        FROM academy_modules m
        LEFT JOIN gap_state g ON g.module_key = m.key
        WHERE m.key = ?
        """,
        (module_key,),
    )
    return dict(row) if row else None


def get_primer(conn: sqlite3.Connection, module_key: str) -> Optional[sqlite3.Row]:
    return db.query_one(
        conn,
        "SELECT * FROM primers WHERE module_key = ? AND is_current = 1",
        (module_key,),
    )


def glossary(conn: sqlite3.Connection, module_key: Optional[str] = None) -> list[sqlite3.Row]:
    if module_key:
        return db.query(
            conn,
            "SELECT * FROM glossary_terms WHERE module_key = ? ORDER BY term",
            (module_key,),
        )
    return db.query(
        conn,
        """
        SELECT g.*, m.name AS module_name FROM glossary_terms g
        JOIN academy_modules m ON m.key = g.module_key
        ORDER BY g.term
        """,
    )


def resources(conn: sqlite3.Connection, module_key: str) -> list[sqlite3.Row]:
    return db.query(
        conn,
        """
        SELECT * FROM resources
        WHERE module_key = ? AND status = 'active'
        ORDER BY rank DESC, added_at DESC
        """,
        (module_key,),
    )


# ---------------------------------------------------------------------------
# Feedback (spec 2.4)
# ---------------------------------------------------------------------------

def record_feedback(
    conn: sqlite3.Connection, module_key: str, signal: str, note: str = ""
) -> bool:
    """Record "more of this" / "less of this" and let it bias future weighting."""
    if signal not in ("more", "less") or module_key not in MODULES_BY_KEY:
        return False
    db.insert(
        conn,
        "module_feedback",
        {
            "module_key": module_key,
            "signal": signal,
            "note": (note or "").strip() or None,
            "created_at": db.utcnow(),
        },
    )
    from app.gap import engine

    engine.recompute(conn, reason=f"feedback: {signal} on {module_key}")
    return True


def feedback_summary(conn: sqlite3.Connection, module_key: str) -> dict:
    row = db.query_one(
        conn,
        """
        SELECT SUM(CASE WHEN signal = 'more' THEN 1 ELSE 0 END) AS more_count,
               SUM(CASE WHEN signal = 'less' THEN 1 ELSE 0 END) AS less_count
        FROM module_feedback WHERE module_key = ?
        """,
        (module_key,),
    )
    return {
        "more": int(row["more_count"] or 0) if row else 0,
        "less": int(row["less_count"] or 0) if row else 0,
    }


def recent_notes(conn: sqlite3.Connection, module_key: str, limit: int = 5):
    return db.query(
        conn,
        """
        SELECT * FROM module_feedback
        WHERE module_key = ? AND note IS NOT NULL
        ORDER BY created_at DESC LIMIT ?
        """,
        (module_key, limit),
    )


# ---------------------------------------------------------------------------
# Refreshing the deeper-dive links
# ---------------------------------------------------------------------------

RESOURCE_SYSTEM = """
You find genuinely good learning material for a senior executive who already
knows the basics and is preparing to compete for Head of AI Strategy roles.

You have a strong bias against beginner content, vendor marketing, and SEO
listicles. You would rather return four excellent resources than twelve padded
ones, and you only report things you actually found and looked at.
""".strip()


RESOURCE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "resources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "format": {
                        "type": "string",
                        "enum": ["article", "video", "podcast", "course", "paper"],
                    },
                    "publisher": {"type": "string"},
                    "published_at": {"type": ["string", "null"]},
                    "why": {
                        "type": "string",
                        "description": "One sentence: what this specifically gives the reader that the primer does not.",
                    },
                    "rank": {
                        "type": "number",
                        "description": "0 to 1 - how strongly this earns a slot.",
                    },
                },
                "required": ["title", "url", "format", "publisher", "published_at", "why", "rank"],
                "additionalProperties": False,
            },
        },
        "coverage_note": {"type": "string"},
    },
    "required": ["resources", "coverage_note"],
    "additionalProperties": False,
}


def refresh_resources(
    module_key: str,
    client: Optional[ResearchClient] = None,
    limit: Optional[int] = None,
) -> tuple[int, str]:
    """Find current deeper-dive links for one module. Returns (added, message).

    Existing links are not wiped. Anything already known is re-ranked, new
    material is added, and the weakest links beyond the per-module cap are
    retired rather than deleted, so the list stays short and current.
    """
    research = client or get_client()
    if not research.available:
        return 0, (
            "Refreshing links needs an Anthropic API key. The primers and quizzes "
            "work without it."
        )

    module = MODULES_BY_KEY.get(module_key)
    if module is None:
        return 0, "Unknown module."

    keep = limit or config.RESOURCES_PER_MODULE

    with db.session() as conn:
        primer = get_primer(conn, module_key)
        known = [row["url"] for row in resources(conn, module_key)]

    primer_summary = (primer["body"][:3000] + "...") if primer else module.blurb
    known_list = "\n".join(f"  - {url}" for url in known) or "  (none yet)"

    prompt = f"""Find the best current deeper-dive resources on: {module.name}

Scope: {module.blurb}

The reader has already worked through an in-depth written primer on this topic.
The opening of that primer is below so you can see the level and avoid
recommending things that merely repeat it. Your job is to find material that
takes them FURTHER.

WHAT TO LOOK FOR:
  - Written analysis, research and reference material from credible sources
  - Podcasts and audio, which this reader particularly values
  - Video, talks and conference sessions
  - Hands-on or applied material, since this reader learns by doing
Aim for a genuine mix of formats rather than all articles.

QUALITY BAR - apply it strictly:
  - Reputable: established research organisations, major consultancies,
    regulators and standards bodies, respected publications, recognised
    practitioners, serious academic work.
  - Current: prefer the last 12 to 18 months. Older material only if it is a
    genuine reference standard that has not been superseded.
  - Appropriately advanced: written for senior practitioners. Reject
    introductory explainers, "AI 101" content, and vendor marketing outright.
  - Real: only report a URL you actually visited during this search.

Return up to {keep} resources. Fewer excellent ones beats more mediocre ones,
and an empty list is better than padding.

--- ALREADY IN THE LIST (fine to re-report if still among the best) ---
{known_list}

--- PRIMER OPENING (for level calibration) ---
{primer_summary}
"""

    result = research.research(
        purpose=f"academy:resources:{module_key}",
        system=RESOURCE_SYSTEM,
        prompt=prompt,
        schema=RESOURCE_SCHEMA,
        max_searches=8,
    )
    if not result.ok:
        return 0, result.error or "Resource refresh failed."

    now = db.utcnow()
    added = 0

    with db.session() as conn:
        for item in result.items:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            if not url or not title:
                continue
            try:
                rank = max(0.0, min(1.0, float(item.get("rank", 0.5))))
            except (TypeError, ValueError):
                rank = 0.5
            cur = conn.execute(
                """
                INSERT INTO resources
                    (module_key, title, url, format, publisher, published_at, why,
                     rank, status, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                ON CONFLICT(module_key, url) DO UPDATE SET
                    title = excluded.title,
                    format = excluded.format,
                    publisher = excluded.publisher,
                    published_at = excluded.published_at,
                    why = excluded.why,
                    rank = excluded.rank,
                    status = 'active',
                    retired_at = NULL
                """,
                (
                    module_key,
                    title[:300],
                    url,
                    item.get("format") or "article",
                    (item.get("publisher") or "").strip() or None,
                    item.get("published_at"),
                    (item.get("why") or "").strip() or None,
                    rank,
                    now,
                ),
            )
            added += 1 if cur.rowcount else 0

        _retire_surplus(conn, module_key, keep, now)
        db.set_state(conn, _refresh_key(module_key), now)

    return added, f"Refreshed {module.name}: {added} links added or re-ranked."


def _retire_surplus(
    conn: sqlite3.Connection, module_key: str, keep: int, now: str
) -> None:
    """Keep the list short by retiring the weakest links beyond the cap.

    Retired, not deleted: the row stays so the same link is not re-added and
    re-retired every refresh.
    """
    surplus = db.query(
        conn,
        """
        SELECT id FROM resources
        WHERE module_key = ? AND status = 'active'
        ORDER BY rank DESC, added_at DESC
        LIMIT -1 OFFSET ?
        """,
        (module_key, keep),
    )
    for row in surplus:
        db.update(
            conn, "resources", row["id"], {"status": "retired", "retired_at": now}
        )


def _refresh_key(module_key: str) -> str:
    return f"resources_refreshed_at:{module_key}"


def last_refreshed(conn: sqlite3.Connection, module_key: str) -> Optional[str]:
    return db.get_state(conn, _refresh_key(module_key))


def needs_refresh(conn: sqlite3.Connection, module_key: str) -> bool:
    last = last_refreshed(conn, module_key)
    if not last:
        return True
    try:
        stamp = datetime.fromisoformat(last)
    except ValueError:
        return True
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - stamp).days >= config.RESOURCE_REFRESH_DAYS


def refresh_priority_order(conn: sqlite3.Connection) -> list[str]:
    """Which modules to refresh first: highest gap priority, stalest content.

    This is the second thing the gap engine drives, alongside quiz rotation.
    """
    rows = db.query(
        conn,
        "SELECT module_key, priority FROM gap_state ORDER BY priority DESC",
    )
    return [row["module_key"] for row in rows if needs_refresh(conn, row["module_key"])]
