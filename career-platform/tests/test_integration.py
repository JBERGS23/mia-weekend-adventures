"""The integration pass from spec section 6.

Two loops have to work end to end, plus every page has to render:
  * shortlist -> networking trigger
  * gap engine -> quiz weighting
"""

from __future__ import annotations

import config
from app import db
from app.academy import content, quiz
from app.gap import engine
from app.jobs import repository, scanner
from app.networking import targets
from tests.conftest import FakeResearchClient, make_posting


class TestEveryPageRenders:
    def test_all_get_routes_return_200(self, client, app):
        urls = [
            "/", "/settings", "/jobs/", "/jobs/?tab=open", "/jobs/?tab=shortlisted",
            "/jobs/?tab=dismissed", "/jobs/archive", "/jobs/signals",
            "/academy/", "/academy/quiz", "/academy/glossary",
            "/networking/",
        ]
        from app.academy.modules import MODULE_KEYS

        urls += [f"/academy/{key}" for key in MODULE_KEYS]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, f"{url} returned {response.status_code}"

    def test_job_detail_renders(self, client, seeded):
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )
        assert client.get(f"/jobs/{job_id}").status_code == 200

    def test_unknown_module_redirects_rather_than_erroring(self, client):
        assert client.get("/academy/not-a-module").status_code == 302

    def test_scan_status_endpoint_returns_json(self, client):
        response = client.get("/scan/status")
        assert response.status_code == 200
        assert response.get_json()["status"] == "idle"

    def test_primer_renders_as_html_not_raw_markdown(self, client):
        response = client.get("/academy/governance")
        body = response.get_data(as_text=True)
        assert "<h2>" in body
        assert "## " not in body.split("<footer")[0]


