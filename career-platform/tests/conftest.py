"""Test fixtures.

Every test runs against a throwaway database, so nothing here can touch Jeff's
real data. The research layer is replaced by a fake client, so the whole suite
runs offline with no API key and no cost.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """Point every test at a fresh database file."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "test.db"
        monkeypatch.setattr(config, "DATABASE_PATH", path)
        yield path


@pytest.fixture
def seeded(temp_db):
    from app import db, seed

    db.init_db()
    with db.session() as conn:
        seed.seed_all(conn)
    return temp_db


@pytest.fixture
def app(seeded):
    from app import create_app

    application = create_app(testing=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


class FakeResearchClient:
    """Stands in for the Anthropic-backed client.

    Returns whatever payloads the test queues up, and records the prompts it was
    called with so tests can assert on how a module asked its question.
    """

    def __init__(self, payloads=None, available=True):
        self.payloads = list(payloads or [])
        self.available = available
        self.calls = []

    def research(self, *, purpose, system, prompt, schema, **kwargs):
        from app.research.client import ResearchResult

        self.calls.append(
            {"purpose": purpose, "system": system, "prompt": prompt, "schema": schema, **kwargs}
        )
        if not self.available:
            return ResearchResult(ok=False, error="no key")
        if not self.payloads:
            return ResearchResult(ok=True, data={})
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            return ResearchResult(ok=False, error=str(payload))
        return ResearchResult(ok=True, data=payload)


@pytest.fixture
def fake_client():
    return FakeResearchClient


def make_posting(**overrides):
    """A realistic scanner payload, so tests exercise the real shape."""
    posting = {
        "company": "Northwind Insurance",
        "title": "Head of AI Strategy",
        "location": "New York, NY",
        "remote_policy": "hybrid",
        "url": "https://example.com/jobs/head-ai-strategy",
        "posted_at": None,
        "posted_at_is_exact": False,
        "description": "Own the enterprise AI strategy and transformation agenda.",
        "requirements": [
            "Build a risk-tiered AI governance framework",
            "Working knowledge of the EU AI Act",
            "Lead use-case prioritisation and build/buy decisions",
        ],
        "track": "traditional_transformation",
        "seniority": "head_vp",
        "comp_min": 300000,
        "comp_max": 360000,
        "comp_currency": "USD",
        "comp_confidence": "Confirmed",
        "comp_note": "",
        "ai_mandate": True,
        "mandate_evidence": "own the enterprise AI transformation agenda",
        "relevance": 0.92,
        "relevance_note": "Direct match on title and mandate.",
        "source_note": "",
    }
    posting.update(overrides)
    return posting
