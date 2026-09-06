"""The networking module: a short, living, ranked list.

Deliberately the lightest-touch part of the app (spec 3.1). This is not a CRM
and not a contact database. It is at most ten live targets, ranked, refreshed as
better ones appear and weaker ones age out. If it ever starts feeling like a
task list, the cap is wrong, not the philosophy.

Two things generate targets:

  * **Shortlisting a job.** Only companies Jeff has actively shortlisted get
    targets generated (spec 3.2) - never every company the scanner surfaces.
  * **Latent demand.** A small number of high-conviction targets drawn from
    market signals where there is no posting yet. These hold reserved slots so
    they are never crowded out by companies with open roles (spec 3.5), because
    that is where the proactive edge over a normal job search actually lives.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

import config
from app import db
from app.jobs import scoring
from app.research.client import ResearchClient, get_client


# ---------------------------------------------------------------------------
# Research: finding angles into a company
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You research publicly available professional information to help someone
identify sensible people to approach at a company they are targeting for a
senior role.

You work only from public professional sources: company leadership and team
pages, press releases and news coverage, conference speaker listings, published
interviews and articles, and public professional profiles.

You never report personal contact details, personal email addresses, phone
numbers, home locations, personal social media, or anything about someone's
private life. Titles, professional background, public statements and public
posts are in scope; nothing else is.

You never invent a person. If you cannot verify that someone currently holds a
role at the company, do not report them.
""".strip()


SCHEMA: dict = {
    "type": "object",
    "properties": {
        "targets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rec_type": {
                        "type": "string",
                        "enum": ["person", "engagement"],
                        "description": "'person' = someone worth approaching. 'engagement' = specific public activity worth engaging with.",
                    },
                    "person_name": {"type": "string"},
                    "person_title": {"type": "string"},
                    "profile_url": {"type": "string"},
                    "rationale": {
                        "type": "string",
                        "description": "Two or three sentences on why this person is a sensible opening, specific to them.",
                    },
                    "suggested_action": {
                        "type": "string",
                        "description": "One concrete next step, specific enough to act on today.",
                    },
                    "evidence_url": {"type": "string"},
                    "evidence_note": {
                        "type": "string",
                        "description": "The public thing this rests on - a recent post, talk, hire announcement or article.",
                    },
                    "score": {
                        "type": "number",
                        "description": "0 to 1 - how strong an opening this really is.",
                    },
                },
                "required": [
                    "rec_type",
                    "person_name",
                    "person_title",
                    "profile_url",
                    "rationale",
                    "suggested_action",
                    "evidence_url",
                    "evidence_note",
                    "score",
                ],
                "additionalProperties": False,
            },
        },
        "coverage_note": {"type": "string"},
    },
    "required": ["targets", "coverage_note"],
    "additionalProperties": False,
}


def _build_prompt(company: str, context: str) -> str:
    return f"""Research networking angles into **{company}**.

{context}

The person doing the approaching is a senior executive targeting Head of AI
Strategy and AI transformation leadership roles, with a consulting and corporate
strategy background.

Find up to four items, as a mix of these two types:

1. **person** - Someone at {company} who would be a sensible opening. Usually
   the likely hiring manager, the AI or transformation leader, a strategy leader,
   or a talent partner who covers this kind of role. Prefer the person who would
   actually own the role over a recruiter, and prefer someone with public
   professional visibility over someone invisible.

2. **engagement** - Specific recent public activity worth engaging with: a post,
   an article, a podcast appearance, a conference talk, a published point of
   view. Name the person and what they published, and make the suggested action
   about that specific thing. Generic "comment on their content" is useless.

RULES:
  - Public professional information only. Do not report personal contact
    details, personal email addresses, phone numbers, or anything private.
  - Never invent a person or a role. If you cannot confirm from a source you
    read that someone currently holds a position at {company}, leave them out.
    Returning two verified people beats four half-guessed ones.
  - `evidence_url` must be a page you actually read.
  - `suggested_action` must be concrete enough to act on today - what to
    reference, what angle to take - not "reach out on LinkedIn".
  - `score` should reflect how strong an opening this genuinely is, not how
    senior the person is. A mid-level person who just published something
    directly relevant is a better opening than a silent CEO.

Return an empty list rather than padding if you cannot verify anything.
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_for_job(
    job_id: int, client: Optional[ResearchClient] = None
) -> tuple[int, str]:
    """Generate targets for a shortlisted job's company (spec 3.2 trigger)."""
    with db.session() as conn:
        job = db.query_one(conn, "SELECT * FROM jobs WHERE id = ?", (job_id,))
        if job is None:
            return 0, "Job not found."
        if job["decision"] != "shortlisted":
            return 0, "Targets are only generated for shortlisted roles."

    context = f"""They have shortlisted this specific open role, which is the
natural reason to reach out:

  Role: {job['title']}
  Location: {job['location'] or 'not stated'}
  Posting: {job['url'] or 'not available'}
  What it is: {job['description'] or 'no description captured'}"""

    return _generate(
        company=job["company"],
        context=context,
        client=client,
        job_id=job_id,
        is_latent=False,
        purpose=f"networking:job:{job_id}",
    )


