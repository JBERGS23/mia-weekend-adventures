"""Fit scoring, compensation handling, and dedupe."""

from __future__ import annotations

from datetime import date, timedelta

import config
from app.jobs import scoring
from tests.conftest import make_posting


class TestDedupe:
    def test_same_role_different_formatting_collapses(self):
        a = scoring.fingerprint("Acme Corp.", "VP of AI Strategy", "New York, NY")
        b = scoring.fingerprint("Acme Corporation", "VP AI Strategy", "New York, NY (Hybrid)")
        assert a == b

    def test_vice_president_matches_vp(self):
        a = scoring.fingerprint("Acme", "Vice President AI Strategy", "Boston")
        b = scoring.fingerprint("Acme", "VP of AI Strategy", "Boston")
        assert a == b

    def test_different_companies_stay_separate(self):
        a = scoring.fingerprint("Acme", "Head of AI Strategy", "NYC")
        b = scoring.fingerprint("Globex", "Head of AI Strategy", "NYC")
        assert a != b

    def test_url_hash_ignores_tracking_params(self):
        a = scoring.hash_url("https://example.com/jobs/1?utm_source=linkedin")
        b = scoring.hash_url("https://example.com/jobs/1/")
        assert a == b


class TestCompensation:
    def test_confirmed_range_survives(self):
        comp = scoring.clean_compensation(make_posting())
        assert comp["comp_confidence"] == "Confirmed"
        assert comp["comp_min"] == 300000

    def test_no_numbers_forces_unknown(self):
        """A model claiming Confirmed with no figures is corrected, not trusted."""
        comp = scoring.clean_compensation(
            make_posting(comp_min=None, comp_max=None, comp_confidence="Confirmed")
        )
        assert comp["comp_confidence"] == "Unknown"

    def test_implausible_figure_is_discarded(self):
        comp = scoring.clean_compensation(make_posting(comp_min=180, comp_max=220))
        assert comp["comp_min"] is None
        assert comp["comp_confidence"] == "Unknown"

    def test_reversed_range_is_corrected(self):
        comp = scoring.clean_compensation(make_posting(comp_min=400000, comp_max=300000))
        assert comp["comp_min"] == 300000 and comp["comp_max"] == 400000

    def test_unknown_comp_is_not_scored_out_of_contention(self):
        """Spec 1.3: missing comp must never bury a strong role."""
        unknown = scoring.comp_fit({"comp_min": None, "comp_max": None})
        below = scoring.comp_fit({"comp_min": 150000, "comp_max": 170000})
        assert unknown > below
        assert unknown >= 0.5

    def test_below_floor_is_flagged_not_filtered(self):
        comp = scoring.clean_compensation(make_posting(comp_min=180000, comp_max=200000))
        assert scoring.below_floor(comp) is True
        assert comp["comp_min"] == 180000  # still stored, not dropped


class TestTitleMatching:
    def test_exact_target_titles_score_top(self):
        assert scoring.title_match("Head of AI Strategy") >= 0.95
        assert scoring.title_match("Chief AI Officer") >= 0.95

    def test_plain_strategy_title_scores_lower_but_survives(self):
        """Spec 1.1: these are caught by the description, not the title."""
        score = scoring.title_match("VP Corporate Strategy")
        assert 0.4 < score < 0.8

    def test_unrelated_title_scores_low(self):
        assert scoring.title_match("Senior Software Engineer") <= 0.25


class TestFitScore:
    def test_strong_match_scores_high(self):
        posting = make_posting()
        comp = scoring.clean_compensation(posting)
        score, rationale = scoring.score_posting(posting, comp)
        assert score > 0.85
        assert "explicit AI mandate" in rationale

    def test_strategy_title_with_mandate_beats_ai_title_without(self):
        """The whole point of reading descriptions rather than titles."""
        with_mandate = make_posting(
            title="VP Corporate Strategy", ai_mandate=True, relevance=0.8
        )
        without = make_posting(
            title="Head of AI Strategy", ai_mandate=False, relevance=0.45,
            comp_min=None, comp_max=None, comp_confidence="Unknown",
        )
        a, _ = scoring.score_posting(with_mandate, scoring.clean_compensation(with_mandate))
        b, _ = scoring.score_posting(without, scoring.clean_compensation(without))
        assert a > b

    def test_model_relevance_cannot_carry_a_posting_alone(self):
        """Relevance is weighted under 50%, so a bad fit cannot be talked up."""
        posting = make_posting(
            title="Software Engineer", seniority="other", ai_mandate=False,
            relevance=1.0, comp_min=None, comp_max=None, comp_confidence="Unknown",
        )
        score, _ = scoring.score_posting(posting, scoring.clean_compensation(posting))
        assert score < config.MIN_FIT_TO_SURFACE + 0.2

    def test_stale_postings_are_pushed_down(self):
        old = (date.today() - timedelta(days=200)).isoformat()
        fresh = make_posting(posted_at=date.today().isoformat())
        stale = make_posting(posted_at=old)
        a, _ = scoring.score_posting(fresh, scoring.clean_compensation(fresh))
        b, _ = scoring.score_posting(stale, scoring.clean_compensation(stale))
        assert a > b

    def test_rationale_is_always_populated(self):
        posting = make_posting()
        _, rationale = scoring.score_posting(posting, scoring.clean_compensation(posting))
        assert len(rationale) > 20


class TestFreshness:
    def test_recent_posting_is_fresh(self):
        recent = (date.today() - timedelta(days=2)).isoformat()
        assert scoring.is_fresh(recent, "2020-01-01") is True

    def test_old_posting_is_not_fresh_even_if_just_seen(self):
        old = (date.today() - timedelta(days=90)).isoformat()
        assert scoring.is_fresh(old, date.today().isoformat()) is False

    def test_undated_posting_is_fresh_while_newly_seen(self):
        assert scoring.is_fresh(None, date.today().isoformat()) is True

    def test_undated_posting_ages_out_of_the_new_view(self):
        long_ago = (date.today() - timedelta(days=60)).isoformat()
        assert scoring.is_fresh(None, long_ago) is False
