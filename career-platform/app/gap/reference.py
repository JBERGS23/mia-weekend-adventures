"""The gap engine's reference layer (spec 1.6, layer 2).

The live layer reads what the currently scanned postings ask for. That is a
sharp signal but a narrow one: it reflects whichever roles happened to be open
this month. The reference layer balances it with a broader, more stable view of
what senior AI strategy and transformation roles generally require, refreshed by
fresh web search rather than read from a static seed list.

Source quality is part of the brief, not an afterthought: the search is told to
prefer reputable, current, appropriately advanced sources and to say why each
one passed.
"""

from __future__ import annotations

from typing import Optional

from app import db
from app.academy.modules import MODULES
from app.research.client import ResearchClient, get_client

REFRESH_INTERVAL_DAYS = 30
STATE_KEY = "reference_layer_refreshed_at"

MODULE_LIST = "\n".join(f"  - {m.key}: {m.name} - {m.blurb}" for m in MODULES)


SYSTEM_PROMPT = """
You are researching what senior AI strategy and transformation leadership roles
actually require, for someone preparing to compete for them.

Report only what you found in sources you actually read during this search.
Judge sources critically: a vendor's content-marketing blog post and a major
executive search firm's published role specification are not equally good
evidence, and you should say which you are relying on.
""".strip()


PROMPT = f"""
Research what senior AI strategy and transformation leadership roles require in
2026. Target roles: Head of AI Strategy, Head of AI Transformation, VP of AI
Strategy, Chief AI Officer, and strategy leadership roles carrying an explicit
AI transformation mandate.

Search across: executive search firm role specifications and published points of
view, recent analyst and consulting research on AI leadership capability,
serious industry commentary on what these roles are accountable for, and
credible reporting on what companies say they need from AI leaders.

SOURCE QUALITY BAR - apply this before including anything:
  - Reputable: established research bodies, executive search firms, major
    consultancies, respected industry publications, academic work. Not vendor
    content marketing dressed as research, not SEO listicles.
  - Current: published or substantially updated within roughly the last 18
    months. This field moves fast and older material describes a different job.
  - Appropriately advanced: written for senior practitioners. Explicitly reject
    "what is AI" explainers and beginner career content - they describe the
    wrong altitude entirely.
State briefly in `quality_note` why each source cleared this bar.

Map each requirement you find to exactly one of these five capability areas:
{MODULE_LIST}

Only report requirements that genuinely map to one of the five. Plenty of what
these roles ask for - executive presence, P&L experience, industry knowledge -
does not, and should simply be left out rather than forced into a category.

Set `importance` from 0 to 1 based on how consistently the requirement appeared
across the credible sources you read, not on how important it sounds.

Return 15 to 30 requirements in total, spread across the areas according to what
you actually found - do not force an even distribution.
""".strip()


SCHEMA: dict = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "module_key": {
                        "type": "string",
                        "enum": [m.key for m in MODULES],
                    },
                    "requirement": {
                        "type": "string",
                        "description": "One specific capability these roles ask for, in a single sentence.",
                    },
                    "importance": {"type": "number"},
                    "source_url": {"type": "string"},
                    "source_title": {"type": "string"},
                    "quality_note": {
                        "type": "string",
                        "description": "Why this source cleared the quality bar.",
                    },
                },
                "required": [
                    "module_key",
                    "requirement",
                    "importance",
                    "source_url",
                    "source_title",
                    "quality_note",
                ],
                "additionalProperties": False,
            },
        },
        "coverage_note": {"type": "string"},
    },
    "required": ["requirements", "coverage_note"],
    "additionalProperties": False,
}


def needs_refresh(conn) -> bool:
    last = db.get_state(conn, STATE_KEY)
    if not last:
        return True
    from datetime import datetime, timezone

    try:
        stamp = datetime.fromisoformat(last)
    except ValueError:
        return True
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - stamp).days
    return age_days >= REFRESH_INTERVAL_DAYS


def refresh(client: Optional[ResearchClient] = None) -> tuple[bool, str]:
    """Refresh the reference layer. Returns (ok, message)."""
    research = client or get_client()
    if not research.available:
        return False, (
            "Refreshing the reference layer needs an Anthropic API key. The gap "
            "engine still works from the diagnostic baseline and the live job pool."
        )

    result = research.research(
        purpose="gap:reference_layer",
        system=SYSTEM_PROMPT,
        prompt=PROMPT,
        schema=SCHEMA,
        max_searches=10,
    )
    if not result.ok:
        return False, result.error or "The reference layer refresh failed."

    now = db.utcnow()
    written = 0
    valid_keys = {m.key for m in MODULES}

    with db.session() as conn:
        # Replace wholesale: this layer is a snapshot of current thinking, not
        # an accumulating log, and stale requirements would skew the weights.
        conn.execute("DELETE FROM reference_requirements")
        for item in result.items:
            module_key = item.get("module_key")
            requirement = (item.get("requirement") or "").strip()
            if module_key not in valid_keys or not requirement:
                continue
            try:
                importance = max(0.0, min(1.0, float(item.get("importance", 0.5))))
            except (TypeError, ValueError):
                importance = 0.5
            conn.execute(
                """
                INSERT INTO reference_requirements
                    (module_key, requirement, importance, source_url, source_title,
                     quality_note, refreshed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(module_key, requirement) DO UPDATE SET
                    importance = excluded.importance,
                    source_url = excluded.source_url,
                    source_title = excluded.source_title,
                    quality_note = excluded.quality_note,
                    refreshed_at = excluded.refreshed_at
                """,
                (
                    module_key,
                    requirement[:500],
                    importance,
                    (item.get("source_url") or "").strip() or None,
                    (item.get("source_title") or "").strip() or None,
                    (item.get("quality_note") or "").strip() or None,
                    now,
                ),
            )
            written += 1
        db.set_state(conn, STATE_KEY, now)

    # New reference weights change the demand blend, so recompute immediately.
    from app.gap import engine

    engine.recompute(reason="reference layer refreshed")

    return True, f"Reference layer refreshed: {written} requirements."


def current(conn, module_key: Optional[str] = None):
    if module_key:
        return db.query(
            conn,
            """
            SELECT * FROM reference_requirements WHERE module_key = ?
            ORDER BY importance DESC
            """,
            (module_key,),
        )
    return db.query(
        conn,
        "SELECT * FROM reference_requirements ORDER BY module_key, importance DESC",
    )
