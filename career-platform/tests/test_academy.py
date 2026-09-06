"""Academy: rotation, answering, feedback, resources, question generation."""

from __future__ import annotations

import collections

from app import db
from app.academy import content, quiz
from app.academy.modules import MODULE_KEYS
from app.gap import engine
from tests.conftest import FakeResearchClient


class TestRotation:
    def test_daily_quiz_has_the_configured_number_of_questions(self, seeded):
        import config

        with db.session() as conn:
            questions = quiz.get_or_build_daily(conn, "2026-09-06")
            assert len(questions) == config.QUESTIONS_PER_DAY

    def test_quiz_is_stable_within_a_day(self, seeded):
        """Opening the app twice must not reshuffle today's questions."""
        with db.session() as conn:
            first = quiz.get_or_build_daily(conn, "2026-09-06")
            second = quiz.get_or_build_daily(conn, "2026-09-06")
        assert [q["question_id"] for q in first] == [q["question_id"] for q in second]

    def test_rotation_leans_toward_the_weakest_modules(self, seeded):
        """Spec 2.3: gap-weighted, not tied to whatever module is being read."""
        with db.session() as conn:
            priorities = engine.priorities(conn)

        tally = collections.Counter()
        for day in range(300):
            tally.update(quiz.choose_modules(priorities, f"day-{day}"))

        assert tally["governance"] > tally["strategy_fundamentals"]
        assert tally["governance"] > tally["change_adoption"]

    def test_change_management_is_deliberately_lighter(self, seeded):
        """Spec 2.3: Jeff's strongest area gets the least airtime..."""
        with db.session() as conn:
            priorities = engine.priorities(conn)
        tally = collections.Counter()
        for day in range(300):
            tally.update(quiz.choose_modules(priorities, f"day-{day}"))
        assert tally["change_adoption"] == min(tally.values())

    def test_but_no_module_ever_disappears(self, seeded):
        """...without being crowded out entirely, so retention holds."""
        with db.session() as conn:
            priorities = engine.priorities(conn)
        tally = collections.Counter()
        for day in range(300):
            tally.update(quiz.choose_modules(priorities, f"day-{day}"))
        for key in MODULE_KEYS:
            assert tally[key] > 0

    def test_questions_are_not_repeated_within_a_day(self, seeded):
        with db.session() as conn:
            questions = quiz.get_or_build_daily(conn, "2026-09-06")
        ids = [q["question_id"] for q in questions]
        assert len(ids) == len(set(ids))

    def test_a_module_is_exhausted_before_any_question_repeats(self, seeded):
        """Unseen questions come first. Heavily weighted modules will exhaust
        their bank and start repeating - that is expected - but a module must
        never repeat while it still has unseen questions."""
        served = collections.defaultdict(list)
        with db.session() as conn:
            for day in range(10):
                for question in quiz.get_or_build_daily(conn, f"2026-09-{day + 1:02d}"):
                    served[question["module_key"]].append(question["question_id"])

            for module_key, ids in served.items():
                bank = db.scalar(
                    conn,
                    "SELECT COUNT(*) FROM quiz_questions WHERE module_key = ? AND status = 'active'",
                    (module_key,),
                )
                distinct = len(set(ids))
                # Either nothing repeated, or the whole bank was used up first.
                assert distinct == len(ids) or distinct == bank


