"""The skills-gap engine.

Not a user-facing module (spec 1.6). Its only output is a priority weight per
academy module, which decides how the daily quiz rotates and which modules get
their content refreshed first.

Four inputs feed the weight:

  1. **Baseline proficiency** - the diagnostic levels from spec 2.5, loaded at
     seed time. This is the starting point and never fully washes out, because
     it came from a real conversation rather than an inference.
  2. **Quiz accuracy** - actual measured performance, which progressively
     overrides the baseline as evidence accumulates.
  3. **Demand** - what the live pool of scanned job descriptions is asking for,
     blended with the reference layer's more stable view.
  4. **Feedback** - Jeff's own "more of this / less of this" per module.

Everything here is deterministic arithmetic on rows already in the database, so
recomputing is cheap, needs no API key, and can be re-run at any time.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

import config
from app import db
from app.academy.modules import MODULE_KEYS, MODULES_BY_KEY
from app.jobs import scoring

# How far back the live job pool counts. Long enough to have a sample, short
# enough to be a signal about now rather than about last year.
DEMAND_WINDOW_DAYS = 120

# Smoothing prior. Until this many weighted signals exist, demand is pulled
# toward uniform so a handful of postings cannot swing the rotation.
DEMAND_PRIOR_STRENGTH = 25.0

# Quiz evidence can move proficiency by at most this share of the way from the
# baseline toward measured accuracy.
MAX_QUIZ_INFLUENCE = 0.6

# Attempts needed before quiz evidence carries its full influence.
QUIZ_CONFIDENCE_ATTEMPTS = 20

UNIFORM_SHARE = 1.0 / len(MODULE_KEYS)


# ---------------------------------------------------------------------------
# The public entry point
# ---------------------------------------------------------------------------

def recompute(conn: Optional[sqlite3.Connection] = None, reason: str = "recompute") -> dict[str, float]:
    """Recalculate every module's priority. Returns {module_key: priority}."""
    if conn is not None:
        return _recompute(conn, reason)
    with db.session() as session:
        return _recompute(session, reason)


def _recompute(conn: sqlite3.Connection, reason: str) -> dict[str, float]:
    demand = demand_scores(conn)
    accuracy = quiz_accuracy(conn)
    bias = feedback_bias(conn)
    now = db.utcnow()

    raw: dict[str, float] = {}
    details: dict[str, dict] = {}

    for key in MODULE_KEYS:
        state = db.query_one(
            conn, "SELECT * FROM gap_state WHERE module_key = ?", (key,)
        )
        if state is None:
            continue

        baseline = float(state["baseline_score"])
        module_accuracy, attempts = accuracy.get(key, (None, 0))
        proficiency = blended_proficiency(baseline, module_accuracy, attempts)

        gap = 1.0 - proficiency
        module_demand = demand.get(key, UNIFORM_SHARE)
        module_bias = bias.get(key, 1.0)
        damping = MODULES_BY_KEY[key].weight_damping

        raw[key] = max(0.0, gap * demand_factor(module_demand) * module_bias * damping)
        details[key] = {
            "demand_score": module_demand,
            "quiz_accuracy": module_accuracy,
            "quiz_attempts": attempts,
            "feedback_bias": module_bias,
        }

    total = sum(raw.values())
    priorities: dict[str, float] = {}

    for key, value in raw.items():
        priority = round(value / total, 4) if total > 0 else round(UNIFORM_SHARE, 4)
        priorities[key] = priority
        info = details[key]
        db.update(
            conn,
            "gap_state",
            key,
            {
                "demand_score": round(info["demand_score"], 4),
                "quiz_accuracy": info["quiz_accuracy"],
                "quiz_attempts": info["quiz_attempts"],
                "feedback_bias": round(info["feedback_bias"], 4),
                "priority": priority,
                "updated_at": now,
            },
            key="module_key",
        )
        db.insert(
            conn,
            "gap_history",
            {
                "module_key": key,
                "priority": priority,
                "demand_score": round(info["demand_score"], 4),
                "reason": reason,
                "recorded_at": now,
            },
        )

    return priorities


# ---------------------------------------------------------------------------
# The four inputs
# ---------------------------------------------------------------------------

def blended_proficiency(
    baseline: float, accuracy: Optional[float], attempts: int
) -> float:
    """Move proficiency from the baseline toward measured quiz accuracy.

    With no attempts, this returns the baseline unchanged. Influence grows with
    the number of attempts and caps out, so the diagnostic baseline always
    retains some weight - a run of unlucky questions should not declare a strong
    area weak.
    """
    if accuracy is None or attempts <= 0:
        return baseline
    confidence = min(1.0, attempts / QUIZ_CONFIDENCE_ATTEMPTS)
    influence = confidence * MAX_QUIZ_INFLUENCE
    return (baseline * (1.0 - influence)) + (accuracy * influence)


