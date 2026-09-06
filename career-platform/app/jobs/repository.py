"""Database access for jobs, decisions, skill signals and market signals.

All SQL touching the job tables lives here. The scanner and the web layer call
these functions rather than writing queries of their own, so the dedupe rule and
the definition of "the review queue" exist in exactly one place.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

import config
from app import db
from app.academy.modules import classify_requirement
from app.jobs import scoring


# ---------------------------------------------------------------------------
# Writing scan results
# ---------------------------------------------------------------------------

def upsert_job(
    conn: sqlite3.Connection,
    posting: dict,
    *,
    source_name: str,
    source_kind: str,
    scan_run_id: Optional[int] = None,
) -> tuple[Optional[int], bool]:
    """Insert a posting, or touch it if it has been seen before.

    Returns (job_id, is_new). This is the dedupe rule from spec 1.5: everything
    ever scanned is kept, and a posting already in the archive is never shown
    as new again, however many sources report it.
    """
    company = (posting.get("company") or "").strip()
    title = (posting.get("title") or "").strip()
    if not company or not title:
        return None, False

    location = (posting.get("location") or "").strip()
    print_id = scoring.fingerprint(company, title, location)
    url = (posting.get("url") or "").strip() or None
    url_hash = scoring.hash_url(url)
    now = db.utcnow()

    # Identity is company + title + city. The URL is only a secondary match, and
    # only when the role matches too: the extraction prompt deliberately allows a
    # careers-index URL when no direct posting link was reachable, so several
    # genuinely different roles can share one URL and must not be collapsed.
    existing = db.query_one(
        conn, "SELECT id FROM jobs WHERE fingerprint = ?", (print_id,)
    )
    if existing is None and url_hash:
        for row in db.query(
            conn, "SELECT id, title FROM jobs WHERE url_hash = ?", (url_hash,)
        ):
            if scoring.normalise_title(row["title"]) == scoring.normalise_title(title):
                existing = row
                break

    if existing:
        # Seen before. Record that it is still live, and nothing else - Jeff's
        # decision and the original scoring stay as they were.
        db.update(conn, "jobs", existing["id"], {"last_seen_at": now})
        return int(existing["id"]), False

    comp = scoring.clean_compensation(posting)
    fit_score, rationale = scoring.score_posting(posting, comp)

    requirements = posting.get("requirements") or []
    if isinstance(requirements, str):
        requirements = [requirements]

    job_id = db.insert(
        conn,
        "jobs",
        {
            "fingerprint": print_id,
            "url": url,
            "url_hash": url_hash,
            "company": company,
            "title": title,
            "location": location,
            "remote_policy": posting.get("remote_policy") or "unknown",
            "posted_at": scoring.parse_date(posting.get("posted_at")).isoformat()
            if scoring.parse_date(posting.get("posted_at"))
            else None,
            "posted_at_is_exact": 1 if posting.get("posted_at_is_exact") else 0,
            "description": (posting.get("description") or "").strip(),
            "requirements": "\n".join(str(item).strip() for item in requirements if item),
            "track": posting.get("track") or None,
            "seniority": posting.get("seniority") or None,
            **comp,
            "fit_score": fit_score,
            "fit_rationale": rationale,
            "ai_mandate": 1 if posting.get("ai_mandate") else 0,
            "mandate_evidence": (posting.get("mandate_evidence") or "").strip(),
            "source_name": source_name,
            "source_kind": source_kind,
            "first_seen_at": now,
            "last_seen_at": now,
            "scan_run_id": scan_run_id,
            "decision": None,
        },
    )

    record_skill_signals(conn, job_id, requirements, posting.get("description") or "")
    return job_id, True


def record_skill_signals(
    conn: sqlite3.Connection,
    job_id: int,
    requirements: list,
    description: str = "",
) -> int:
    """Map a posting's requirements onto academy modules.

    This is the live layer feeding the gap engine (spec 1.6): a rolling signal
    of what senior AI strategy roles are actually asking for right now.
    """
    now = db.utcnow()
    written = 0
    seen: set[tuple[str, str]] = set()

    for phrase in list(requirements) + ([description] if description else []):
        text = str(phrase).strip()
        if not text:
            continue
        # A requirement can legitimately speak to more than one module.
        for module_key in classify_requirement(text):
            key = (module_key, text[:200])
            if key in seen:
                continue
            seen.add(key)
            # The description is a weaker signal than an explicit requirement.
            weight = 0.4 if text == description else 1.0
            db.insert(
                conn,
                "job_skill_signals",
                {
                    "job_id": job_id,
                    "module_key": module_key,
                    "phrase": text[:500],
                    "weight": weight,
                    "created_at": now,
                },
            )
            written += 1
    return written


def upsert_signal(
    conn: sqlite3.Connection,
    signal: dict,
    *,
    scan_run_id: Optional[int] = None,
) -> tuple[Optional[int], bool]:
    """Store a market signal, deduped on company plus headline."""
    company = (signal.get("company") or "").strip()
    headline = (signal.get("headline") or "").strip()
    if not company or not headline:
        return None, False

    print_id = scoring.fingerprint(company, headline)
    existing = db.query_one(
        conn, "SELECT id FROM market_signals WHERE fingerprint = ?", (print_id,)
    )
    if existing:
        return int(existing["id"]), False

    signal_id = db.insert(
        conn,
        "market_signals",
        {
            "fingerprint": print_id,
            "company": company,
            "signal_type": signal.get("signal_type") or "ai_initiative",
            "headline": headline,
            "detail": (signal.get("detail") or "").strip(),
            "url": (signal.get("url") or "").strip() or None,
            "signal_date": signal.get("signal_date"),
            "strength": scoring._clamp(scoring._as_float(signal.get("strength"), 0.5)),
            "scan_run_id": scan_run_id,
            "created_at": db.utcnow(),
        },
    )
    return signal_id, True


# ---------------------------------------------------------------------------
# Reading: the views the UI needs
# ---------------------------------------------------------------------------

def new_jobs(conn: sqlite3.Connection, limit: int = 100) -> list[sqlite3.Row]:
    """The main review queue: undecided, relevant, and genuinely recent.

    "Recent" means posted within the freshness window, or - for postings with
    no date - first seen within the grace window. Anything older stays in the
    archive rather than cluttering this view.
    """
    posted_cutoff = scoring.cutoff_date(config.FRESHNESS_DAYS)
    seen_cutoff = scoring.cutoff_date(config.UNDATED_GRACE_DAYS)
    return db.query(
        conn,
        """
        SELECT * FROM jobs
        WHERE decision IS NULL
          AND fit_score >= ?
          AND (
                (posted_at IS NOT NULL AND posted_at >= ?)
             OR (posted_at IS NULL AND first_seen_at >= ?)
          )
        ORDER BY fit_score DESC, first_seen_at DESC
        LIMIT ?
        """,
        (config.MIN_FIT_TO_SURFACE, posted_cutoff, seen_cutoff, limit),
    )


def open_jobs(conn: sqlite3.Connection, limit: int = 300) -> list[sqlite3.Row]:
    """Everything still undecided, regardless of age."""
    return db.query(
        conn,
        """
        SELECT * FROM jobs
        WHERE decision IS NULL AND fit_score >= ?
        ORDER BY fit_score DESC, first_seen_at DESC
        LIMIT ?
        """,
        (config.MIN_FIT_TO_SURFACE, limit),
    )


def jobs_by_decision(
    conn: sqlite3.Connection, decision: str, limit: int = 300
) -> list[sqlite3.Row]:
    return db.query(
        conn,
        """
        SELECT * FROM jobs WHERE decision = ?
        ORDER BY decided_at DESC LIMIT ?
        """,
        (decision, limit),
    )


def shortlisted(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return jobs_by_decision(conn, "shortlisted")


def search_archive(
    conn: sqlite3.Connection,
    *,
    text: str = "",
    track: str = "",
    decision: str = "",
    source: str = "",
    limit: int = 400,
) -> list[sqlite3.Row]:
    """The searchable archive of everything ever scanned (spec 1.5).

    Visible on request, deliberately not part of the main view.
    """
    clauses: list[str] = []
    params: list[Any] = []

    if text:
        clauses.append(
            "(company LIKE ? OR title LIKE ? OR description LIKE ? OR location LIKE ?)"
        )
        pattern = f"%{text}%"
        params.extend([pattern] * 4)
    if track:
        clauses.append("track = ?")
        params.append(track)
    if decision == "undecided":
        clauses.append("decision IS NULL")
    elif decision:
        clauses.append("decision = ?")
        params.append(decision)
    if source:
        clauses.append("source_name = ?")
        params.append(source)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return db.query(
        conn,
        f"SELECT * FROM jobs {where} ORDER BY first_seen_at DESC LIMIT ?",
        params,
    )


def get_job(conn: sqlite3.Connection, job_id: int) -> Optional[sqlite3.Row]:
    return db.query_one(conn, "SELECT * FROM jobs WHERE id = ?", (job_id,))


def decision_history(conn: sqlite3.Connection, job_id: int) -> list[sqlite3.Row]:
    return db.query(
        conn,
        "SELECT * FROM job_decisions WHERE job_id = ? ORDER BY decided_at DESC",
        (job_id,),
    )


def recent_signals(conn: sqlite3.Connection, limit: int = 40) -> list[sqlite3.Row]:
    return db.query(
        conn,
        "SELECT * FROM market_signals ORDER BY strength DESC, created_at DESC LIMIT ?",
        (limit,),
    )


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

def set_decision(
    conn: sqlite3.Connection,
    job_id: int,
    decision: Optional[str],
    note: str = "",
) -> None:
    """Shortlist, dismiss, or reset a posting to undecided.

    The current state lives on the job row; every change is also appended to
    job_decisions, so the archive remembers that Jeff dismissed something before
    he changed his mind (spec 1.5).
    """
    now = db.utcnow()
    db.update(
        conn,
        "jobs",
        job_id,
        {
            "decision": decision,
            "decided_at": now if decision else None,
            "decision_note": note or None,
        },
    )
    db.insert(
        conn,
        "job_decisions",
        {
            "job_id": job_id,
            "decision": decision or "reset",
            "note": note or None,
            "decided_at": now,
        },
    )


# ---------------------------------------------------------------------------
# Counts for the dashboard
# ---------------------------------------------------------------------------

def counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "new": len(new_jobs(conn, limit=1000)),
        "open": db.scalar(
            conn,
            "SELECT COUNT(*) FROM jobs WHERE decision IS NULL AND fit_score >= ?",
            (config.MIN_FIT_TO_SURFACE,),
            0,
        ),
        "shortlisted": db.scalar(
            conn, "SELECT COUNT(*) FROM jobs WHERE decision = 'shortlisted'", (), 0
        ),
        "dismissed": db.scalar(
            conn, "SELECT COUNT(*) FROM jobs WHERE decision = 'dismissed'", (), 0
        ),
        "archive": db.scalar(conn, "SELECT COUNT(*) FROM jobs", (), 0),
        "signals": db.scalar(conn, "SELECT COUNT(*) FROM market_signals", (), 0),
    }


def distinct_sources(conn: sqlite3.Connection) -> list[str]:
    rows = db.query(
        conn, "SELECT DISTINCT source_name FROM jobs ORDER BY source_name"
    )
    return [row["source_name"] for row in rows]