class TestAnswering:
    def test_correct_answer_is_recorded(self, seeded):
        with db.session() as conn:
            questions = quiz.get_or_build_daily(conn, "2026-09-06")
            first = questions[0]
            result = quiz.answer(conn, first["attempt_id"], first["correct_index"])
            assert result["is_correct"] is True
            assert quiz.today_progress(conn, "2026-09-06")["correct"] == 1

    def test_wrong_answer_returns_the_explanation(self, seeded):
        with db.session() as conn:
            first = quiz.get_or_build_daily(conn, "2026-09-06")[0]
            wrong = (first["correct_index"] + 1) % len(first["options"])
            result = quiz.answer(conn, first["attempt_id"], wrong)
            assert result["is_correct"] is False
            assert len(result["explanation"]) > 20

    def test_a_question_cannot_be_answered_twice(self, seeded):
        with db.session() as conn:
            first = quiz.get_or_build_daily(conn, "2026-09-06")[0]
            quiz.answer(conn, first["attempt_id"], 0)
            assert quiz.answer(conn, first["attempt_id"], 1) is None

    def test_out_of_range_answer_is_rejected(self, seeded):
        with db.session() as conn:
            first = quiz.get_or_build_daily(conn, "2026-09-06")[0]
            assert quiz.answer(conn, first["attempt_id"], 99) is None

    def test_finishing_a_day_updates_the_gap_weights(self, seeded):
        """Spec 2.3 -> 1.6: quiz results feed back into priority."""
        with db.session() as conn:
            before = engine.priorities(conn)
            for question in quiz.get_or_build_daily(conn, "2026-09-06"):
                quiz.answer(conn, question["attempt_id"], question["correct_index"])
            after = engine.priorities(conn)
        assert before != after

    def test_streak_counts_completed_days(self, seeded):
        from datetime import date, timedelta

        with db.session() as conn:
            for offset in (2, 1, 0):
                day = (date.today() - timedelta(days=offset)).isoformat()
                for question in quiz.get_or_build_daily(conn, day):
                    quiz.answer(conn, question["attempt_id"], question["correct_index"])
            assert quiz.streak(conn) == 3


class TestContent:
    def test_every_module_has_a_substantial_primer(self, seeded):
        """Spec 2.2: 'not a one-pager'."""
        with db.session() as conn:
            for key in MODULE_KEYS:
                primer = content.get_primer(conn, key)
                assert primer is not None
                assert len(primer["body"]) > 8000

    def test_every_module_has_glossary_terms(self, seeded):
        with db.session() as conn:
            for key in MODULE_KEYS:
                assert len(content.glossary(conn, key)) >= 10

    def test_every_module_has_starter_questions(self, seeded):
        """The quiz must work on day one with no API key."""
        with db.session() as conn:
            for key in MODULE_KEYS:
                count = db.scalar(
                    conn,
                    "SELECT COUNT(*) FROM quiz_questions WHERE module_key = ?",
                    (key,),
                )
                assert count >= 8

    def test_reseeding_does_not_duplicate_or_reset(self, seeded):
        from app import seed

        with db.session() as conn:
            before = db.scalar(conn, "SELECT COUNT(*) FROM quiz_questions")
            for question in quiz.get_or_build_daily(conn, "2026-09-06"):
                quiz.answer(conn, question["attempt_id"], question["correct_index"])
            seed.seed_all(conn)
            assert db.scalar(conn, "SELECT COUNT(*) FROM quiz_questions") == before
            # History survives a re-seed.
            assert db.scalar(conn, "SELECT COUNT(*) FROM quiz_attempts") == 5


class TestFeedback:
    def test_more_of_this_raises_the_module_weight(self, seeded):
        with db.session() as conn:
            before = engine.priorities(conn)["technical_fluency"]
            for _ in range(3):
                content.record_feedback(conn, "technical_fluency", "more", "useful")
            after = engine.priorities(conn)["technical_fluency"]
        assert after > before

    def test_less_of_this_lowers_it(self, seeded):
        with db.session() as conn:
            before = engine.priorities(conn)["governance"]
            for _ in range(3):
                content.record_feedback(conn, "governance", "less")
            after = engine.priorities(conn)["governance"]
        assert after < before

    def test_feedback_is_a_nudge_not_an_override(self, seeded):
        """Feedback must not be able to invert the automated weighting."""
        with db.session() as conn:
            for _ in range(20):
                content.record_feedback(conn, "change_adoption", "more")
            priorities = engine.priorities(conn)
        assert priorities["governance"] > priorities["change_adoption"]

    def test_invalid_signal_is_rejected(self, seeded):
        with db.session() as conn:
            assert content.record_feedback(conn, "governance", "maybe") is False


