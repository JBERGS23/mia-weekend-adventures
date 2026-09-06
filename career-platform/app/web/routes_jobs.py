"""Job scanner views: review queue, detail, decisions, archive, signals."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.jobs import repository, scanner, scoring
from app.networking import targets

bp = Blueprint("jobs", __name__, url_prefix="/jobs")

TABS = {
    "new": "New this week",
    "open": "All open",
    "shortlisted": "Shortlisted",
    "dismissed": "Dismissed",
}


@bp.get("/")
def index():
    tab = request.args.get("tab", "new")
    if tab not in TABS:
        tab = "new"

    with db.session() as conn:
        if tab == "new":
            rows = repository.new_jobs(conn)
        elif tab == "open":
            rows = repository.open_jobs(conn)
        else:
            rows = repository.jobs_by_decision(conn, tab)

        return render_template(
            "jobs.html",
            jobs=rows,
            tab=tab,
            tabs=TABS,
            counts=repository.counts(conn),
            scanning=scanner.is_running(conn),
            latest_run=scanner.latest_run(conn),
        )


@bp.get("/archive")
def archive():
    """Everything ever scanned, searchable (spec 1.5)."""
    text = request.args.get("q", "").strip()
    track = request.args.get("track", "")
    decision = request.args.get("decision", "")
    source = request.args.get("source", "")

    with db.session() as conn:
        return render_template(
            "archive.html",
            jobs=repository.search_archive(
                conn, text=text, track=track, decision=decision, source=source
            ),
            counts=repository.counts(conn),
            sources=repository.distinct_sources(conn),
            q=text,
            track=track,
            decision=decision,
            source=source,
        )


@bp.get("/signals")
def signals():
    """Market signals: latent demand that has not become a posting yet."""
    with db.session() as conn:
        return render_template(
            "signals.html",
            signals=repository.recent_signals(conn),
            counts=repository.counts(conn),
            capacity=targets.capacity(conn),
        )


@bp.get("/<int:job_id>")
def detail(job_id: int):
    with db.session() as conn:
        job = repository.get_job(conn, job_id)
        if job is None:
            flash("That posting is not in the archive.", "warn")
            return redirect(url_for("jobs.index"))
        return render_template(
            "job_detail.html",
            job=job,
            history=repository.decision_history(conn, job_id),
            requirements=[
                line for line in (job["requirements"] or "").split("\n") if line.strip()
            ],
            below_floor=scoring.below_floor(dict(job)),
            related_targets=[
                row for row in targets.active(conn) if row["job_id"] == job_id
            ],
        )


@bp.post("/<int:job_id>/decision")
def decide(job_id: int):
    """Shortlist, dismiss, or reset - and trigger networking on a shortlist.

    This is the integration point in spec 3.2: shortlisting is the only thing
    that puts a company into the networking module.
    """
    decision = request.form.get("decision") or None
    note = request.form.get("note", "").strip()
    if decision not in ("shortlisted", "dismissed", None):
        flash("Unknown decision.", "warn")
        return redirect(url_for("jobs.detail", job_id=job_id))

    with db.session() as conn:
        job = repository.get_job(conn, job_id)
        if job is None:
            flash("That posting is not in the archive.", "warn")
            return redirect(url_for("jobs.index"))
        repository.set_decision(conn, job_id, decision, note)

    if decision == "shortlisted":
        added, message = targets.generate_for_job(job_id)
        flash(
            f"Shortlisted. {message}" if added else f"Shortlisted. {message}",
            "info" if added else "warn",
        )
    elif decision == "dismissed":
        flash("Dismissed. It stays in the archive.", "info")
    else:
        flash("Moved back to undecided.", "info")

    return redirect(request.form.get("next") or url_for("jobs.index"))


@bp.post("/signals/<int:signal_id>/network")
def network_signal(signal_id: int):
    """Turn a market signal into a latent-demand networking target."""
    added, message = targets.generate_for_signal(signal_id)
    flash(message, "info" if added else "warn")
    return redirect(url_for("jobs.signals"))
