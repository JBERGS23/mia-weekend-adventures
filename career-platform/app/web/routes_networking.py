"""Networking views: the short ranked list, and acting on it."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.jobs import repository
from app.networking import targets
from app.research.client import get_client

bp = Blueprint("networking", __name__, url_prefix="/networking")


@bp.get("/")
def index():
    with db.session() as conn:
        return render_template(
            "networking.html",
            targets=targets.active(conn),
            capacity=targets.capacity(conn),
            done=targets.by_status(conn, "done", limit=20),
            aged_out=targets.by_status(conn, "aged_out", limit=20),
            shortlisted=repository.shortlisted(conn),
            signals=repository.recent_signals(conn, limit=6),
            research_ready=get_client().available,
        )


@bp.post("/<int:target_id>/status")
def set_status(target_id: int):
    status = request.form.get("status", "")
    note = request.form.get("note", "").strip()
    with db.session() as conn:
        ok = targets.set_status(conn, target_id, status, note)
    flash("Updated." if ok else "Unknown status.", "info" if ok else "warn")
    return redirect(url_for("networking.index"))


@bp.post("/refresh-latent")
def refresh_latent():
    """Top up the reserved latent-demand slots from market signals (spec 3.5)."""
    added, message = targets.refresh_latent()
    flash(message, "info" if added else "warn")
    return redirect(url_for("networking.index"))


@bp.post("/generate/<int:job_id>")
def generate_for_job(job_id: int):
    """Manual re-run of target generation for an already shortlisted role."""
    added, message = targets.generate_for_job(job_id)
    flash(message, "info" if added else "warn")
    return redirect(url_for("networking.index"))
