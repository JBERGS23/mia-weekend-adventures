"""Prompts and JSON schemas for turning a source brief into structured rows.

The rules that apply to every source live here, in one place, so that changing
"never invent a posting" changes it everywhere. The per-source part is just the
brief from sources.py.
"""

from __future__ import annotations

import config
from app.jobs.sources import TITLE_LIST, Source

# ---------------------------------------------------------------------------
# The candidate profile every source is searching against
# ---------------------------------------------------------------------------

CANDIDATE_PROFILE = f"""
You are sourcing roles for a senior executive running a focused job search.

Target titles, roughly in priority order:
{TITLE_LIST}

The last of those matters as much as the first: a strategy leadership role whose
description carries a clear AI transformation mandate counts, even when the word
"AI" never appears in the title. Read descriptions, not just titles.

Four target tracks, all equally in scope:
  1. AI-native companies hiring strategy or transformation leadership
  2. Traditional companies undergoing AI transformation who need that leadership
  3. PE and VC firms hiring AI strategy roles that serve portfolio companies
  4. Consulting and advisory firms building out or scaling AI practices

Seniority: this is a Head of / VP / C-suite search. Director-level roles are
worth reporting only at large companies where Director is genuinely a senior
band. Individual contributor, engineering, research and manager-level roles are
out of scope.

Compensation context: the floor is ${config.COMP_FLOOR:,} base, the target is
${config.COMP_TARGET:,}+ base. Most senior postings will not state compensation.
That is expected and is NOT a reason to exclude a role.

Geography: United States, with remote roles anywhere in scope. Non-US roles only
if explicitly remote-friendly for a US-based candidate.

Explicitly out of scope: climate, energy, and critical minerals roles. This
search is exclusively about AI strategy and transformation.
""".strip()


# ---------------------------------------------------------------------------
# Rules that apply to every job source
# ---------------------------------------------------------------------------

JOB_RULES = f"""
Rules, in order of importance:

1. NEVER invent a posting. Report only roles you actually found on a page you
   read during this search. If a search returns nothing suitable, return an
   empty list. An empty list is a completely acceptable answer and is far more
   useful than a plausible-looking fabrication.

2. Every posting needs a real URL that you saw. If you found a role mentioned
   but could not reach the posting itself, give the best URL you did see (a
   careers index page or the article that mentioned it) and say so in
   `source_note`. Do not construct a URL you did not visit.

3. Prefer recent postings. Aim for roles posted or updated within roughly the
   last {config.FRESHNESS_DAYS} days. Slightly older roles are worth reporting
   if they are strong matches and clearly still open, but say so in
   `source_note`.

4. Compensation: set `comp_confidence` honestly.
   - "Confirmed": the posting itself states a salary or range. Use the base
     salary range, not total compensation, and put anything about equity or
     bonus in `comp_note`.
   - "Estimated": the posting does not state compensation but you can make a
     defensible estimate from the level, company, and location. Say what the
     estimate is based on in `comp_note`.
   - "Unknown": no reasonable basis for an estimate. Leave comp_min and
     comp_max null.
   Never guess a number and label it Confirmed. Under-reporting confidence is
   always better than over-reporting it.

5. `ai_mandate` is true when the role's own responsibilities are substantially
   about setting or delivering an AI strategy or transformation agenda. A role
   that merely mentions AI as industry context, or that sits in a company that
   happens to do AI, is false. Quote the specific language that convinced you
   in `mandate_evidence` - a direct phrase from the posting, not a paraphrase.

6. `requirements` should be the 5 to 10 substantive things the role actually
   asks for, in the posting's own words where possible. Skip boilerplate
   ("excellent communication skills", "bachelor's degree"). These feed a skills
   analysis, so specificity matters more than completeness.

7. `relevance` is your judgement, 0 to 1, of how well this matches the profile
   above. Be discriminating: 0.9+ means a strong, obvious fit; 0.5 means
   plausible but with real reservations; below 0.4 means do not report it at
   all. Explain the score in one sentence in `relevance_note`, and lead with
   the reservation if there is one.

8. Report each distinct role once. If the same role appears on several boards,
   report it once with the most authoritative URL.
""".strip()