class TestResourceRefresh:
    payload = {
        "resources": [
            {
                "title": "The EU AI Act explained for boards",
                "url": "https://example.com/eu-ai-act",
                "format": "article",
                "publisher": "Example Institute",
                "published_at": "2026-05-01",
                "why": "Covers deployer obligations the primer only summarises.",
                "rank": 0.9,
            },
            {
                "title": "Governance in practice",
                "url": "https://example.com/podcast",
                "format": "podcast",
                "publisher": "Example FM",
                "published_at": "2026-06-01",
                "why": "Practitioner detail on running an intake process.",
                "rank": 0.7,
            },
        ],
        "coverage_note": "test",
    }

    def test_links_are_stored_and_ranked(self, seeded):
        added, _ = content.refresh_resources(
            "governance", FakeResearchClient([self.payload])
        )
        assert added == 2
        with db.session() as conn:
            rows = content.resources(conn, "governance")
            assert [r["title"] for r in rows][0] == "The EU AI Act explained for boards"

    def test_refresh_is_idempotent_on_the_same_links(self, seeded):
        client = FakeResearchClient([self.payload, self.payload])
        content.refresh_resources("governance", client)
        content.refresh_resources("governance", client)
        with db.session() as conn:
            assert len(content.resources(conn, "governance")) == 2

    def test_surplus_links_are_retired_not_deleted(self, seeded):
        import config

        many = {
            "resources": [
                {
                    "title": f"Resource {i}",
                    "url": f"https://example.com/{i}",
                    "format": "article",
                    "publisher": "Example",
                    "published_at": None,
                    "why": "test",
                    "rank": 1.0 - i / 100,
                }
                for i in range(config.RESOURCES_PER_MODULE + 5)
            ],
            "coverage_note": "test",
        }
        content.refresh_resources("governance", FakeResearchClient([many]))
        with db.session() as conn:
            assert len(content.resources(conn, "governance")) == config.RESOURCES_PER_MODULE
            assert db.scalar(
                conn, "SELECT COUNT(*) FROM resources WHERE status = 'retired'"
            ) == 5

    def test_refresh_prompt_carries_the_quality_bar(self, seeded):
        client = FakeResearchClient([self.payload])
        content.refresh_resources("governance", client)
        prompt = client.calls[0]["prompt"]
        assert "QUALITY BAR" in prompt
        assert "Reject" in prompt or "reject" in prompt

    def test_no_api_key_degrades_with_a_message(self, seeded):
        added, message = content.refresh_resources(
            "governance", FakeResearchClient(available=False)
        )
        assert added == 0
        assert "API key" in message


class TestQuestionGeneration:
    payload = {
        "questions": [
            {
                "question": "A deployer heavily customises a vendor model. What changes?",
                "options": ["Nothing", "They become a provider", "They become an importer", "Tier drops"],
                "correct_index": 1,
                "explanation": "Substantial modification flips deployer to provider.",
                "style": "scenario",
            }
        ]
    }

    def test_generated_questions_join_the_bank(self, seeded):
        added, _ = content and quiz.generate_questions(
            "governance", client=FakeResearchClient([self.payload])
        )
        assert added == 1
        with db.session() as conn:
            row = db.query_one(
                conn,
                "SELECT * FROM quiz_questions WHERE source = 'generated'",
            )
            assert row["module_key"] == "governance"

    def test_generation_reads_the_primer_not_the_links(self, seeded):
        """Spec 2.3: quizzes must not assume external links were clicked."""
        client = FakeResearchClient([self.payload])
        quiz.generate_questions("governance", client=client)
        call = client.calls[0]
        assert call["use_search"] is False
        assert "PRIMER" in call["prompt"]

    def test_malformed_questions_are_dropped(self, seeded):
        bad = {
            "questions": [
                {"question": "", "options": ["a", "b"], "correct_index": 0,
                 "explanation": "x", "style": "recall"},
                {"question": "Out of range?", "options": ["a", "b"], "correct_index": 7,
                 "explanation": "x", "style": "recall"},
            ]
        }
        added, _ = quiz.generate_questions("governance", client=FakeResearchClient([bad]))
        assert added == 0
