"""Scan orchestration.

One scan runs each enabled source in turn, stores what comes back, and updates
a progress row the browser polls. Sources are independent: one failing source
logs its error and the scan carries on, because a dead job board should never
cost Jeff the other seven sources.

A scan runs in a background thread so the browser is never left hanging on a
multi-minute research call.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from typing import Optional

from app import db
from app.gap import engine as gap_engine
from app.jobs import extraction, repository
from app.jobs.sources import Source, enabled_sources
from app.research.client import ResearchClient, get_client

logger = logging.getLogger(__name__)

# Guards against two scans running at once. A single-user local app only ever
# needs one in flight, and concurrent scans would double the API spend.
_scan_lock = threading.Lock()
_active_thread: Optional[threading.Thread] = None


# ---------------------------------------------------------------------------
# Run lifecycle
# ---------------------------------------------------------------------------

def start_scan(client: Optional[ResearchClient] = None) -> tuple[bool, str]:
    """Kick off a scan in the background.

    Returns (started, message). Refuses to start a second concurrent scan.
    """
    global _active_thread

    if _active_thread is not None and _active_thread.is_alive():
        return False, "A scan is already running."

    research = client or get_client()
    if not research.available:
        return False, (
            "Live scanning needs an Anthropic API key. Set ANTHROPIC_API_KEY and "
            "restart, and the scan will run. Everything else works without it."
        )

    thread = threading.Thread(target=run_scan, args=(research,), daemon=True)
    _active_thread = thread
    thread.start()
    return True, "Scan started."


def run_scan(client: Optional[ResearchClient] = None) -> int:
    """Run a full scan synchronously. Returns the scan run id.

    Called directly by the background thread, and by tests with a fake client.
    """
    research = client or get_client()
    sources = enabled_sources()

    with db.session() as conn:
        run_id = db.insert(
            conn,
            "scan_runs",
            {
                "started_at": db.utcnow(),
                "status": "running",
                "progress_note": "Starting scan...",
                "sources_total": len(sources),
            },
        )

    if not _scan_lock.acquire(blocking=False):
        _finish_run(run_id, status="failed", error="Another scan is already running.")
        return run_id

    found = 0
    new = 0
    failures: list[str] = []

    try:
        for index, source in enumerate(sources, start=1):
            _progress(
                run_id,
                note=f"Searching: {source.label} ({index} of {len(sources)})",
                sources_run=index - 1,
            )
            try:
                source_found, source_new = _run_source(research, source, run_id)
            except Exception as exc:  # noqa: BLE001 - never let one source kill the scan
                logger.exception("Source %s failed", source.key)
                failures.append(f"{source.label}: {exc}")
                continue

            found += source_found
            new += source_new
            _progress(
                run_id,
                note=f"Finished {source.label}: {source_new} new",
                sources_run=index,
                jobs_found=found,
                jobs_new=new,
            )

        # A scan changes what the live job pool looks like, so the gap engine's
        # demand signal is stale until it is recomputed (spec 1.6 -> 2.3).
        _progress(run_id, note="Updating skills-gap weights...")
        try:
            gap_engine.recompute()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gap recompute failed after scan")
            failures.append(f"Gap recompute: {exc}")

        error = "; ".join(failures) if failures else None
        status = "complete" if len(failures) < len(sources) else "failed"
        _finish_run(
            run_id,
            status=status,
            error=error,
            jobs_found=found,
            jobs_new=new,
            sources_run=len(sources),
            note=f"Done. {new} new of {found} found.",
        )
    finally:
        _scan_lock.release()

    return run_id


def _run_source(client: ResearchClient, source: Source, run_id: int) -> tuple[int, int]:
    """Run one source and store its results. Returns (found, new)."""
    if source.kind == "signals":
        result = client.research(
            purpose=f"scan:{source.key}",
            system=extraction.SYSTEM_PROMPT,
            prompt=extraction.build_signal_prompt(source),
            schema=extraction.SIGNAL_SCHEMA,
            max_searches=source.max_searches,
            allowed_domains=list(source.allowed_domains) or None,
        )
        if not result.ok:
            raise RuntimeError(result.error or "research call failed")

        found = new = 0
        with db.session() as conn:
            for signal in result.items:
                found += 1
                _, is_new = repository.upsert_signal(conn, signal, scan_run_id=run_id)
                new += 1 if is_new else 0
        return found, new

    result = client.research(
        purpose=f"scan:{source.key}",
        system=extraction.SYSTEM_PROMPT,
        prompt=extraction.build_job_prompt(source),
        schema=extraction.JOB_SCHEMA,
        max_searches=source.max_searches,
        allowed_domains=list(source.allowed_domains) or None,
    )
    if not result.ok:
        raise RuntimeError(result.error or "research call failed")

    found = new = 0
    with db.session() as conn:
        for posting in result.items:
            found += 1
            _, is_new = repository.upsert_job(
                conn,
                posting,
                source_name=source.label,
                source_kind=source.key,
                scan_run_id=run_id,
            )
            new += 1 if is_new else 0
    return found, new


# ---------------------------------------------------------------------------
# Progress, read by the browser while a scan is in flight
# ---------------------------------------------------------------------------

def _progress(run_id: int, *, note: str, **fields) -> None:
    values = {"progress_note": note}
    values.update({key: value for key, value in fields.items() if value is not None})
    try:
        with db.session() as conn:
            db.update(conn, "scan_runs", run_id, values)
    except Exception:  # noqa: BLE001 - progress reporting must not break a scan
        logger.exception("Could not update scan progress")


def _finish_run(
    run_id: int,
    *,
    status: str,
    error: Optional[str] = None,
    jobs_found: int = 0,
    jobs_new: int = 0,
    sources_run: int = 0,
    note: str = "",
) -> None:
    with db.session() as conn:
        db.update(
            conn,
            "scan_runs",
            run_id,
            {
                "status": status,
                "finished_at": db.utcnow(),
                "error": error,
                "jobs_found": jobs_found,
                "jobs_new": jobs_new,
                "sources_run": sources_run,
                "progress_note": note or status,
            },
        )


def latest_run(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return db.query_one(conn, "SELECT * FROM scan_runs ORDER BY id DESC LIMIT 1")


def is_running(conn: sqlite3.Connection) -> bool:
    run = latest_run(conn)
    return bool(run and run["status"] == "running")


def recent_runs(conn: sqlite3.Connection, limit: int = 10) -> list[sqlite3.Row]:
    return db.query(
        conn, "SELECT * FROM scan_runs ORDER BY id DESC LIMIT ?", (limit,)
    )