def generate_for_signal(
    signal_id: int, client: Optional[ResearchClient] = None
) -> tuple[int, str]:
    """Generate a latent-demand target from a market signal (spec 3.5)."""
    with db.session() as conn:
        signal = db.query_one(
            conn, "SELECT * FROM market_signals WHERE id = ?", (signal_id,)
        )
        if signal is None:
            return 0, "Signal not found."

    context = f"""There is no posted role here. The reason to reach out is a
recent public signal suggesting this company will soon need senior AI strategy
leadership:

  Signal: {signal['headline']}
  Detail: {signal['detail'] or ''}
  Source: {signal['url'] or 'not available'}

Because there is no posting, the approach has to be genuinely about the signal
rather than about an application. Weight the suggested actions accordingly."""

    return _generate(
        company=signal["company"],
        context=context,
        client=client,
        job_id=None,
        is_latent=True,
        signal_id=signal_id,
        purpose=f"networking:signal:{signal_id}",
    )


def _generate(
    *,
    company: str,
    context: str,
    client: Optional[ResearchClient],
    job_id: Optional[int],
    is_latent: bool,
    purpose: str,
    signal_id: Optional[int] = None,
) -> tuple[int, str]:
    research = client or get_client()
    if not research.available:
        return 0, (
            "Finding networking targets needs an Anthropic API key. Existing "
            "targets still display and can be worked without it."
        )

    result = research.research(
        purpose=purpose,
        system=SYSTEM_PROMPT,
        prompt=_build_prompt(company, context),
        schema=SCHEMA,
        max_searches=6,
    )
    if not result.ok:
        return 0, result.error or "Target research failed."

    now = db.utcnow()
    added = 0

    with db.session() as conn:
        for item in result.items:
            rec_type = item.get("rec_type") or "person"
            if rec_type not in ("person", "engagement"):
                continue
            rationale = (item.get("rationale") or "").strip()
            person = (item.get("person_name") or "").strip()
            if not rationale or not person:
                continue

            print_id = scoring.fingerprint(company, f"{rec_type}:{person}")
            if db.query_one(
                conn,
                "SELECT id FROM networking_targets WHERE fingerprint = ?",
                (print_id,),
            ):
                continue

            try:
                raw_score = max(0.0, min(1.0, float(item.get("score", 0.5))))
            except (TypeError, ValueError):
                raw_score = 0.5

            db.insert(
                conn,
                "networking_targets",
                {
                    "fingerprint": print_id,
                    "company": company,
                    "person_name": person,
                    "person_title": (item.get("person_title") or "").strip() or None,
                    "profile_url": (item.get("profile_url") or "").strip() or None,
                    "rec_type": rec_type,
                    "rationale": rationale,
                    "suggested_action": (item.get("suggested_action") or "").strip() or None,
                    "evidence_url": (item.get("evidence_url") or "").strip() or None,
                    "evidence_note": (item.get("evidence_note") or "").strip() or None,
                    "job_id": job_id,
                    "is_latent": 1 if is_latent else 0,
                    "signal_id": signal_id,
                    "score": raw_score,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            added += 1

        rerank(conn)

    return added, f"Added {added} networking targets for {company}."


def refresh_latent(
    client: Optional[ResearchClient] = None, max_new: int = 2
) -> tuple[int, str]:
    """Top up latent-demand targets from the strongest unused market signals."""
    with db.session() as conn:
        active_latent = db.scalar(
            conn,
            "SELECT COUNT(*) FROM networking_targets WHERE status = 'active' AND is_latent = 1",
            (),
            0,
        )
        if active_latent >= config.LATENT_RESERVED_SLOTS:
            return 0, "Latent targets are already covered."

        signals = db.query(
            conn,
            """
            SELECT s.* FROM market_signals s
            WHERE NOT EXISTS (
                SELECT 1 FROM networking_targets t WHERE t.signal_id = s.id
            )
            ORDER BY s.strength DESC, s.created_at DESC
            LIMIT ?
            """,
            (max_new,),
        )
        signal_ids = [row["id"] for row in signals]

    if not signal_ids:
        return 0, "No unused market signals to work from. Run a scan first."

    total = 0
    for signal_id in signal_ids:
        added, _ = generate_for_signal(signal_id, client=client)
        total += added
    return total, f"Added {total} latent-demand targets."


# ---------------------------------------------------------------------------
# Ranking and the cap
# ---------------------------------------------------------------------------

def rank_score(row: sqlite3.Row) -> float:
    """Rank a target. Open shortlisted roles outrank latent ones, but not by
    so much that latent targets ever become pointless."""
    has_role = row["job_id"] is not None
    base = 0.55 if has_role else 0.35
    model_score = float(row["score"] or 0.5)

    score = base + 0.35 * model_score

    # Latent targets carry the strength of the signal behind them.
    if row["is_latent"] and row["signal_id"]:
        score += 0.10 * _signal_strength(row["signal_id"])

    return round(min(1.0, score) * _age_decay(row["created_at"]), 4)


def _signal_strength(signal_id: int) -> float:
    with db.session() as conn:
        return float(
            db.scalar(
                conn,
                "SELECT strength FROM market_signals WHERE id = ?",
                (signal_id,),
                0.5,
            )
        )


def _age_decay(created_at: Optional[str]) -> float:
    """Older targets decay so the list keeps moving, but never to zero."""
    if not created_at:
        return 1.0
    try:
        stamp = datetime.fromisoformat(created_at)
    except ValueError:
        return 1.0
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - stamp).days
    if age_days <= 0:
        return 1.0
    return max(0.5, 1.0 - 0.5 * (age_days / config.TARGET_STALE_DAYS))


def rerank(conn: sqlite3.Connection) -> None:
    """Rescore every active target and enforce the 5-10 cap.

    Latent targets hold reserved slots: they are kept even when companies with
    open roles would otherwise fill the whole list.
    """
    rows = db.query(
        conn, "SELECT * FROM networking_targets WHERE status = 'active'"
    )
    now = db.utcnow()

    scored = sorted(
        ((rank_score(row), row) for row in rows), key=lambda pair: -pair[0]
    )
    for score, row in scored:
        db.update(
            conn, "networking_targets", row["id"], {"score": score, "updated_at": now}
        )

    if len(scored) <= config.NETWORKING_MAX_ACTIVE:
        return

    latent = [row for score, row in scored if row["is_latent"]]
    reserved_ids = {row["id"] for row in latent[: config.LATENT_RESERVED_SLOTS]}

    keep_ids = set(reserved_ids)
    for _, row in scored:
        if len(keep_ids) >= config.NETWORKING_MAX_ACTIVE:
            break
        keep_ids.add(row["id"])

    for _, row in scored:
        if row["id"] not in keep_ids:
            db.update(
                conn,
                "networking_targets",
                row["id"],
                {"status": "aged_out", "status_changed_at": now, "updated_at": now},
            )


# ---------------------------------------------------------------------------
# Reading and acting
# ---------------------------------------------------------------------------

def active(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.query(
        conn,
        """
        SELECT t.*, j.title AS job_title, j.url AS job_url,
               s.headline AS signal_headline, s.url AS signal_url
        FROM networking_targets t
        LEFT JOIN jobs j ON j.id = t.job_id
        LEFT JOIN market_signals s ON s.id = t.signal_id
        WHERE t.status = 'active'
        ORDER BY t.score DESC
        """,
    )


def by_status(conn: sqlite3.Connection, status: str, limit: int = 100):
    return db.query(
        conn,
        """
        SELECT t.*, j.title AS job_title FROM networking_targets t
        LEFT JOIN jobs j ON j.id = t.job_id
        WHERE t.status = ? ORDER BY t.updated_at DESC LIMIT ?
        """,
        (status, limit),
    )


def set_status(
    conn: sqlite3.Connection, target_id: int, status: str, note: str = ""
) -> bool:
    if status not in ("active", "done", "dismissed", "aged_out"):
        return False
    now = db.utcnow()
    values = {"status": status, "status_changed_at": now, "updated_at": now}
    if note:
        values["note"] = note
    db.update(conn, "networking_targets", target_id, values)
    if status == "active":
        rerank(conn)
    return True


def capacity(conn: sqlite3.Connection) -> dict:
    """How full the list is, so the UI can say when to add more."""
    active_count = db.scalar(
        conn, "SELECT COUNT(*) FROM networking_targets WHERE status = 'active'", (), 0
    )
    latent_count = db.scalar(
        conn,
        "SELECT COUNT(*) FROM networking_targets WHERE status = 'active' AND is_latent = 1",
        (),
        0,
    )
    return {
        "active": active_count,
        "latent": latent_count,
        "min": config.NETWORKING_MIN_ACTIVE,
        "max": config.NETWORKING_MAX_ACTIVE,
        "has_room": active_count < config.NETWORKING_MAX_ACTIVE,
        "below_min": active_count < config.NETWORKING_MIN_ACTIVE,
    }