def demand_scores(conn: sqlite3.Connection) -> dict[str, float]:
    """What the market is currently asking for, per module.

    Blends the live layer (requirements extracted from recently scanned job
    descriptions) with the reference layer (a broader, more stable view
    refreshed by web search). Both are shares that sum to 1 across modules.
    """
    live = _live_demand(conn)
    reference = _reference_demand(conn)

    if reference is None:
        return live
    return {
        key: 0.65 * live.get(key, UNIFORM_SHARE) + 0.35 * reference.get(key, UNIFORM_SHARE)
        for key in MODULE_KEYS
    }


def _live_demand(conn: sqlite3.Connection) -> dict[str, float]:
    cutoff = scoring.cutoff_date(DEMAND_WINDOW_DAYS)
    rows = db.query(
        conn,
        """
        SELECT module_key, SUM(weight) AS total
        FROM job_skill_signals
        WHERE created_at >= ?
        GROUP BY module_key
        """,
        (cutoff,),
    )
    weights = {row["module_key"]: float(row["total"] or 0) for row in rows}
    return _smoothed_shares(weights)


def _reference_demand(conn: sqlite3.Connection) -> Optional[dict[str, float]]:
    rows = db.query(
        conn,
        """
        SELECT module_key, SUM(importance) AS total
        FROM reference_requirements
        GROUP BY module_key
        """,
    )
    if not rows:
        return None
    weights = {row["module_key"]: float(row["total"] or 0) for row in rows}
    if sum(weights.values()) <= 0:
        return None
    return _smoothed_shares(weights)


def _smoothed_shares(weights: dict[str, float]) -> dict[str, float]:
    """Turn raw weights into shares, pulled toward uniform on a thin sample."""
    observed = sum(weights.values())
    if observed <= 0:
        return {key: UNIFORM_SHARE for key in MODULE_KEYS}
    return {
        key: (
            (weights.get(key, 0.0) + UNIFORM_SHARE * DEMAND_PRIOR_STRENGTH)
            / (observed + DEMAND_PRIOR_STRENGTH)
        )
        for key in MODULE_KEYS
    }


def demand_factor(demand: float) -> float:
    """Turn a demand share into a multiplier centred on 1.

    A module at exactly its uniform share gets 1.0, so demand only ever tilts
    the ranking rather than dominating it. The gap itself stays the main driver.
    """
    return 0.7 + 0.3 * (demand / UNIFORM_SHARE)


def quiz_accuracy(conn: sqlite3.Connection) -> dict[str, tuple[Optional[float], int]]:
    """Measured accuracy per module, from answered questions only."""
    rows = db.query(
        conn,
        """
        SELECT module_key,
               COUNT(*) AS attempts,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct
        FROM quiz_attempts
        WHERE answered_at IS NOT NULL
        GROUP BY module_key
        """,
    )
    result: dict[str, tuple[Optional[float], int]] = {}
    for row in rows:
        attempts = int(row["attempts"] or 0)
        if attempts == 0:
            continue
        result[row["module_key"]] = (float(row["correct"] or 0) / attempts, attempts)
    return result


def feedback_bias(conn: sqlite3.Connection) -> dict[str, float]:
    """Turn "more of this / less of this" into a gentle multiplier.

    Deliberately gentle and bounded: this is a nudge on top of the automated
    weighting (spec 2.4), not an override of it.
    """
    rows = db.query(
        conn,
        """
        SELECT module_key,
               SUM(CASE WHEN signal = 'more' THEN 1 ELSE 0 END) AS more_count,
               SUM(CASE WHEN signal = 'less' THEN 1 ELSE 0 END) AS less_count
        FROM module_feedback
        GROUP BY module_key
        """,
    )
    bias: dict[str, float] = {}
    for row in rows:
        net = int(row["more_count"] or 0) - int(row["less_count"] or 0)
        bias[row["module_key"]] = max(0.5, min(2.0, 1.0 + 0.15 * net))
    return bias


# ---------------------------------------------------------------------------
# Reading the current state
# ---------------------------------------------------------------------------

def current_state(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.query(
        conn,
        """
        SELECT g.*, m.name, m.blurb, m.sort_order
        FROM gap_state g
        JOIN academy_modules m ON m.key = g.module_key
        ORDER BY g.priority DESC
        """,
    )


def priorities(conn: sqlite3.Connection) -> dict[str, float]:
    rows = db.query(conn, "SELECT module_key, priority FROM gap_state")
    return {row["module_key"]: float(row["priority"]) for row in rows}


def priority_label(priority: float) -> str:
    """A plain-language band for the UI, so a number is never shown alone."""
    if priority >= 0.30:
        return "Top priority"
    if priority >= 0.20:
        return "High"
    if priority >= 0.12:
        return "Moderate"
    if priority >= 0.06:
        return "Maintenance"
    return "Light touch"
