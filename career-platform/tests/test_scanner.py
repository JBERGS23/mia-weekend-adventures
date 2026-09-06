"""Scan orchestration: dedupe, skill signals, decisions, archive, resilience."""

from __future__ import annotations

from app import db
from app.jobs import repository, scanner
from tests.conftest import FakeResearchClient, make_posting


def jobs_payload(*postings):
    return {"postings": list(postings), "coverage_note": "test"}


def signals_payload(*signals):
    return {"signals": list(signals), "coverage_note": "test"}


SIGNAL = {
    "company": "Globex",
    "signal_type": "funding",
    "headline": "Globex raises $200m Series C",
    "detail": "Plans to build out an enterprise AI function.",
    "url": "https://example.com/globex",
    "signal_date": "2026-08-30",
    "strength": 0.8,
}


class TestUpsert:
    def test_new_posting_is_stored_and_scored(self, seeded):
        with db.session() as conn:
            job_id, is_new = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )
            assert is_new is True
            job = repository.get_job(conn, job_id)
            assert job["company"] == "Northwind Insurance"
            assert job["fit_score"] > 0.8
            assert job["comp_confidence"] == "Confirmed"
            assert job["decision"] is None

    def test_second_sighting_is_not_new(self, seeded):
        """Spec 1.5: nothing already shown is ever surfaced as new again."""
        with db.session() as conn:
            first_id, first_new = repository.upsert_job(
                conn, make_posting(), source_name="Board A", source_kind="a"
            )
            second_id, second_new = repository.upsert_job(
                conn,
                make_posting(url="https://elsewhere.com/same-role"),
                source_name="Board B",
                source_kind="b",
            )
            assert first_new is True and second_new is False
            assert first_id == second_id
            assert db.scalar(conn, "SELECT COUNT(*) FROM jobs") == 1

    def test_second_sighting_does_not_overwrite_a_decision(self, seeded):
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="A", source_kind="a"
            )
            repository.set_decision(conn, job_id, "shortlisted", "worth a look")
            repository.upsert_job(conn, make_posting(), source_name="B", source_kind="b")
            assert repository.get_job(conn, job_id)["decision"] == "shortlisted"

    def test_posting_without_company_is_rejected(self, seeded):
        with db.session() as conn:
            job_id, is_new = repository.upsert_job(
                conn, make_posting(company=""), source_name="A", source_kind="a"
            )
            assert job_id is None and is_new is False

    def test_requirements_become_gap_engine_signals(self, seeded):
        """Spec 1.6 live layer: requirements are mapped onto academy modules."""
        with db.session() as conn:
            repository.upsert_job(conn, make_posting(), source_name="A", source_kind="a")
            rows = db.query(
                conn, "SELECT DISTINCT module_key FROM job_skill_signals"
            )
            modules = {row["module_key"] for row in rows}
            assert "governance" in modules
            assert "strategy_fundamentals" in modules


class TestDecisions:
    def test_decision_history_is_append_only(self, seeded):
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="A", source_kind="a"
            )
            repository.set_decision(conn, job_id, "dismissed", "too junior")
            repository.set_decision(conn, job_id, "shortlisted", "changed my mind")
            history = repository.decision_history(conn, job_id)
            assert len(history) == 2
            assert repository.get_job(conn, job_id)["decision"] == "shortlisted"

    def test_dismissed_stays_in_the_archive(self, seeded):
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="A", source_kind="a"
            )
            repository.set_decision(conn, job_id, "dismissed")
            assert len(repository.search_archive(conn)) == 1
            assert len(repository.new_jobs(conn)) == 0


class TestArchiveSearch:
    def test_filters_combine(self, seeded):
        with db.session() as conn:
            repository.upsert_job(conn, make_posting(), source_name="A", source_kind="a")
            repository.upsert_job(
                conn,
                make_posting(company="Initech", title="VP AI Strategy", track="ai_native",
                             url="https://example.com/jobs/initech-vp"),
                source_name="B",
                source_kind="b",
            )
            assert len(repository.search_archive(conn, text="Initech")) == 1
            assert len(repository.search_archive(conn, track="ai_native")) == 1
            assert len(repository.search_archive(conn, decision="undecided")) == 2
            assert len(repository.search_archive(conn, source="A")) == 1


