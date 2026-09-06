#!/usr/bin/env python3
"""Fill a SEPARATE demo database with example data, then run the app on it.

    python demo.py

Useful for seeing what the app looks like populated before you have an API key.

The demo data is entirely made up. It is written to data/demo.db, never to your
real data/career.db, so there is no way to confuse example postings with real
ones. Delete data/demo.db to reset it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import config

config.DATABASE_PATH = Path(__file__).resolve().parent / "data" / "demo.db"

from app import create_app, db  # noqa: E402
from app.jobs import repository  # noqa: E402
from app.networking import targets  # noqa: E402

DEMO_POSTINGS = [
    {
        "company": "[DEMO] Northwind Insurance",
        "title": "Head of AI Strategy",
        "location": "New York, NY",
        "remote_policy": "hybrid",
        "url": "https://example.invalid/northwind/head-ai-strategy",
        "posted_at": None,
        "posted_at_is_exact": False,
        "description": (
            "Own the enterprise AI strategy for a $12bn insurer, reporting to the "
            "Chief Strategy Officer. Set the use-case portfolio, run the governance "
            "framework, and lead the transformation of claims and underwriting."
        ),
        "requirements": [
            "Build and run a risk-tiered AI governance framework",
            "Working knowledge of the EU AI Act and US state AI regulation",
            "Lead use-case prioritisation and build/buy/partner decisions",
            "Partner with model risk and internal audit",
            "Drive adoption across 4,000 knowledge workers",
        ],
        "track": "traditional_transformation",
        "seniority": "head_vp",
        "comp_min": 300000, "comp_max": 360000, "comp_currency": "USD",
        "comp_confidence": "Confirmed", "comp_note": "Plus 30% target bonus.",
        "ai_mandate": True,
        "mandate_evidence": "own the enterprise AI strategy and transformation agenda",
        "relevance": 0.94,
        "relevance_note": "Direct title match with an explicit transformation mandate.",
        "source_note": "",
    },
    {
        "company": "[DEMO] Vantage Partners Capital",
        "title": "Operating Partner, AI Value Creation",
        "location": "Boston, MA",
        "remote_policy": "hybrid",
        "url": "https://example.invalid/vantage/operating-partner-ai",
        "posted_at": None, "posted_at_is_exact": False,
        "description": (
            "Serve 30 portfolio companies as the firm's senior AI operator. Set the "
            "AI value creation playbook and work directly with portfolio CEOs."
        ),
        "requirements": [
            "Define an AI value creation playbook across a portfolio",
            "Assess build/buy/partner decisions and ROI frameworks",
            "Evaluate agentic AI and orchestration opportunities",
        ],
        "track": "pe_vc", "seniority": "head_vp",
        "comp_min": None, "comp_max": None, "comp_currency": "USD",
        "comp_confidence": "Estimated",
        "comp_note": "Estimated $325-400k base from level and market; carry likely.",
        "ai_mandate": True,
        "mandate_evidence": "set the AI value creation playbook across the portfolio",
        "relevance": 0.88, "relevance_note": "Strong PE track fit.",
        "source_note": "",
    },
    {
        "company": "[DEMO] Meridian Health Systems",
        "title": "VP Corporate Strategy",
        "location": "Chicago, IL",
        "remote_policy": "onsite",
        "url": "https://example.invalid/meridian/vp-strategy",
        "posted_at": None, "posted_at_is_exact": False,
        "description": (
            "Lead corporate strategy with a specific mandate to define and deliver "
            "the system's AI agenda across clinical and administrative operations."
        ),
        "requirements": [
            "Define the enterprise AI agenda and roadmap",
            "Navigate FDA and state regulation of clinical AI",
            "Build the case for AI investment with the board",
        ],
        "track": "traditional_transformation", "seniority": "head_vp",
        "comp_min": None, "comp_max": None, "comp_currency": "USD",
        "comp_confidence": "Unknown", "comp_note": "",
        "ai_mandate": True,
        "mandate_evidence": "a specific mandate to define and deliver the system's AI agenda",
        "relevance": 0.81,
        "relevance_note": "AI mandate lives in the description, not the title.",
        "source_note": "",
    },
    {
        "company": "[DEMO] Halcyon Labs",
        "title": "Head of AI Transformation",
        "location": "Remote (US)",
        "remote_policy": "remote",
        "url": "https://example.invalid/halcyon/head-ai-transformation",
        "posted_at": None, "posted_at_is_exact": False,
        "description": (
            "Take an AI-native platform company from product-led growth into "
            "enterprise deployment. Own the deployment operating model."
        ),
        "requirements": [
            "Design operating models for agentic AI deployment",
            "Multi-agent orchestration and MCP-based integration strategy",
            "Enterprise change management and adoption",
        ],
        "track": "ai_native", "seniority": "head_vp",
        "comp_min": 280000, "comp_max": 340000, "comp_currency": "USD",
        "comp_confidence": "Confirmed", "comp_note": "Significant equity component.",
        "ai_mandate": True,
        "mandate_evidence": "own the deployment operating model",
        "relevance": 0.86, "relevance_note": "AI-native track, remote.",
        "source_note": "",
    },
    {
        "company": "[DEMO] Ashgrove Advisory",
        "title": "Partner, AI Strategy Practice",
        "location": "New York, NY",
        "remote_policy": "hybrid",
        "url": "https://example.invalid/ashgrove/partner-ai",
        "posted_at": None, "posted_at_is_exact": False,
        "description": "Build out the firm's AI strategy practice from a standing start.",
        "requirements": [
            "Build an AI advisory practice and its point of view",
            "AI governance and regulatory advisory for regulated clients",
        ],
        "track": "consulting", "seniority": "head_vp",
        "comp_min": 250000, "comp_max": 300000, "comp_currency": "USD",
        "comp_confidence": "Estimated",
        "comp_note": "Estimated from partner band; profit share on top.",
        "ai_mandate": True,
        "mandate_evidence": "build out the firm's AI strategy practice",
        "relevance": 0.79, "relevance_note": "Consulting track; comp at the floor.",
        "source_note": "",
    },
]

DEMO_SIGNALS = [
    {
        "company": "[DEMO] Cascade Logistics",
        "signal_type": "ai_initiative",
        "headline": "Cascade announces $400m AI transformation programme",
        "detail": (
            "Three-year programme across network planning and customer operations. "
            "No AI leader named, and the CIO said the search is under way."
        ),
        "url": "https://example.invalid/news/cascade-ai",
        "signal_date": "2026-08-28", "strength": 0.9,
    },
    {
        "company": "[DEMO] Brightline Bank",
        "signal_type": "leadership_gap",
        "headline": "Brightline's Chief Data Officer departs after four years",
        "detail": "Leaves the AI agenda without an owner mid-programme.",
        "url": "https://example.invalid/news/brightline",
        "signal_date": "2026-09-01", "strength": 0.75,
    },
]

DEMO_TARGETS = [
    {
        "person_name": "[DEMO] Dana Reid", "person_title": "Chief Strategy Officer",
        "company": "[DEMO] Northwind Insurance", "rec_type": "person",
        "rationale": (
            "Reid owns the strategy function this role reports into, and has spoken "
            "publicly about the insurer's AI programme twice this year."
        ),
        "suggested_action": (
            "Reference their InsurTech Connect talk on risk-tiering and ask how the "
            "governance framework is landing with the model risk team."
        ),
        "evidence_note": "Keynote on AI governance in insurance, June 2026.",
        "score": 0.9, "job_index": 0, "is_latent": False,
    },
    {
        "person_name": "[DEMO] Sam Okafor", "person_title": "Managing Director, Portfolio Operations",
        "company": "[DEMO] Vantage Partners Capital", "rec_type": "engagement",
        "rationale": (
            "Published a piece last week arguing most portfolio AI pilots never reach "
            "the P&L - directly adjacent to the harvest problem."
        ),
        "suggested_action": (
            "Comment on the harvest point specifically, with the released-capacity "
            "framing, rather than a generic note of agreement."
        ),
        "evidence_note": "LinkedIn article, 2 September 2026.",
        "score": 0.82, "job_index": 1, "is_latent": False,
    },
    {
        "person_name": "[DEMO] Priya Raman", "person_title": "Chief Information Officer",
        "company": "[DEMO] Cascade Logistics", "rec_type": "person",
        "rationale": (
            "Announced the $400m programme and said the AI leadership search is under "
            "way. No posting exists yet, so this is a genuine head start."
        ),
        "suggested_action": (
            "Reach out referencing the programme announcement, positioning around "
            "network planning rather than a generic AI pitch."
        ),
        "evidence_note": "Press announcement, 28 August 2026.",
        "score": 0.86, "signal_index": 0, "is_latent": True,
    },
]


def load() -> None:
    from app.jobs import scoring

    with db.session() as conn:
        if db.scalar(conn, "SELECT COUNT(*) FROM jobs", (), 0):
            print("  Demo data already loaded.")
            return

        job_ids = []
        for posting in DEMO_POSTINGS:
            job_id, _ = repository.upsert_job(
                conn, posting, source_name="Demo data", source_kind="demo"
            )
            job_ids.append(job_id)

        signal_ids = []
        for signal in DEMO_SIGNALS:
            signal_id, _ = repository.upsert_signal(conn, signal)
            signal_ids.append(signal_id)

        # Shortlist two, so the networking module has a reason to exist.
        repository.set_decision(conn, job_ids[0], "shortlisted", "Best fit so far.")
        repository.set_decision(conn, job_ids[1], "shortlisted")
        repository.set_decision(conn, job_ids[4], "dismissed", "Comp at the floor.")

        now = db.utcnow()
        for target in DEMO_TARGETS:
            db.insert(conn, "networking_targets", {
                "fingerprint": scoring.fingerprint(
                    target["company"], target["person_name"]
                ),
                "company": target["company"],
                "person_name": target["person_name"],
                "person_title": target["person_title"],
                "profile_url": None,
                "rec_type": target["rec_type"],
                "rationale": target["rationale"],
                "suggested_action": target["suggested_action"],
                "evidence_url": None,
                "evidence_note": target["evidence_note"],
                "job_id": job_ids[target["job_index"]] if "job_index" in target else None,
                "is_latent": 1 if target["is_latent"] else 0,
                "signal_id": signal_ids[target["signal_index"]] if "signal_index" in target else None,
                "score": target["score"],
                "status": "active",
                "created_at": now, "updated_at": now,
            })

        targets.rerank(conn)

        from app.gap import engine
        engine.recompute(conn, reason="demo data loaded")

        print(f"  Loaded {len(job_ids)} demo postings, {len(signal_ids)} signals, "
              f"{len(DEMO_TARGETS)} networking targets.")


def main() -> int:
    app = create_app()
    load()
    url = f"http://{config.HOST}:{config.PORT}"
    print()
    print("  AI Career Platform - DEMO MODE")
    print("  All data is made up and prefixed [DEMO].")
    print(f"  Database: {config.DATABASE_PATH}")
    print(f"  Open: {url}")
    print()
    app.run(host=config.HOST, port=config.PORT, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
