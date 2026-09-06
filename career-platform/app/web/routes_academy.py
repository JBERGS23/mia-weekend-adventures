"""Academy views: module list, primers, glossary, resources, quiz, feedback."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.academy import content, quiz
from app.academy.modules import MODULES_BY_KEY
from app.gap import engine as gap_engine
from app.research.client import get_client

bp = Blueprint("academy", __name__, url_prefix="/academy")


@bp.get("/")
def index():
    with db.session() as conn:
        return render_template(
            "academy.html",
            modules=content.list_modules(conn),
            quiz_progress=quiz.today_progress(conn),
            streak=quiz.streak(conn),
            performance=quiz.module_performance(conn),
            priority_label=gap_engine.priority_label,
            research_ready=get_client().available,
        )


@bp.get("/quiz")
def daily_quiz():
    """Today's questions, rotating across all five modules (spec 2.3)."""
    with db.session() as conn:
        questions = quiz.get_or_build_daily(conn)
        return render_template(
            "quiz.html",
            questions=questions,
            progress=quiz.today_progress(conn),
            streak=quiz.streak(conn),
        )


@bp.post("/quiz/answer")
def answer_quiz():
    attempt_id = request.form.get("attempt_id", type=int)
    chosen = request.form.get("chosen_index", type=int)
    if attempt_id is None or chosen is None:
        flash("Pick an answer first.", "warn")
        return redirect(url_for("academy.daily_quiz"))

    with db.session() as conn:
        result = quiz.answer(conn, attempt_id, chosen)
    if result is None:
        flash("That question was already answered.", "warn")
    return redirect(url_for("academy.daily_quiz") + f"#q{attempt_id}")


@bp.get("/glossary")
def glossary():
    with db.session() as conn:
        return render_template(
            "glossary.html",
            terms=content.glossary(conn),
            modules=content.list_modules(conn),
        )


@bp.get("/<module_key>")
def module(module_key: str):
    if module_key not in MODULES_BY_KEY:
        flash("Unknown module.", "warn")
        return redirect(url_for("academy.index"))

    with db.session() as conn:
        primer = content.get_primer(conn, module_key)
        return render_template(
            "module.html",
            module=content.get_module(conn, module_key),
            primer=primer,
            glossary=content.glossary(conn, module_key),
            resources=content.resources(conn, module_key),
            feedback=content.feedback_summary(conn, module_key),
            notes=content.recent_notes(conn, module_key),
            last_refreshed=content.last_refreshed(conn, module_key),
            stale=content.needs_refresh(conn, module_key),
            performance=quiz.module_performance(conn).get(module_key),
            priority_label=gap_engine.priority_label,
            research_ready=get_client().available,
        )


@bp.post("/<module_key>/feedback")
def feedback(module_key: str):
    """The lightweight "more of this / less of this" control (spec 2.4)."""
    signal = request.form.get("signal", "")
    note = request.form.get("note", "")
    with db.session() as conn:
        ok = content.record_feedback(conn, module_key, signal, note)
    flash(
        "Noted - this nudges future weighting for this module."
        if ok
        else "Could not record that feedback.",
        "info" if ok else "warn",
    )
    return redirect(url_for("academy.module", module_key=module_key))


@bp.post("/<module_key>/resources/refresh")
def refresh_resources(module_key: str):
    added, message = content.refresh_resources(module_key)
    flash(message, "info" if added else "warn")
    return redirect(url_for("academy.module", module_key=module_key))


@bp.post("/<module_key>/questions/generate")
def generate_questions(module_key: str):
    added, message = quiz.generate_questions(module_key)
    flash(message, "info" if added else "warn")
    return redirect(url_for("academy.module", module_key=module_key))
