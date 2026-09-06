"""Networking: shortlist trigger, ranking, the cap, and latent reservation."""

from __future__ import annotations

import config
from app import db
from app.jobs import repository
from app.networking import targets
from tests.conftest import FakeResearchClient, make_posting


def target_payload(*names, latent_hint=False):
    return {
        "targets": [
            {
                "rec_type": "person",
                "person_name": name,
                "person_title": "Chief Digital Officer",
                "profile_url": f"https://example.com/{name.replace(' ', '-').lower()}",
                "rationale": f"{name} owns the AI agenda and would own this role.",
                "suggested_action": "Reference their recent post on agent governance.",
                "evidence_url": "https://example.com/post",
                "evidence_note": "Published a piece on AI operating models last week.",
                "score": 0.8,
            }
            for name in names
        ],
        "coverage_note": "test",
    }


def shortlist_a_job(conn, **overrides):
    job_id, _ = repository.upsert_job(
        conn, make_posting(**overrides), source_name="Test", source_kind="test"
    )
    repository.set_decision(conn, job_id, "shortlisted")
    return job_id


class TestTrigger:
    def test_shortlisting_generates_targets(self, seeded):
        """Spec 3.2: shortlisting is the trigger."""
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        added, _ = targets.generate_for_job(
            job_id, FakeResearchClient([target_payload("Dana Reid", "Sam Okafor")])
        )
        assert added == 2
        with db.session() as conn:
            rows = targets.active(conn)
            assert len(rows) == 2
            assert rows[0]["job_id"] == job_id

    def test_undecided_job_generates_nothing(self, seeded):
        """Spec 3.2: not every company the scanner surfaces."""
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )
        added, message = targets.generate_for_job(
            job_id, FakeResearchClient([target_payload("Dana Reid")])
        )
        assert added == 0
        assert "shortlisted" in message

    def test_duplicate_people_are_not_added_twice(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        client = FakeResearchClient([target_payload("Dana Reid"), target_payload("Dana Reid")])
        targets.generate_for_job(job_id, client)
        targets.generate_for_job(job_id, client)
        with db.session() as conn:
            assert len(targets.active(conn)) == 1

    def test_prompt_forbids_private_details(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        client = FakeResearchClient([target_payload("Dana Reid")])
        targets.generate_for_job(job_id, client)
        call = client.calls[0]
        assert "Public professional information only" in call["prompt"]
        assert "never report personal contact details" in call["system"].lower()

    def test_no_api_key_degrades_with_a_message(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        added, message = targets.generate_for_job(
            job_id, FakeResearchClient(available=False)
        )
        assert added == 0 and "API key" in message


class TestRankingAndCap:
    def test_open_role_outranks_latent(self, seeded):
        """Spec 3.5: a concrete reason to reach out ranks higher."""
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
            signal_id = db.insert(
                conn,
                "market_signals",
                {
                    "fingerprint": "sig1", "company": "Globex", "signal_type": "funding",
                    "headline": "Globex raises $200m", "detail": "", "url": None,
                    "signal_date": None, "strength": 0.8, "created_at": db.utcnow(),
                },
            )
        targets.generate_for_job(job_id, FakeResearchClient([target_payload("Dana Reid")]))
        targets.generate_for_signal(
            signal_id, FakeResearchClient([target_payload("Alex Chen")])
        )
        with db.session() as conn:
            rows = targets.active(conn)
        assert rows[0]["person_name"] == "Dana Reid"

    def test_cap_is_enforced(self, seeded):
        """Spec 3.1: never a 200-person task list."""
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        names = [f"Person {i}" for i in range(20)]
        targets.generate_for_job(job_id, FakeResearchClient([target_payload(*names)]))
        with db.session() as conn:
            assert len(targets.active(conn)) == config.NETWORKING_MAX_ACTIVE

    def test_surplus_targets_age_out_rather_than_being_deleted(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        names = [f"Person {i}" for i in range(20)]
        targets.generate_for_job(job_id, FakeResearchClient([target_payload(*names)]))
        with db.session() as conn:
            assert len(targets.by_status(conn, "aged_out")) == 20 - config.NETWORKING_MAX_ACTIVE

    def test_latent_targets_keep_reserved_slots(self, seeded):
        """Spec 3.5: latent targets are never crowded out entirely, which is
        where the proactive edge over a normal job search lives."""
        with db.session() as conn:
            signal_id = db.insert(
                conn,
                "market_signals",
                {
                    "fingerprint": "sig1", "company": "Globex", "signal_type": "funding",
                    "headline": "Globex raises $200m", "detail": "", "url": None,
                    "signal_date": None, "strength": 0.9, "created_at": db.utcnow(),
                },
            )
        # Two latent targets first...
        targets.generate_for_signal(
            signal_id, FakeResearchClient([target_payload("Latent One", "Latent Two")])
        )
        # ...then a flood of higher-ranked targets with open roles.
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        names = [f"Person {i}" for i in range(20)]
        targets.generate_for_job(job_id, FakeResearchClient([target_payload(*names)]))

        with db.session() as conn:
            active = targets.active(conn)
            latent = [row for row in active if row["is_latent"]]
        assert len(active) == config.NETWORKING_MAX_ACTIVE
        assert len(latent) >= config.LATENT_RESERVED_SLOTS

    def test_capacity_reports_room(self, seeded):
        with db.session() as conn:
            capacity = targets.capacity(conn)
            assert capacity["active"] == 0
            assert capacity["below_min"] is True
            assert capacity["max"] == config.NETWORKING_MAX_ACTIVE


class TestStatus:
    def test_marking_done_frees_a_slot(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        targets.generate_for_job(
            job_id, FakeResearchClient([target_payload("Dana Reid", "Sam Okafor")])
        )
        with db.session() as conn:
            first = targets.active(conn)[0]
            targets.set_status(conn, first["id"], "done", "sent a note")
            assert len(targets.active(conn)) == 1
            assert len(targets.by_status(conn, "done")) == 1

    def test_unknown_status_is_rejected(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        targets.generate_for_job(job_id, FakeResearchClient([target_payload("Dana Reid")]))
        with db.session() as conn:
            first = targets.active(conn)[0]
            assert targets.set_status(conn, first["id"], "maybe") is False


class TestWarmIntroDeferral:
    def test_schema_supports_warm_intros_without_generating_them(self, seeded):
        """Spec 3.3: deferred to a later phase, but no rework needed to add it."""
        with db.session() as conn:
            columns = {
                row["name"]
                for row in db.query(conn, "PRAGMA table_info(networking_targets)")
            }
        assert {"connector_name", "connector_context"} <= columns

    def test_phase_one_never_produces_a_warm_intro(self, seeded):
        with db.session() as conn:
            job_id = shortlist_a_job(conn)
        targets.generate_for_job(job_id, FakeResearchClient([target_payload("Dana Reid")]))
        with db.session() as conn:
            rows = db.query(conn, "SELECT rec_type FROM networking_targets")
        assert all(row["rec_type"] in ("person", "engagement") for row in rows)
