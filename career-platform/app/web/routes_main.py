"""Dashboard, scanning, and the settings/diagnostics page."""

from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import db
from app.academy import content, quiz
from app.gap import engine as gap_engine
from app.gap import reference
from app.jobs import repository, scanner
from app.networking import targets
from app.research.client import get_client

bp = Blueprint("main", __name__)


@bp.route("/")
def dashboard():
    """One screen answering: what is new, what should I study, who should I talk to."""
    with db.session() as conn:
        return render_template(
            "dashboard.html",
            counts=repository.counts(conn),
            new_jobs=repository.new_jobs(conn, limit=6),
            quiz_progress=quiz.today_progress(conn),
            streak=quiz.streak(conn),
            gap=gap_engine.current_state(conn),
            targets=targets.active(conn)[:4],
            capacity=targets.capacity(conn),
            latest_run=scanner.latest_run(conn),
            scanning=scanner.is_running(conn),
            research_ready=get_client().available,
            priority_label=gap_engine.priority_label,
        )


@bp.post("/scan")
def start_scan():
    started, message = scanner.start_scan()
    flash(message, "info" if started else "warn")
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.get("/scan/status")
def scan_status():
    """Polled by the browser while a scan is in flight."""
    with db.session() as conn:
        run = scanner.latest_run(conn)
        if run is None:
            return jsonify({"status": "idle"})
        return jsonify(
            {
                "status": run["status"],
                "note": run["progress_note"],
                "sources_run": run["sources_run"],
                "sources_total": run["sources_total"],
                "jobs_new": run["jobs_new"],
                "jobs_found": run["jobs_found"],
                "error": run["error"],
            }
        )


@bp.get("/settings")
def settings():
    """Diagnostics: how the gap weights were derived, what the API has cost,
    and what the last few scans did. Nothing here is required reading."""
    with db.session() as conn:
        return render_template(
            "settings.html",
            gap=gap_engine.current_state(conn),
            reference=reference.current(conn),
            reference_stale=reference.needs_refresh(conn),
            runs=scanner.recent_runs(conn),
            calls=db.query(
                conn,
                "SELECT * FROM research_calls ORDER BY id DESC LIMIT 25",
            ),
            totals=db.query_one(
                conn,
                """
                SELECT COUNT(*) AS calls,
                       SUM(input_tokens) AS input_tokens,
                       SUM(output_tokens) AS output_tokens,
                       SUM(web_searches) AS searches
                FROM research_calls
                """,
            ),
            modules=content.list_modules(conn),
            research_ready=get_client().available,
            priority_label=gap_engine.priority_label,
        )


@bp.post("/gap/recompute")
def recompute_gap():
    gap_engine.recompute(reason="manual recompute")
    flash("Skills-gap weights recomputed.", "info")
    return redirect(url_for("main.settings"))


@bp.post("/gap/reference/refresh")
def refresh_reference():
    ok, message = reference.refresh()
    flash(message, "info" if ok else "warn")
    return redirect(url_for("main.settings"))