class TestShortlistToNetworking:
    def test_the_full_loop(self, app, seeded, monkeypatch):
        """Spec 6.6: shortlist -> networking trigger, end to end."""
        payload = {
            "targets": [
                {
                    "rec_type": "person",
                    "person_name": "Dana Reid",
                    "person_title": "Chief Digital Officer",
                    "profile_url": "https://example.com/dana",
                    "rationale": "Owns the AI agenda and would own this role.",
                    "suggested_action": "Reference their recent post.",
                    "evidence_url": "https://example.com/post",
                    "evidence_note": "Recent piece on AI operating models.",
                    "score": 0.85,
                }
            ],
            "coverage_note": "test",
        }
        fake = FakeResearchClient([payload])
        monkeypatch.setattr("app.networking.targets.get_client", lambda: fake)

        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )

        client = app.test_client()
        # Nothing in networking before the shortlist.
        assert "Dana Reid" not in client.get("/networking/").get_data(as_text=True)

        response = client.post(
            f"/jobs/{job_id}/decision", data={"decision": "shortlisted"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        body = client.get("/networking/").get_data(as_text=True)
        assert "Dana Reid" in body
        assert "Northwind Insurance" in body

        with db.session() as conn:
            assert repository.get_job(conn, job_id)["decision"] == "shortlisted"

    def test_dismissing_does_not_trigger_networking(self, app, seeded, monkeypatch):
        fake = FakeResearchClient([])
        monkeypatch.setattr("app.networking.targets.get_client", lambda: fake)
        with db.session() as conn:
            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )
        app.test_client().post(
            f"/jobs/{job_id}/decision", data={"decision": "dismissed"},
            follow_redirects=True,
        )
        assert fake.calls == []


class TestGapToQuizWeighting:
    def test_the_full_loop(self, seeded):
        """Spec 6.6: gap engine -> quiz weighting, end to end.

        A market that suddenly demands technical fluency should pull the quiz
        mix toward it, even though the diagnostic baseline ranked it fourth.
        """
        import collections

        with db.session() as conn:
            before = engine.priorities(conn)
            before_mix = collections.Counter()
            for day in range(300):
                before_mix.update(quiz.choose_modules(before, f"a-{day}"))

            technical = make_posting(
                requirements=[
                    "Deep understanding of RAG and fine-tuning trade-offs",
                    "Fluency in LLM mechanics and data infrastructure",
                    "Own model evaluation and evals strategy",
                    "Assess vector database and data platform choices",
                ]
            )
            for index in range(40):
                repository.upsert_job(
                    conn,
                    dict(technical, company=f"Co {index}",
                         url=f"https://example.com/{index}"),
                    source_name="Test",
                    source_kind="test",
                )

            after = engine.recompute(conn, reason="test")
            after_mix = collections.Counter()
            for day in range(300):
                after_mix.update(quiz.choose_modules(after, f"a-{day}"))

        assert after["technical_fluency"] > before["technical_fluency"]
        assert after_mix["technical_fluency"] > before_mix["technical_fluency"]

    def test_feedback_reaches_the_quiz_mix(self, seeded):
        import collections

        with db.session() as conn:
            before = collections.Counter()
            for day in range(300):
                before.update(quiz.choose_modules(engine.priorities(conn), f"b-{day}"))
            for _ in range(4):
                content.record_feedback(conn, "strategy_fundamentals", "more")
            after = collections.Counter()
            for day in range(300):
                after.update(quiz.choose_modules(engine.priorities(conn), f"b-{day}"))
        assert after["strategy_fundamentals"] > before["strategy_fundamentals"]


class TestOfflineOperation:
    """Everything except live research must work with no API key at all."""

    def test_core_journey_works_without_a_key(self, app, seeded, monkeypatch):
        offline = FakeResearchClient(available=False)
        for module in (
            "app.jobs.scanner", "app.networking.targets",
            "app.academy.content", "app.academy.quiz",
        ):
            monkeypatch.setattr(f"{module}.get_client", lambda: offline)

        client = app.test_client()

        # Browse, take the quiz, shortlist - all fine.
        assert client.get("/academy/quiz").status_code == 200
        with db.session() as conn:
            questions = quiz.get_or_build_daily(conn)
            response = client.post(
                "/academy/quiz/answer",
                data={"attempt_id": questions[0]["attempt_id"], "chosen_index": 0},
                follow_redirects=True,
            )
            assert response.status_code == 200

            job_id, _ = repository.upsert_job(
                conn, make_posting(), source_name="Test", source_kind="test"
            )
        response = client.post(
            f"/jobs/{job_id}/decision", data={"decision": "shortlisted"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Scanning says so plainly rather than failing obscurely.
        body = client.post("/scan", follow_redirects=True).get_data(as_text=True)
        assert "ANTHROPIC_API_KEY" in body


class TestSpecInvariants:
    def test_the_five_modules_are_fixed(self, seeded):
        from app.academy.modules import MODULE_KEYS

        with db.session() as conn:
            rows = db.query(conn, "SELECT key FROM academy_modules ORDER BY sort_order")
        assert [row["key"] for row in rows] == list(MODULE_KEYS)
        assert len(MODULE_KEYS) == 5

    def test_baseline_matches_the_diagnostic(self, seeded):
        """Spec 2.5, loaded as the starting state rather than asked in-app."""
        expected = {
            "strategy_fundamentals": "moderate",
            "agentic_ai": "developing",
            "governance": "weak",
            "technical_fluency": "intermediate",
            "change_adoption": "strong",
        }
        with db.session() as conn:
            rows = db.query(conn, "SELECT module_key, baseline_level FROM gap_state")
        assert {row["module_key"]: row["baseline_level"] for row in rows} == expected

    def test_governance_starts_as_the_top_priority(self, seeded):
        with db.session() as conn:
            priorities = engine.priorities(conn)
        assert max(priorities, key=priorities.get) == "governance"

    def test_change_management_starts_lightest(self, seeded):
        with db.session() as conn:
            priorities = engine.priorities(conn)
        assert min(priorities, key=priorities.get) == "change_adoption"

    def test_priorities_always_sum_to_one(self, seeded):
        with db.session() as conn:
            assert abs(sum(engine.priorities(conn).values()) - 1.0) < 0.01

    def test_all_four_tracks_are_covered_by_sources(self, seeded):
        """Spec 1.2: four non-exclusive tracks."""
        from app.jobs.sources import SOURCES

        tracks = {source.default_track for source in SOURCES if source.default_track}
        assert tracks == {
            "ai_native", "traditional_transformation", "pe_vc", "consulting",
        }

    def test_sourcing_goes_wider_than_the_obvious_boards(self, seeded):
        """Spec 1.4: comprehensive, creative sourcing."""
        from app.jobs.sources import SOURCES

        keys = {source.key for source in SOURCES}
        assert {"exec_search", "pe_portfolio", "ai_job_boards", "market_signals"} <= keys
        assert len(SOURCES) >= 8

    def test_comp_is_never_a_hard_filter(self, seeded):
        """Spec 1.3: strong roles with unknown comp still surface."""
        with db.session() as conn:
            repository.upsert_job(
                conn,
                make_posting(comp_min=None, comp_max=None, comp_confidence="Unknown"),
                source_name="Test", source_kind="test",
            )
            queue = repository.new_jobs(conn)
        assert len(queue) == 1
        assert queue[0]["comp_confidence"] == "Unknown"

    def test_networking_cap_is_between_five_and_ten(self, seeded):
        assert config.NETWORKING_MIN_ACTIVE == 5
        assert config.NETWORKING_MAX_ACTIVE == 10
