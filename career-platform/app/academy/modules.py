"""The five fixed academy modules.

These are permanent (spec 2.1). Content inside a module changes constantly;
this list does not. Everything else in the app - the gap engine, quiz rotation,
job-requirement classification - keys off `MODULE_KEYS`, so adding a sixth
module would be a deliberate, single-place change rather than an accident.

The starting proficiency levels come from spec 2.5, established by diagnostic
interview rather than an in-app onboarding flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Proficiency levels mapped to a 0..1 score. The gap engine turns these into
# "how much room is left to improve" (1 - score), so weak modules pull weight.
LEVEL_SCORES: dict[str, float] = {
    "weak": 0.20,
    "developing": 0.40,
    "moderate": 0.60,
    "intermediate": 0.62,
    "strong": 0.85,
}


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    name: str
    blurb: str
    sort_order: int

    # Starting state from the spec 2.5 diagnostic.
    baseline_level: str
    baseline_note: str

    # Deliberate weighting thumb on the scale. Only change management is
    # damped, because Jeff is already strong there (spec 2.3).
    weight_damping: float = 1.0

    # Used to map job-description requirements onto this module without
    # needing an API call. The research layer refines this when available.
    keywords: tuple[str, ...] = field(default_factory=tuple)


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        key="strategy_fundamentals",
        name="AI Strategy Fundamentals",
        blurb=(
            "Use-case prioritisation, build/buy/partner, ROI frameworks, "
            "vendor and platform selection."
        ),
        sort_order=1,
        baseline_level="moderate",
        baseline_note=(
            "Real experience at the platform/vendor-selection and decision-framework "
            "level (e.g. Claude Enterprise vs. Copilot vs. GPT decisions); not "
            "hands-on technical evaluation."
        ),
        keywords=(
            "use case prioritization", "use-case prioritisation", "build vs buy",
            "build/buy", "roi", "business case", "vendor selection", "platform selection",
            "ai roadmap", "ai strategy", "portfolio prioritization", "value realization",
            "operating plan", "investment case", "make or buy", "total cost of ownership",
        ),
    ),
    ModuleSpec(
        key="agentic_ai",
        name="Agentic AI & Orchestration",
        blurb=(
            "Single-agent vs. multi-agent workflows, tool use, MCP, and operating "
            "models for deploying agents."
        ),
        sort_order=2,
        baseline_level="developing",
        baseline_note=(
            "Understands orchestration and operating-model considerations conceptually "
            "(has authored an internal proposal); recognises terms like multi-agent "
            "workflows and MCP but lacks confident, precise command of them; limited "
            "to one real example."
        ),
        keywords=(
            "agent", "agentic", "multi-agent", "orchestration", "tool use",
            "mcp", "model context protocol", "workflow automation", "copilot deployment",
            "autonomous", "agent framework", "human in the loop", "human-in-the-loop",
        ),
    ),
    ModuleSpec(
        key="governance",
        name="AI Governance & Regulation",
        blurb=(
            "Risk-tiering frameworks, the EU AI Act, U.S. state-level rules, and "
            "sector-specific regulation beyond financial services."
        ),
        sort_order=3,
        baseline_level="weak",
        baseline_note=(
            "Priority area. Has built a real risk-tiered governance framework for a "
            "client, but regulatory literacy is thin - only minimal exposure via one "
            "client's SEC-related requirements. The EU AI Act, U.S. state rules, and "
            "non-financial sector regulation are essentially unknown."
        ),
        keywords=(
            "governance", "regulation", "regulatory", "compliance", "eu ai act",
            "risk tiering", "risk-tier", "responsible ai", "ai ethics", "audit",
            "model risk", "nist", "iso 42001", "privacy", "gdpr", "policy",
            "assurance", "controls", "third-party risk",
        ),
    ),
    ModuleSpec(
        key="technical_fluency",
        name="Technical Fluency for Non-Technical Leaders",
        blurb=(
            "How LLMs actually work, fine-tuning vs. prompting vs. RAG, and data "
            "infrastructure basics."
        ),
        sort_order=4,
        baseline_level="intermediate",
        baseline_note=(
            "Steady baseline across LLM mechanics, fine-tuning/prompting/RAG, and data "
            "infrastructure basics. No particular weak sub-area identified."
        ),
        keywords=(
            "llm", "large language model", "fine-tuning", "fine tuning", "rag",
            "retrieval augmented", "retrieval-augmented", "embedding", "vector database",
            "data infrastructure", "data platform", "mlops", "machine learning",
            "prompt engineering", "inference", "model evaluation", "evals",
            "data pipeline", "data quality", "technical fluency",
        ),
    ),
    ModuleSpec(
        key="change_adoption",
        name="AI-Specific Change Management & Adoption",
        blurb=(
            "Adoption research specific to AI: resistance patterns, trust dynamics, "
            "and workforce fears - not general change management."
        ),
        sort_order=5,
        baseline_level="strong",
        baseline_note=(
            "General change management is a genuine strength from a consulting "
            "background. The gap is specifically AI-adoption research (resistance "
            "patterns, trust, workforce fears). Lowest priority for time investment."
        ),
        # Deliberately lighter than the other four (spec 2.3).
        weight_damping=0.55,
        keywords=(
            "change management", "adoption", "enablement", "training", "upskilling",
            "stakeholder", "communication", "culture", "workforce", "reskilling",
            "user adoption", "behaviour change", "behavior change", "transformation office",
        ),
    ),
)


MODULE_KEYS: tuple[str, ...] = tuple(m.key for m in MODULES)
MODULES_BY_KEY: dict[str, ModuleSpec] = {m.key: m for m in MODULES}


def get_module(key: str) -> ModuleSpec:
    return MODULES_BY_KEY[key]


def classify_requirement(text: str) -> list[str]:
    """Map a requirement phrase onto the modules it speaks to.

    Deterministic keyword matching, used as the offline path and as a sanity
    check on the research layer's classification. A phrase can legitimately hit
    more than one module ("build a governance framework for agent deployment").
    Returns an empty list when nothing matches, which is a normal outcome -
    plenty of requirements are about leadership or industry, not these five
    topics.
    """
    lowered = text.lower()
    hits: list[str] = []
    for module in MODULES:
        if any(keyword in lowered for keyword in module.keywords):
            hits.append(module.key)
    return hits
