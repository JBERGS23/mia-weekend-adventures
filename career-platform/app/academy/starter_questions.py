"""Hand-written starter question bank, drawn from the built-in primers.

Purpose: the daily quiz works on day one, with no API key and no generation
step. The research layer adds generated questions on top of these over time;
both live in the same table and rotate together.

Every question here is answerable from the primer text alone (spec 2.3 - quizzes
must not assume Jeff clicked an external link), and most are scenario-style
rather than recall.
"""

from __future__ import annotations

QUESTIONS: dict[str, list[dict]] = {
    # -----------------------------------------------------------------
    "strategy_fundamentals": [
        {
            "question": (
                "A CFO reviews your AI programme: 4,000 staff each report saving about "
                "three hours a week, verified by a time study. Twelve months on, "
                "operating costs are flat and headcount is unchanged. What is the most "
                "accurate diagnosis?"
            ),
            "options": [
                "The time savings were overstated and the study methodology was flawed",
                "No harvest mechanism was defined, so released capacity was reabsorbed",
                "The rollout reached too few users to move a company-level number",
                "The wrong use cases were prioritised and should be re-scored",
            ],
            "correct_index": 1,
            "explanation": (
                "This is the harvest problem. Released capacity only reaches the P&L if "
                "the organisation reduces headcount, redeploys people to revenue work, or "
                "absorbs growth without hiring. Without an explicit harvest decision and a "
                "named owner made before deployment, meetings and review cycles expand to "
                "reabsorb the time. The savings can be entirely real and still never appear."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Your team wants to build an internal meeting-summarisation tool rather "
                "than buy one, arguing it will be tailored to company terminology. Under "
                "the build-thin/buy-deep heuristic, what is the strongest counter?"
            ),
            "options": [
                "Internal builds always cost more than vendor licences",
                "It is a commodity horizontal category with real vendors, so it is "
                "non-differentiating and commits you to a maintenance treadmill",
                "The company lacks the engineering talent to build it",
                "Terminology tailoring is impossible without fine-tuning",
            ],
            "correct_index": 1,
            "explanation": (
                "Buy the horizontal. Meeting tools are a commodity category where a "
                "competitor buying the same product gets the same result, so building "
                "spends scarce attention on something non-differentiating while committing "
                "to keeping pace with a fast-moving category. Build the middle - "
                "orchestration, retrieval over proprietary data, evaluation - where your "
                "advantage is actually expressible."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which use case should be sequenced first, given it is ranked third on "
                "value but is the only one that forces the customer-data platform work "
                "that five later use cases depend on?"
            ),
            "options": [
                "The highest-value use case, since value ranking should drive sequence",
                "The third-ranked one, because sequencing should build capability, not "
                "just harvest value in rank order",
                "Whichever has the lowest change load",
                "None; run all six in parallel to compress the timeline",
            ],
            "correct_index": 1,
            "explanation": (
                "Strategy is about order, not ranking. Sequencing for capability means "
                "doing the item that unblocks the portfolio, even when it is not the "
                "highest-value item on its own. A pure value ranking repeatedly rediscovers "
                "the same missing foundations."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A vendor presents leaderboard results showing their model outperforms "
                "competitors on several public benchmarks. What is the appropriate "
                "response in a platform selection process?"
            ),
            "options": [
                "Weight the benchmarks heavily; they are standardised and comparable",
                "Discount them and run a blind bake-off on a hundred real prompts from "
                "real workflows, scored by the people who do the work",
                "Ask for benchmark results on a larger set of public tasks",
                "Select on price, since benchmark differences are not meaningful",
            ],
            "correct_index": 1,
            "explanation": (
                "Public benchmarks are general, frequently contaminated, and weakly "
                "correlated with performance on your specific tasks. The bake-off on real "
                "prompts, blind-scored by practitioners, is the only evidence that "
                "predicts your outcome."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An AI programme portfolio is 95% horizon 1 - enterprise assistant "
                "licences, coding assistants, document retrieval. What is the primary "
                "strategic risk?"
            ),
            "options": [
                "Costs will exceed budget because horizon 1 is the most expensive tier",
                "It is a procurement exercise, not a strategy: no workflow redesign and "
                "no bets, so nothing structural changes",
                "Adoption will be too low to justify the spend",
                "Governance requirements will not be met",
            ],
            "correct_index": 1,
            "explanation": (
                "Horizon 1 is necessary table stakes but non-differentiating. Without "
                "horizon 2 workflow redesign - where P&L movement actually lives - and a "
                "small horizon 3 allocation, the programme buys tools rather than "
                "producing a structural change in how the company operates."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "In the four-layer AI measurement stack, which layer do most programmes "
                "report while implying a different one?"
            ),
            "options": [
                "They report adoption while implying task effect",
                "They report activity while implying business outcome",
                "They report task effect while implying adoption",
                "They report business outcome while implying activity",
            ],
            "correct_index": 1,
            "explanation": (
                "The stack runs activity, adoption, task effect, business outcome. The "
                "characteristic failure is reporting layer one (licences deployed, prompts "
                "sent) while implying layer four, with the two middle layers - the ones "
                "that would actually connect them - never measured."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A business unit wants to buy a contract-review point solution. Central "
                "AI review would take eleven weeks. What is the most likely consequence "
                "of routing every point-solution decision through the central team?"
            ),
            "options": [
                "Better risk posture at an acceptable cost in speed",
                "Shadow AI, as units route around a bottleneck that treats a reversible "
                "decision like a platform decision",
                "Lower total spend through consolidated purchasing",
                "Improved vendor negotiating leverage",
            ],
            "correct_index": 1,
            "explanation": (
                "Platform decisions - few, expensive to reverse - belong centrally. Point "
                "solutions are many and cheaply reversible, and should be delegated with "
                "guardrails. Centralising them creates a bottleneck that reliably produces "
                "shadow AI within a quarter."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Why does the classic build-versus-buy framing transfer poorly to AI "
                "capability decisions?"
            ),
            "options": [
                "AI projects have higher failure rates, so buying is always safer",
                "The underlying capability is depreciating rapidly in your favour, so "
                "anything built must assume the model gets better and cheaper soon",
                "Vendors will not sign enterprise agreements for AI products",
                "Building requires data science talent that cannot be hired",
            ],
            "correct_index": 1,
            "explanation": (
                "Unlike classic IT, the foundation improves dramatically underneath you. "
                "That argues for building thin - orchestration, retrieval, evaluation, "
                "integration - and buying deep, so improvements in the underlying models "
                "accrue to you rather than obsoleting your build."
            ),
            "style": "recall",
        },
        {
            "question": (
                "Your enterprise assistant pilot is priced per seat. Deployment succeeds "
                "beyond expectation and heavy users run large document workloads daily. "
                "What should have been modelled at selection?"
            ),
            "options": [
                "The cost of the pilot, extrapolated linearly by headcount",
                "The cost of success under the actual deployment pattern, since per-seat "
                "and consumption pricing reward opposite usage shapes",
                "Only the licence cost, since inference is included in enterprise plans",
                "The vendor's list price with a standard volume discount",
            ],
            "correct_index": 1,
            "explanation": (
                "Per-seat pricing rewards broad shallow use; consumption pricing rewards "
                "deep narrow use. Matching the commercial shape to the expected deployment "
                "pattern - and modelling the cost of enthusiastic success rather than the "
                "pilot - is the discipline that avoids a budget surprise in year two."
            ),
            "style": "scenario",
        },
    ],
    # -----------------------------------------------------------------
    "agentic_ai": [
        {
            "question": (
                "A team describes their invoice-processing system as an 'agent'. It "
                "extracts fields, validates them against a database, routes exceptions, "
                "and posts to the ledger, in that fixed order, with code controlling each "
                "step. What is it actually?"
            ),
            "options": [
                "An agent, because it uses tools and completes a task end to end",
                "A workflow, because the control flow is defined in code rather than "
                "decided by the model",
                "A multi-agent system, because it has four distinct stages",
                "Neither; it is a traditional RPA pipeline",
            ],
            "correct_index": 1,
            "explanation": (
                "The distinction is who controls the flow. Here the steps, order and exit "
                "conditions are written by engineers; the model supplies intelligence at "
                "fixed points. That is a workflow - predictable, testable and cheap, and "
                "the right default. Most enterprise value today sits here, not in agents."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An executive asks: 'Can we stop the agent from issuing refunds over "
                "$500?' What does that question actually resolve to?"
            ),
            "options": [
                "Whether the model's system prompt forbids it",
                "Whether your code implements refunds as a callable tool, and what checks "
                "sit in front of that execution",
                "Whether the model provider supports content filtering",
                "Whether the agent has been fine-tuned on refund policy",
            ],
            "correct_index": 1,
            "explanation": (
                "The model never executes anything. It emits structured requests to call "
                "named tools; your application decides what actually runs. Every security "
                "and governance control in agentic systems is built on that fact, so the "
                "answer is always about the tool surface and its gates, not about prompting."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An agent reads customer support emails and can query internal account "
                "data and send outbound replies. Why is this configuration specifically "
                "dangerous?"
            ),
            "options": [
                "Email parsing is unreliable and produces malformed inputs",
                "It combines private data access, untrusted content, and an external "
                "communication channel - the lethal trifecta",
                "Outbound email volume can exceed provider rate limits",
                "Customer emails are usually too long for the context window",
            ],
            "correct_index": 1,
            "explanation": (
                "Untrusted content re-enters the model's context as text, so instructions "
                "hidden in an inbound email can hijack behaviour. With private data access "
                "and an outbound channel present at the same time, the exfiltration path is "
                "complete. Removing any one leg breaks it: strip or sandbox untrusted "
                "content, restrict the outbound channel, or gate sending behind human approval."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A team proposes a multi-agent architecture for a sequential, "
                "interdependent approval process. What is the strongest objection?"
            ),
            "options": [
                "Multi-agent systems cannot maintain state between steps",
                "Coordination overhead and compounding handoff errors add cost and "
                "failure modes with no offsetting benefit, since the work is not parallel",
                "The provider does not support more than two agents per account",
                "Sequential work requires fine-tuning rather than orchestration",
            ],
            "correct_index": 1,
            "explanation": (
                "Multi-agent earns its cost on parallel, context-heavy, read-mostly work "
                "where branches are genuinely independent or need separate tools and "
                "permissions. On sequential interdependent work it multiplies token cost "
                "and compounds errors across handoffs. Reaching for it early usually "
                "signals the wrong problem is being solved."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An agent pilot drafts responses ten times faster than the team it "
                "supports, but every draft requires supervisor approval. Scaling stalls. "
                "What is the binding constraint?"
            ),
            "options": [
                "Model latency during peak hours",
                "Review capacity - the deployment can only scale to the reviewers' "
                "throughput until autonomy is raised with evidence",
                "Insufficient context window for long conversation histories",
                "The absence of fine-tuning on company tone",
            ],
            "correct_index": 1,
            "explanation": (
                "This is the most common scaling wall and is routinely mistaken for a "
                "technology problem. Either the review tier is resourced, or the autonomy "
                "ladder is climbed with evidence, or the deployment does not scale. Planning "
                "the review tier before the pilot is the fix."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "In one sentence, what problem does the Model Context Protocol solve, and "
                "what does it create?"
            ),
            "options": [
                "It compresses context windows, and creates a latency cost",
                "It turns an N x M integration problem into N + M, and creates a new "
                "governance surface in the form of credentialed access paths",
                "It fine-tunes models on enterprise data, and creates a data residency issue",
                "It standardises prompt formats, and creates vendor lock-in",
            ],
            "correct_index": 1,
            "explanation": (
                "MCP standardises how applications expose tools, resources and prompts to "
                "models, so one server per system serves every MCP-capable client. That "
                "shifts build/buy economics and preserves provider optionality - and it "
                "means each server is a credentialed path into a system of record, needing "
                "a managed catalogue, least-privilege credentials and logging."
            ),
            "style": "recall",
        },
        {
            "question": (
                "An agent works well in testing but performs poorly in production, "
                "returning irrelevant results. Traces show the tools are being called "
                "correctly. What is the most likely cause?"
            ),
            "options": [
                "The model version changed without notice",
                "Tool design and results - verbose, unstructured tool output crowding the "
                "context, or descriptions too ambiguous to guide correct calls",
                "The context window is too small for production traffic",
                "Temperature is set too low for production variety",
            ],
            "correct_index": 1,
            "explanation": (
                "Agent projects fail on tool design far more often than on model "
                "capability. Tools mirroring internal REST endpoints return large nested "
                "payloads that dominate the context window, and thin descriptions leave the "
                "model guessing. Fewer, higher-level tools with compact, meaningful results "
                "and instructive errors is the fix."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which action belongs on the 'gate behind human approval' side of the "
                "reversibility rule?"
            ),
            "options": [
                "Drafting an internal summary document",
                "Issuing a customer refund",
                "Querying a read-only reporting database",
                "Generating three candidate email subject lines",
            ],
            "correct_index": 1,
            "explanation": (
                "Automate the reversible; gate the irreversible. Drafts, reads and "
                "candidate generation can be undone or ignored at no cost. A refund moves "
                "money and touches a customer, so it sits behind approval regardless of how "
                "reliable the agent has been."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Why is 'cost per completed task' the correct unit for agent economics "
                "rather than cost per API call?"
            ),
            "options": [
                "Providers bill per task rather than per token",
                "A cheaper model that needs more turns, retries or human correction is "
                "not actually cheaper",
                "API calls are free below a monthly threshold",
                "Task cost is easier to forecast than token cost",
            ],
            "correct_index": 1,
            "explanation": (
                "Agentic runs multiply token consumption, and a weaker model often "
                "compensates with more iterations. Comparing per-call prices systematically "
                "favours choices that cost more in total once the full loop is counted."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A long-running agent starts ignoring instructions given early in its "
                "task and acting on results that are no longer current. What discipline "
                "addresses this?"
            ),
            "options": [
                "Fine-tuning the model on the instruction set",
                "Context engineering - retrieval, compaction, context editing and memory "
                "to control what occupies the model's attention",
                "Increasing temperature to encourage exploration",
                "Switching to a multi-agent architecture",
            ],
            "correct_index": 1,
            "explanation": (
                "Long-horizon agents fail from context mismanagement far more often than "
                "from insufficient intelligence. Compaction summarises earlier turns, "
                "context editing clears stale tool results, memory persists durable facts "
                "outside the window, and sub-agents isolate token-heavy exploration."
            ),
            "style": "scenario",
        },
    ],
    # -----------------------------------------------------------------
    "governance": [
        {
            "question": (
                "Your company licenses a vendor's AI screening tool, rebrands it under "
                "your own name for internal use, and substantially modifies its scoring "
                "logic. Under the EU AI Act, what has most likely happened?"
            ),
            "options": [
                "Nothing changes; you remain a deployer with deployer obligations",
                "You have become a provider, taking on the far heavier provider obligations",
                "You become an importer, with supply-chain documentation duties",
                "The system moves down a risk tier because it is used internally",
            ],
            "correct_index": 1,
            "explanation": (
                "Putting your own name or trademark on a system, substantially modifying "
                "it, or repurposing a general system into a high-risk use flips a deployer "
                "into a provider. Enterprises that heavily customise vendor models cross "
                "this line without noticing, and it is one of the most consequential "
                "distinctions in the Act."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which of these is prohibited outright under the EU AI Act rather than "
                "classified as high risk?"
            ),
            "options": [
                "An AI system used to screen job applications",
                "Untargeted scraping of facial images to build a recognition database",
                "An AI system assessing creditworthiness of consumers",
                "An AI system used in medical device software",
            ],
            "correct_index": 1,
            "explanation": (
                "Untargeted scraping of facial images for recognition databases falls in "
                "the unacceptable-risk tier, alongside social scoring by public authorities, "
                "manipulative techniques causing significant harm, workplace and educational "
                "emotion inference, and biometric categorisation inferring protected "
                "attributes. Employment screening, creditworthiness and medical devices are "
                "high risk - heavily regulated, but permitted."
            ),
            "style": "recall",
        },
        {
            "question": (
                "You are asked in an interview when EU AI Act high-risk obligations take "
                "effect. What is the strongest answer?"
            ),
            "options": [
                "Give the specific date confidently from memory",
                "Describe the phasing - prohibitions and AI literacy first, then GPAI, "
                "then high risk - note that high-risk dates have been subject to amendment, "
                "and say you track it",
                "Say the Act has not yet entered into force",
                "Say obligations apply immediately on entry into force",
            ],
            "correct_index": 1,
            "explanation": (
                "The phasing structure is stable knowledge; the specific high-risk dates "
                "have moved through active simplification and delay proposals. Demonstrating "
                "command of the structure while flagging that the dates are live is stronger "
                "than a confidently wrong date, and it is what an experienced practitioner "
                "actually sounds like."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A national employer runs one hiring model across several US states with "
                "different notice, audit and impact-assessment duties. What is the mature "
                "operating response?"
            ),
            "options": [
                "Maintain separate state-specific model variants to match each rule",
                "Govern to the strictest applicable standard and treat the patchwork as a "
                "design constraint",
                "Wait for federal preemption to resolve the conflict",
                "Apply only the rules of the state of incorporation",
            ],
            "correct_index": 1,
            "explanation": (
                "Maintaining per-state variants multiplies validation, monitoring and "
                "documentation burden and creates its own consistency risk. Governing to "
                "the strictest applicable standard is cheaper in practice and is what "
                "multinationals already do with the EU regime - the Brussels effect applied "
                "domestically."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Name the four functions of the NIST AI Risk Management Framework."
            ),
            "options": [
                "Plan, Build, Deploy, Monitor",
                "Govern, Map, Measure, Manage",
                "Identify, Protect, Detect, Respond",
                "Assess, Authorise, Audit, Assure",
            ],
            "correct_index": 1,
            "explanation": (
                "Govern is the cross-cutting continuous function; Map establishes context "
                "and what could go wrong; Measure assesses and monitors; Manage allocates "
                "resources, decides on deployment, and responds to incidents. Identify/"
                "Protect/Detect/Respond is the NIST Cybersecurity Framework, a common "
                "confusion worth avoiding out loud."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A board asks why the company should pursue ISO/IEC 42001 certification "
                "when NIST AI RMF adoption is already underway. What is the strongest "
                "business answer?"
            ),
            "options": [
                "42001 is legally mandatory in the EU while NIST is voluntary",
                "42001 is certifiable, so it functions as a procurement asset increasingly "
                "requested in enterprise and public-sector RFPs",
                "42001 replaces the need for internal risk tiering",
                "NIST AI RMF does not cover generative AI",
            ],
            "correct_index": 1,
            "explanation": (
                "The two are complementary: NIST AI RMF is voluntary internal scaffolding, "
                "and its Generative AI Profile does cover generative risks. 42001's "
                "distinguishing feature is that it specifies a certifiable AI management "
                "system, which makes the case commercial rather than compliance-driven."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "You inherit an AI governance programme with a monthly review committee, "
                "a policy document, and a risk taxonomy. Teams are routing around it. "
                "What is most likely missing?"
            ),
            "options": [
                "Board-level sponsorship for the committee",
                "An inventory and a control catalogue by tier - reusable standards teams "
                "can apply without asking permission",
                "A larger committee with broader functional representation",
                "External legal counsel review of the policy",
            ],
            "correct_index": 1,
            "explanation": (
                "Governance as a committee rather than a catalogue is the classic failure. "
                "If the output is meeting minutes instead of reusable standards - and if "
                "nobody can enumerate the systems in use - teams route around it. The "
                "catalogue is the product; the committee is only the delivery mechanism."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which is the largest ungoverned AI surface in most enterprises?"
            ),
            "options": [
                "Custom models built by internal data science teams",
                "AI features arriving by upgrade inside existing SaaS products",
                "Open-source models downloaded by engineers",
                "Consumer chatbots used on personal devices",
            ],
            "correct_index": 1,
            "explanation": (
                "Vendor-delivered AI is the most commonly missed category, because it "
                "arrives through a product the company already approved, with no new "
                "procurement event to trigger review. This is a large part of why every "
                "organisation underestimates its AI inventory."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A health insurer wants to use a model to support coverage denials in "
                "utilisation review. Beyond general AI governance, what specific "
                "constraint applies?"
            ),
            "options": [
                "Only HIPAA data-handling rules apply",
                "State laws increasingly require that a licensed clinician, not an "
                "algorithm, issues the denial",
                "The model must be FDA-cleared as a medical device",
                "No sector-specific constraint applies to payers",
            ],
            "correct_index": 1,
            "explanation": (
                "Utilisation review is a live and specific area of state legislation "
                "restricting algorithmic denials. This is a good example of the broader "
                "point: sector regulators applying existing and new authority are doing more "
                "enforcement today than any horizontal AI statute."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "What is the Predetermined Change Control Plan, and why does it matter?"
            ),
            "options": [
                "An EU AI Act requirement for documenting model version history",
                "An FDA mechanism authorising anticipated post-clearance model updates "
                "without a new submission for each change",
                "A NIST control for managing model drift thresholds",
                "An ISO 42001 requirement for change management records",
            ],
            "correct_index": 1,
            "explanation": (
                "The PCCP is the regulatory answer to the problem of models that keep "
                "changing after approval. Knowing it by name is a fast credibility marker "
                "in any healthcare AI conversation, because it is the mechanism that makes "
                "continuously improving clinical models legally practical."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A lender deploys a complex model for credit decisions. Which legal "
                "requirement most directly constrains the choice of model?"
            ),
            "options": [
                "The EU AI Act's GPAI documentation obligations",
                "Adverse action notice requirements, which demand specific reasons for a "
                "negative decision",
                "State biometric privacy statutes",
                "FTC Section 5 deception authority",
            ],
            "correct_index": 1,
            "explanation": (
                "Adverse action notices require the lender to give specific principal "
                "reasons for a denial. That obligation constrains model architecture "
                "directly, because a model whose reasons cannot be articulated cannot "
                "satisfy it regardless of accuracy - a rare case where law shapes technical "
                "design rather than just process."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "The same foundation model is used in an internal drafting assistant and "
                "in a hiring screen. How should risk tiering treat them?"
            ),
            "options": [
                "Identically, since the underlying model and its risks are the same",
                "Separately - tier the use, not the model; one is minimal risk and the "
                "other is high risk",
                "Both at the higher tier, to be conservative",
                "Both at the lower tier, since the model has already been assessed",
            ],
            "correct_index": 1,
            "explanation": (
                "Confusing model risk with use risk is a common failure. Obligations attach "
                "to the context and consequences of deployment, not the technology. "
                "Tiering everything to the highest applicable level is equally damaging: it "
                "makes low-risk deployments expensive and is the fastest way for a "
                "governance function to lose credibility."
            ),
            "style": "scenario",
        },
    ],
    # -----------------------------------------------------------------
    "technical_fluency": [
        {
            "question": (
                "A team proposes fine-tuning a model on the product catalogue so it "
                "'knows' the products. What is the correct response?"
            ),
            "options": [
                "Approve it; fine-tuning is the standard way to add domain knowledge",
                "Redirect to retrieval - use retrieval to add knowledge, fine-tuning to "
                "change behaviour",
                "Approve only if the catalogue exceeds the context window",
                "Require continued pretraining instead for better results",
            ],
            "correct_index": 1,
            "explanation": (
                "This is the classic expensive mistake. Fine-tuning on facts is slow, stale "
                "the day the catalogue changes, and produces confident errors on gaps. "
                "Retrieval does it better and far cheaper. Fine-tuning earns its keep for "
                "output format adherence, unusual procedures, or distilling a large model "
                "into a small cheap one for a narrow task."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A RAG system gives disappointing answers. Where should you look first?"
            ),
            "options": [
                "The generation model - try a more capable one",
                "Retrieval - if the right passage was never retrieved, no model can save "
                "the answer",
                "The system prompt wording",
                "Temperature settings",
            ],
            "correct_index": 1,
            "explanation": (
                "The diagnosis is nearly always retrieval. Ask to see retrieval measured "
                "separately from end-to-end answer quality; a team that cannot do that is "
                "guessing. Common specific causes: fixed-size chunking that destroys "
                "structure, pure semantic search missing exact terms, and no reranking stage."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Users report the search assistant cannot find documents by part number "
                "or error code, though it handles conceptual questions well. What is the "
                "likely cause and fix?"
            ),
            "options": [
                "Context window too small; upgrade to a long-context model",
                "Pure semantic search is weak on exact strings; add hybrid search "
                "combining keyword and vector retrieval",
                "The embedding model needs fine-tuning on the catalogue",
                "Temperature is too high, causing inconsistent lookups",
            ],
            "correct_index": 1,
            "explanation": (
                "Embeddings capture meaning, not exact strings, so part numbers, error "
                "codes and proper names retrieve poorly. Hybrid search is the standard fix "
                "and its absence is one of the most common causes of a disappointing "
                "internal search deployment."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "What is the single highest-leverage artefact an enterprise AI programme "
                "owns, and whose deliverable is it?"
            ),
            "options": [
                "The model selection matrix, owned by architecture",
                "A golden set of real inputs with agreed correct outputs, owned by the "
                "business people who do the work",
                "The prompt library, owned by the central AI team",
                "The vendor scorecard, owned by procurement",
            ],
            "correct_index": 1,
            "explanation": (
                "Without a golden set you cannot compare vendors, detect regressions after "
                "a model or prompt change, or make a defensible quality claim. It is a "
                "business deliverable because only practitioners can say what a correct "
                "output is, and treating it as an engineering artefact is why it so often "
                "does not exist."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A vendor claims their system 'doesn't hallucinate'. What is the accurate "
                "technical response?"
            ),
            "options": [
                "Plausible if they use retrieval grounding, which eliminates hallucination",
                "Nothing eliminates it - fluency and accuracy come from the same "
                "next-token mechanism; grounding and citation reduce and expose it",
                "True only for fine-tuned models on narrow domains",
                "True if temperature is set to zero",
            ],
            "correct_index": 1,
            "explanation": (
                "The model produces plausible continuations, not lookups, and there is no "
                "internal signal separating a grounded answer from a fabricated one. "
                "Retrieval, citation and verification reduce the rate and make errors "
                "detectable; they do not remove the failure mode."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "A pilot costs very little to run. Finance asks what full deployment "
                "costs. What is structurally different about AI cost compared with "
                "licensed software?"
            ),
            "options": [
                "Nothing; both scale linearly with headcount",
                "Cost scales with usage in tokens rather than seats, so successful "
                "adoption raises cost - model the cost of success",
                "AI costs fall as usage grows due to volume discounting",
                "Costs are fixed once the model is deployed",
            ],
            "correct_index": 1,
            "explanation": (
                "Token-denominated inference cost breaks the budgeting instincts of anyone "
                "used to per-seat licensing: the better adoption goes, the more it costs. "
                "Prompt caching, batch processing for non-latency-sensitive work, and "
                "routing easy traffic to cheaper models are the main levers."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An internal assistant indexes documents from a shared drive. What "
                "governance problem does this most likely create?"
            ),
            "options": [
                "Excessive storage cost for the vector index",
                "A permissions leak - an index built without per-document access control "
                "will quote documents the asker was never allowed to see",
                "Slower retrieval as the corpus grows",
                "Model degradation from low-quality training data",
            ],
            "correct_index": 1,
            "explanation": (
                "Retrieval inherits every content-governance problem the organisation "
                "already had, permissions included. Whatever governs who can see a document "
                "must be enforceable at retrieval time, or you have built a very efficient "
                "leak. It also faithfully surfaces the outdated policy nobody deleted."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "What does 'test-time compute' refer to, and why does it change the "
                "vendor selection question?"
            ),
            "options": [
                "Time spent on QA before release; it shortens procurement cycles",
                "Spending more computation at inference on harder problems, so 'which "
                "model' becomes 'which model at what effort'",
                "Benchmark runtime, used to compare model efficiency",
                "The latency budget allocated to a user-facing request",
            ],
            "correct_index": 1,
            "explanation": (
                "Models can be trained to reason at length before answering and to spend "
                "more inference computation on harder problems. This is a scaling axis "
                "distinct from model size: the same model can be dialled between fast-and-"
                "cheap and slow-and-more-accurate, which makes effort level part of both the "
                "quality and the cost decision."
            ),
            "style": "recall",
        },
        {
            "question": (
                "'Our data isn't ready' is offered as the reason to delay all AI work by "
                "eighteen months. What is the pragmatic counter?"
            ),
            "options": [
                "Accept it; data quality is a hard prerequisite for any AI deployment",
                "Pick the first two workflows, fix the data those specifically need, and "
                "let real use cases pull platform work in a prioritised order",
                "Buy a data catalogue product to accelerate the programme",
                "Start with generative use cases, which do not require data",
            ],
            "correct_index": 1,
            "explanation": (
                "The claim is usually true but is used to justify more delay than it "
                "should. What must be true is narrower than a platform rebuild: "
                "accessibility, permissions that travel to retrieval time, quality "
                "sufficient for the specific use, and lineage. A data programme with no "
                "consuming use case produces a catalogue nobody opens."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Prompt caching was enabled but usage reports show no cache hits. What is "
                "the most likely cause?"
            ),
            "options": [
                "The model does not support caching",
                "Something volatile sits in the cached prefix - a timestamp or per-request "
                "ID - so the byte-identical prefix match never occurs",
                "The prompt is too long to cache",
                "Caching only applies to output tokens",
            ],
            "correct_index": 1,
            "explanation": (
                "Caching is a prefix match: any byte change anywhere in the prefix "
                "invalidates everything after it. A current timestamp in a system prompt, "
                "an unsorted JSON serialisation, or a varying tool list silently defeats it. "
                "Stable content first, volatile content last."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which pairing correctly matches the adaptation approach to the problem?"
            ),
            "options": [
                "Fine-tuning for live inventory levels; retrieval for tone of voice",
                "Retrieval for company knowledge; tool use for live system state; "
                "fine-tuning for consistent output format",
                "Prompting for live data; fine-tuning for policy documents",
                "Continued pretraining for output format; few-shot for live data",
            ],
            "correct_index": 1,
            "explanation": (
                "Retrieval adds knowledge, tool use adds capability and access to live "
                "state, and fine-tuning changes behaviour such as format adherence or an "
                "unusual procedure. Live inventory is a tool-use problem - it must be "
                "queried, never memorised."
            ),
            "style": "scenario",
        },
    ],
    # -----------------------------------------------------------------
    "change_adoption": [
        {
            "question": (
                "Your most experienced underwriters resist the new AI assistant while "
                "junior staff adopt it enthusiastically. What does the research suggest?"
            ),
            "options": [
                "The seniors have a mindset problem requiring targeted change messaging",
                "Their resistance is largely rational - field evidence shows gains "
                "concentrate among less experienced workers, so their cost-benefit is genuinely worse",
                "The tool was configured for junior workflows only",
                "Seniors need more training hours than juniors",
            ],
            "correct_index": 1,
            "explanation": (
                "Multiple field studies find performance compression: the tools raise the "
                "floor much more than the ceiling. Experts also discount algorithmic advice "
                "in their own domain more than novices do. Treating rational cost-benefit "
                "as a mindset deficit is both wrong and insulting, and it reliably deepens "
                "the resistance."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "An early pilot produces one visible, embarrassing AI error in front of a "
                "large internal audience. Why is this disproportionately costly?"
            ),
            "options": [
                "It triggers mandatory incident reporting under most AI policies",
                "Algorithm aversion: people abandon algorithms after seeing them err far "
                "more readily than they abandon humans who err comparably",
                "It invalidates the pilot's measurement baseline",
                "It requires the model to be retrained on corrected examples",
            ],
            "correct_index": 1,
            "explanation": (
                "Dietvorst and colleagues showed people apply an asymmetric error standard: "
                "human mistakes read as normal variance, machine mistakes as evidence of "
                "fundamental brokenness - even after watching the algorithm outperform the "
                "human. So sequence pilots where errors are cheap and correctable, not "
                "where value is highest."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which interface change is best supported by evidence as a way to overcome "
                "algorithm aversion?"
            ),
            "options": [
                "Displaying the model's confidence score alongside each output",
                "Letting users modify the output, even slightly, before it is used",
                "Showing which training data informed the answer",
                "Adding a detailed explanation of how the model works",
            ],
            "correct_index": 1,
            "explanation": (
                "Dietvorst's follow-up found that granting even slight modification "
                "control substantially restored willingness to use an imperfect algorithm. "
                "Perceived control, not accuracy or explanation, was the lever - which "
                "argues directly for draft-and-edit interfaces over accept-or-reject ones."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "What is the 'jagged technological frontier', and what does it imply for "
                "enablement content?"
            ),
            "options": [
                "The uneven pace of model releases; enablement should be refreshed quarterly",
                "The irregular, invisible boundary of model capability; the highest-value "
                "training is task-boundary literacy, not prompt technique",
                "Variation in adoption rates between departments; enablement should be "
                "targeted at laggards",
                "The gap between pilot and production performance; enablement should focus "
                "on operational readiness",
            ],
            "correct_index": 1,
            "explanation": (
                "In the BCG field experiment, consultants using AI inside the capability "
                "boundary produced significantly better work faster, while on a task outside "
                "it they were substantially more likely to reach the wrong answer than "
                "colleagues without AI. Since the boundary is invisible from outside, "
                "teaching where it sits for someone's own work beats prompt libraries."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Survey data shows 30% AI adoption, but licence telemetry and anecdote "
                "suggest far higher real use. What is the most likely explanation?"
            ),
            "options": [
                "Survey sampling error from low response rates",
                "People hide use - disclosure carries an evaluative penalty and "
                "displacement risk, so reported adoption understates real adoption",
                "Users misunderstand what counts as AI",
                "Telemetry double-counts sessions",
            ],
            "correct_index": 1,
            "explanation": (
                "Workers who disclose AI assistance are often judged as less competent or "
                "diligent, and visibly demonstrating your job can be done faster is not "
                "obviously in your interest when headcount decisions are pending. The gap is "
                "largest where anxiety is highest, and the hidden use typically runs through "
                "unsanctioned tools - a security problem as much as a cultural one."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Adoption is strong at the executive level and among front-line staff but "
                "stalls in between. What is the most effective intervention?"
            ),
            "options": [
                "Escalate through the sponsorship coalition to enforce compliance",
                "Adjust middle managers' throughput metrics for a defined learning period "
                "and give them use cases for their own work first",
                "Increase the frequency of all-hands communications",
                "Replace resistant managers with early adopters",
            ],
            "correct_index": 1,
            "explanation": (
                "Middle managers are measured on short-term throughput that adoption "
                "temporarily costs, are accountable for an unfamiliar error profile, and "
                "often have not crossed the frontier-literacy threshold themselves. Their "
                "metrics, not their mindset, are the thing to change - and they need to "
                "experience the tool on their own work before they can coach it."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Which adoption metric is the most reliable early signal of a deployment "
                "that will stick?"
            ),
            "options": [
                "Licences deployed in the first month",
                "Retention past week four",
                "Total prompts sent in week one",
                "Self-reported satisfaction scores",
            ],
            "correct_index": 1,
            "explanation": (
                "Curiosity produces a large week-one spike in essentially every deployment, "
                "and almost all of it is noise. Sustained use a month in separates real "
                "workflow integration from novelty, and it is much harder to game than "
                "licence or prompt counts."
            ),
            "style": "recall",
        },
        {
            "question": (
                "A support team using an AI assistant stops catching errors it would "
                "previously have flagged, and quality drops on the rare hard cases. What "
                "is happening?"
            ),
            "options": [
                "Algorithm aversion, causing disengagement from the tool",
                "Automation bias - over-acceptance and decayed verification, worst where "
                "the system is usually right and failures are rare",
                "Model drift from changing customer language",
                "Insufficient prompt training among the team",
            ],
            "correct_index": 1,
            "explanation": (
                "This is the mirror-image failure to aversion and gets far less attention "
                "in enterprise programmes. Vigilance decays with the rarity of failure, so "
                "a mostly-correct system produces the worst over-reliance. The target is "
                "calibrated trust, not maximum adoption."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Employees ask directly whether AI will cost jobs, and the strategy does "
                "contemplate a headcount harvest. What is the defensible response?"
            ),
            "options": [
                "'This augments, it doesn't replace' - reassurance maintains morale",
                "Be specific about what is decided and what is not, commit to the "
                "transition rather than the outcome, and name the harvest mechanism openly",
                "Decline to comment until decisions are finalised",
                "Redirect to the productivity benefits for individual workers",
            ],
            "correct_index": 1,
            "explanation": (
                "Employees detect the gap between reassurance and the operating plan, and "
                "once it is visible every later communication is discounted. Retraining, "
                "redeployment priority, notice and internal mobility are commitments a "
                "company can actually keep; 'nobody will lose their job' usually is not, and "
                "cannot be retracted gracefully."
            ),
            "style": "scenario",
        },
        {
            "question": (
                "Under what conditions does research find algorithm *appreciation* rather "
                "than aversion?"
            ),
            "options": [
                "When users are domain experts evaluating advice in their own field",
                "For tasks perceived as objective and quantitative, especially among "
                "non-experts",
                "After users have observed the algorithm making a visible error",
                "When the case is perceived as personally unique",
            ],
            "correct_index": 1,
            "explanation": (
                "Logg and colleagues found people often weight algorithmic advice above "
                "human advice for objective, quantitative tasks, particularly when they are "
                "not experts themselves. The moderators reconciling the two literatures are "
                "task subjectivity, user expertise, observed error, and perceived uniqueness "
                "of the case."
            ),
            "style": "recall",
        },
    ],
}