JOB_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "postings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "location": {"type": "string"},
                    "remote_policy": {
                        "type": "string",
                        "enum": ["remote", "hybrid", "onsite", "unknown"],
                    },
                    "url": {"type": "string"},
                    "posted_at": {
                        "type": ["string", "null"],
                        "description": "ISO date (YYYY-MM-DD) if stated or clearly derivable, else null.",
                    },
                    "posted_at_is_exact": {
                        "type": "boolean",
                        "description": "True only if the posting stated a date; false for estimates such as 'posted 3 days ago'.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Two to four sentences on what the role actually is.",
                    },
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "track": {
                        "type": "string",
                        "enum": [
                            "ai_native",
                            "traditional_transformation",
                            "pe_vc",
                            "consulting",
                        ],
                    },
                    "seniority": {
                        "type": "string",
                        "enum": ["c_suite", "head_vp", "director", "other"],
                    },
                    "comp_min": {"type": ["integer", "null"]},
                    "comp_max": {"type": ["integer", "null"]},
                    "comp_currency": {"type": "string"},
                    "comp_confidence": {
                        "type": "string",
                        "enum": ["Confirmed", "Estimated", "Unknown"],
                    },
                    "comp_note": {"type": "string"},
                    "ai_mandate": {"type": "boolean"},
                    "mandate_evidence": {"type": "string"},
                    "relevance": {"type": "number"},
                    "relevance_note": {"type": "string"},
                    "source_note": {"type": "string"},
                },
                "required": [
                    "company",
                    "title",
                    "location",
                    "remote_policy",
                    "url",
                    "posted_at",
                    "posted_at_is_exact",
                    "description",
                    "requirements",
                    "track",
                    "seniority",
                    "comp_min",
                    "comp_max",
                    "comp_currency",
                    "comp_confidence",
                    "comp_note",
                    "ai_mandate",
                    "mandate_evidence",
                    "relevance",
                    "relevance_note",
                    "source_note",
                ],
                "additionalProperties": False,
            },
        },
        "coverage_note": {
            "type": "string",
            "description": "One or two sentences on what was searched and any gaps.",
        },
    },
    "required": ["postings", "coverage_note"],
    "additionalProperties": False,
}


SIGNAL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "signal_type": {
                        "type": "string",
                        "enum": [
                            "funding",
                            "leadership_hire",
                            "ai_initiative",
                            "practice_launch",
                            "leadership_gap",
                        ],
                    },
                    "headline": {"type": "string"},
                    "detail": {
                        "type": "string",
                        "description": "Two or three sentences, including why it implies senior AI leadership demand.",
                    },
                    "url": {"type": "string"},
                    "signal_date": {"type": ["string", "null"]},
                    "strength": {
                        "type": "number",
                        "description": "0 to 1: how strongly this implies a near-term senior AI strategy hire.",
                    },
                },
                "required": [
                    "company",
                    "signal_type",
                    "headline",
                    "detail",
                    "url",
                    "signal_date",
                    "strength",
                ],
                "additionalProperties": False,
            },
        },
        "coverage_note": {"type": "string"},
    },
    "required": ["signals", "coverage_note"],
    "additionalProperties": False,
}


SIGNAL_RULES = """
Rules:

1. Never invent a signal. Report only things you actually read during this
   search, each with a real URL you visited. An empty list is an acceptable
   answer.

2. Recency matters more here than anywhere else. Prefer the last 30 days;
   anything older than about 90 days is not a signal, it is history.

3. `strength` should reflect how strongly this implies a near-term senior AI
   strategy or transformation hire, not how interesting the news is. A large
   funding round at a company that already has a Chief AI Officer is weaker
   than a mid-size traditional company announcing an AI transformation
   programme with no AI leader in place.

4. Prefer signals that give a specific, natural reason to reach out to a named
   company in the next few weeks. Generic industry trend pieces are not signals.
""".strip()


SYSTEM_PROMPT = """
You are a research assistant conducting an executive job search. You search the
web, read what you find, and report only what you actually saw.

Accuracy matters far more than volume here. A short list of real, verified
postings is worth more than a long list padded with plausible guesses, and a
fabricated posting wastes the reader's time and damages their trust in every
other row. When you are unsure whether something is real or current, either say
so in the notes field or leave it out.
""".strip()


def build_job_prompt(source: Source) -> str:
    return f"""{CANDIDATE_PROFILE}

--- YOUR ASSIGNMENT: {source.label} ---

{source.brief}

--- RULES ---

{JOB_RULES}

Work through several different searches rather than relying on one. Return the
postings you found as JSON matching the required schema."""


def build_signal_prompt(source: Source) -> str:
    return f"""{CANDIDATE_PROFILE}

--- YOUR ASSIGNMENT: {source.label} ---

{source.brief}

--- RULES ---

{SIGNAL_RULES}

Return the signals you found as JSON matching the required schema."""
