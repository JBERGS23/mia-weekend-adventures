"""The sourcing catalogue (spec 1.4).

Each source is one research call. They are deliberately varied: four cover the
four target tracks by searching broadly across company career pages and press
releases, three cover specific channels (niche AI job boards, executive search
firms, PE/VC portfolio pages), and one collects market signals rather than
postings.

Overlap between sources is expected and fine. The point is not missing a role
LinkedIn's algorithm never showed Jeff; duplicates are collapsed by the dedupe
step, which costs nothing.

Adding a source means adding one entry to SOURCES. Nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import config

SourceKind = Literal["jobs", "signals"]


@dataclass(frozen=True)
class Source:
    key: str
    label: str
    kind: SourceKind

    # What Claude should go and look for. Combined with the shared instructions
    # in extraction.py, which carry the rules that apply to every source.
    brief: str

    # Default track for postings from this source. The model can override it
    # per posting; this is the prior, not a constraint.
    default_track: str | None = None

    # Restricting a source to specific domains makes it sharper, but also
    # blinder. Only used where the source *is* a set of named sites.
    allowed_domains: tuple[str, ...] = field(default_factory=tuple)

    max_searches: int = config.MAX_SEARCHES_PER_SOURCE

    # Set False to skip a source without deleting it.
    enabled: bool = True


TITLE_LIST = "\n".join(f"  - {title}" for title in config.TARGET_TITLES)


SOURCES: tuple[Source, ...] = (
    # ---- Track 1: AI-native companies ---------------------------------
    Source(
        key="ai_native",
        label="AI-native companies",
        kind="jobs",
        default_track="ai_native",
        brief=(
            "Find current openings at AI-native companies - foundation model labs, "
            "AI infrastructure and tooling companies, applied AI product companies, "
            "and well-funded AI startups at Series B and beyond - for senior strategy "
            "or transformation leadership.\n\n"
            "Search their career pages directly and through job aggregators. Cover a "
            "mix of the large well-known labs and less obvious mid-size AI companies, "
            "since the whole point is finding roles a LinkedIn feed would not surface."
        ),
    ),
    # ---- Track 2: traditional companies with an AI mandate ------------
    Source(
        key="traditional_transformation",
        label="Traditional companies undergoing AI transformation",
        kind="jobs",
        default_track="traditional_transformation",
        brief=(
            "Find current openings at large non-AI companies - banks, insurers, "
            "healthcare, retail, industrials, telecoms, media, logistics - for "
            "leadership roles carrying an explicit AI transformation mandate.\n\n"
            "This is the source where the mandate often does NOT appear in the job "
            "title. A posting titled 'VP Corporate Strategy' or 'Head of Strategy' "
            "whose description is substantially about leading the company's AI agenda "
            "is exactly what this source is for, and is more valuable than an obvious "
            "'Head of AI' title. Read the descriptions, not just the titles.\n\n"
            "Search company career pages and recent press releases announcing AI "
            "transformation programmes, then look for the leadership roles being "
            "hired to run them."
        ),
    ),
    # ---- Track 3: PE / VC --------------------------------------------
    Source(
        key="pe_vc",
        label="PE and VC firms",
        kind="jobs",
        default_track="pe_vc",
        brief=(
            "Find current openings at private equity and venture capital firms for AI "
            "strategy roles that serve portfolio companies - typically titled "
            "operating partner, value creation, portfolio operations, or similar, with "
            "an AI or digital transformation remit.\n\n"
            "Search the careers and team pages of large and mid-market PE firms and "
            "growth investors, plus press coverage of firms building out AI value "
            "creation capability."
        ),
    ),
    # ---- Track 4: consulting / advisory -------------------------------
    Source(
        key="consulting",
        label="Consulting and advisory firms",
        kind="jobs",
        default_track="consulting",
        brief=(
            "Find current openings at consulting and advisory firms building out or "
            "scaling an AI practice - strategy firms, the large accounting and "
            "technology consultancies, boutique AI advisories, and systems "
            "integrators - for practice leadership, partner, or principal-level roles "
            "focused on AI strategy and transformation.\n\n"
            "Also look for firms that have publicly announced new AI practices or "
            "large AI investments recently, since they are usually hiring into them."
        ),
    ),
    # ---- Channel: niche AI job boards ---------------------------------
    Source(
        key="ai_job_boards",
        label="AI-specific job boards",
        kind="jobs",
        brief=(
            "Search AI-specific and specialist job boards for senior AI strategy and "
            "transformation leadership roles. Boards worth covering include "
            "aijobs.com, aijobs.ai, hiringcafe.com, ai-jobs.net, and comparable "
            "specialist aggregators.\n\n"
            "These boards skew technical, so filter hard for strategy and "
            "transformation leadership rather than engineering or research roles. "
            "Report the company and the original posting URL where you can find it."
        ),
    ),
    # ---- Channel: executive search ------------------------------------
    Source(
        key="exec_search",
        label="Executive search firms",
        kind="jobs",
        brief=(
            "Check the public 'current searches', 'open roles' or 'opportunities' "
            "pages of executive search firms active in AI leadership hiring. Firms "
            "worth checking include Christian & Timbers, Cowen Partners, Keller "
            "Executive Search, Russell Reynolds Associates, Heidrick & Struggles, "
            "Spencer Stuart, Egon Zehnder, True Search and Riviera Partners.\n\n"
            "Retained searches are often listed without naming the client. That is "
            "still worth reporting: use a descriptive company field such as "
            "'Confidential - Fortune 500 insurer (via Cowen Partners)' and say so in "
            "the notes. These roles rarely appear on public job boards, which makes "
            "them disproportionately valuable."
        ),
    ),
    # ---- Channel: PE/VC portfolio companies ---------------------------
    Source(
        key="pe_portfolio",
        label="PE/VC portfolio companies",
        kind="jobs",
        brief=(
            "Search the job pages that private equity and venture firms maintain for "
            "their portfolio companies, and portfolio company career pages directly, "
            "for senior AI strategy or transformation leadership roles.\n\n"
            "Many large funds run a shared talent or jobs board across their "
            "portfolio. AI transformation demand runs heavily through portfolio "
            "companies under pressure to show AI-driven value creation, so this is a "
            "high-yield channel that general job search misses."
        ),
    ),
    # ---- Signals: latent demand ---------------------------------------
    Source(
        key="market_signals",
        label="Market signals and latent demand",
        kind="signals",
        brief=(
            "Find recent public signals suggesting a company will soon need senior AI "
            "strategy or transformation leadership, whether or not a role is posted.\n\n"
            "Look for: funding rounds at AI companies large enough to imply a "
            "leadership build-out; newly appointed Chief AI Officers or Heads of AI "
            "at peer companies (which signals both the trend and the teams they will "
            "hire beneath them); public announcements of AI transformation programmes "
            "or dedicated AI budgets; consulting firms launching or scaling AI "
            "practices; and executive departures leaving an AI leadership gap.\n\n"
            "This source feeds proactive networking rather than the job list, so "
            "prefer signals that give a genuine reason to reach out to a named "
            "company in the next few weeks."
        ),
    ),
)


SOURCES_BY_KEY: dict[str, Source] = {source.key: source for source in SOURCES}


def enabled_sources(kind: SourceKind | None = None) -> list[Source]:
    return [
        source
        for source in SOURCES
        if source.enabled and (kind is None or source.kind == kind)
    ]