class TestScanRun:
    def test_full_scan_stores_jobs_and_signals(self, seeded):
        from app.jobs.sources import enabled_sources

        sources = enabled_sources()
        payloads = []
        for source in sources:
            if source.kind == "signals":
                payloads.append(signals_payload(SIGNAL))
            else:
                payloads.append(
                    jobs_payload(make_posting(company=f"Co {source.key}",
                                              url=f"https://example.com/{source.key}"))
                )

        client = FakeResearchClient(payloads)
        run_id = scanner.run_scan(client)

        with db.session() as conn:
            run = db.query_one(conn, "SELECT * FROM scan_runs WHERE id = ?", (run_id,))
            assert run["status"] == "complete"
            assert run["sources_run"] == len(sources)
            job_sources = [s for s in sources if s.kind == "jobs"]
            assert run["jobs_new"] == len(job_sources) + 1  # + the signal
            assert db.scalar(conn, "SELECT COUNT(*) FROM market_signals") == 1

    def test_one_failing_source_does_not_kill_the_scan(self, seeded):
        """A dead job board must not cost the other sources."""
        from app.jobs.sources import enabled_sources

        sources = enabled_sources()
        payloads = [RuntimeError("board is down")]
        for source in sources[1:]:
            payloads.append(
                signals_payload(SIGNAL)
                if source.kind == "signals"
                else jobs_payload(make_posting(company=f"Co {source.key}",
                                              url=f"https://example.com/{source.key}"))
            )

        run_id = scanner.run_scan(FakeResearchClient(payloads))
        with db.session() as conn:
            run = db.query_one(conn, "SELECT * FROM scan_runs WHERE id = ?", (run_id,))
            assert run["status"] == "complete"
            assert "board is down" in (run["error"] or "")
            assert db.scalar(conn, "SELECT COUNT(*) FROM jobs") > 0

    def test_scan_without_api_key_refuses_cleanly(self, seeded):
        started, message = scanner.start_scan(FakeResearchClient(available=False))
        assert started is False
        assert "ANTHROPIC_API_KEY" in message

    def test_scan_recomputes_gap_weights(self, seeded):
        """Spec 1.6 -> 2.3: a scan changes what the academy prioritises."""
        from app.jobs.sources import enabled_sources

        governance_heavy = make_posting(
            requirements=[
                "Own AI governance and regulatory compliance",
                "Deep knowledge of the EU AI Act and US state AI rules",
                "Build risk tiering for AI deployments",
            ]
        )
        payloads = []
        for index, source in enumerate(enabled_sources()):
            if source.kind == "signals":
                payloads.append(signals_payload(SIGNAL))
            else:
                payloads.append(
                    jobs_payload(
                        dict(governance_heavy, company=f"Co {index}",
                             url=f"https://example.com/{index}")
                    )
                )

        with db.session() as conn:
            before = db.query_one(
                conn, "SELECT priority FROM gap_state WHERE module_key = 'governance'"
            )["priority"]

        scanner.run_scan(FakeResearchClient(payloads))

        with db.session() as conn:
            after = db.query_one(
                conn, "SELECT priority FROM gap_state WHERE module_key = 'governance'"
            )["priority"]
        assert after > before


class TestPrompts:
    def test_every_job_source_carries_the_no_invention_rule(self, seeded):
        from app.jobs.sources import enabled_sources

        sources = enabled_sources()
        client = FakeResearchClient([jobs_payload() for _ in sources])
        scanner.run_scan(client)
        for call in client.calls:
            assert "NEVER invent" in call["prompt"] or "Never invent" in call["prompt"]

    def test_job_prompts_state_that_missing_comp_is_not_a_filter(self, seeded):
        from app.jobs.sources import enabled_sources

        client = FakeResearchClient([jobs_payload() for _ in enabled_sources()])
        scanner.run_scan(client)
        job_calls = [c for c in client.calls if "market_signals" not in c["purpose"]]
        assert job_calls
        assert all("NOT a reason to exclude" in c["prompt"] for c in job_calls)
