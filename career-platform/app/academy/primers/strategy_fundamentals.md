# AI Strategy Fundamentals

## What an AI strategy actually is

Most documents titled "AI Strategy" are not strategies. They are inventories: a
list of forty use cases, scored on a value/feasibility grid, with a heat map and
a governance slide bolted on. That artefact is genuinely useful as an input, but
it does not answer the question a board is actually asking, which is: *where is
this company going to be structurally different in three years because of AI,
and what are we deliberately not doing?*

A real AI strategy makes four commitments:

1. **A theory of advantage.** What does AI let *this* company do that a
   competitor with the same off-the-shelf models cannot easily copy? The models
   are a commodity available to everyone. The advantage sits in proprietary
   data, distribution, workflow ownership, regulatory position, or the speed at
   which the organisation can absorb change.
2. **A portfolio shape.** How capital and attention split across near-term
   productivity, medium-term workflow redesign, and a small number of bets that
   only pay off if the technology keeps improving.
3. **A capability build order.** Data, platform, governance, talent, and change
   capacity in the sequence that unblocks the portfolio, not in the abstract.
4. **A set of refusals.** What the company will not build, not buy, and not
   attempt this year. A strategy without refusals is a wish list.

The single most common failure mode in 2025-2026 is the **pilot portfolio with
no harvest**: dozens of proofs of concept, real enthusiasm, measurable task-level
time savings, and no change to headcount, cost-to-serve, cycle time, or revenue.
This is the problem an incoming Head of AI Strategy is usually hired to fix, so
it is worth being able to diagnose it precisely.

## Where the value actually comes from

Value shows up in four places, and they behave very differently.

**Cost-to-serve reduction.** Deflecting contacts, automating document handling,
compressing review cycles. Easiest to measure, easiest to sell internally,
and the place where value most often evaporates between the task and the P&L
(see "The harvest problem" below).

**Revenue and growth.** Better targeting, faster proposal and quote generation,
personalisation, new AI-enabled products or pricing. Harder to attribute,
slower, but the only category that produces a defensible story for investors.

**Risk and quality.** Fewer errors in coding and claims, better surveillance,
faster compliance review. Value is real but shows up as avoided loss, which
means you need a credible base rate to claim it at all.

**Speed and optionality.** Cycle-time reduction in research, engineering, and
decision-making. Chronically under-counted because no line item moves, yet it is
often the largest genuine effect. If a drug programme or a product launch moves
up two months, that is worth more than every chatbot in the company.

A useful discipline: for every use case, name which of the four it is, and name
the single metric that would move. If nobody can name the metric, the use case
is a demo.

## Use-case prioritisation beyond the 2x2

The value/feasibility 2x2 is table stakes and mostly useless on its own, because
"feasibility" hides five different constraints that fail in different ways. A
prioritisation model that survives contact with an operating committee scores
each candidate on:

- **Value size and confidence.** Annualised, with an explicit confidence band.
  Force a range, not a point estimate.
- **Data readiness.** Does the data exist, is it accessible, is it accurate
  enough, and is it permitted for this use? This is where most timelines break.
- **Workflow ownership.** Is there a named executive who owns the process being
  changed and wants it changed? Use cases without an owner do not ship.
- **Regulatory and reputational exposure.** Which risk tier does this land in
  (see the Governance module), and does that add months of assurance work?
- **Change load.** How many people have to work differently, and how much of
  their identity is bound up in the task being automated?
- **Reversibility.** If it goes wrong, can it be switched off without customer
  harm? Cheap-to-reverse decisions deserve less analysis and faster approval.

Two structural points matter more than the scoring mechanics:

**Sequence for capability, not just for value.** The second-highest-value use
case may be worth doing first because it forces the data platform work that
five later use cases depend on. Strategy is about the order, not the ranking.

**Cluster by workflow, not by use case.** Ten separate "AI assistants" bolted
onto ten steps of one process produce far less value than redesigning the
process once. The organisations getting real returns are consolidating around
end-to-end workflows: claims handling, order-to-cash, underwriting, tier-1
support, contract lifecycle. This is also what makes the difference between a
productivity story and a structural one.

### Portfolio shape

A defensible allocation for a large traditional enterprise looks something like:

- **~60% horizon 1 - deployed capability.** Enterprise assistant rollout,
  coding assistants, document and knowledge retrieval, meeting and reporting
  automation. Low differentiation, real cost, necessary table stakes.
- **~30% horizon 2 - workflow redesign.** Two to four end-to-end processes
  rebuilt around AI rather than augmented at the edges. This is where the
  actual P&L movement lives, and where most companies under-invest.
- **~10% horizon 3 - bets.** Small, time-boxed, explicitly allowed to fail,
  aimed at capabilities that only make sense if models keep improving.

The proportions matter less than the fact that all three exist and are funded
separately. A portfolio that is 95% horizon 1 is a procurement exercise. One
that is 50% horizon 3 is a research lab with a business attached.

## Build, buy, or partner

The classic IT framing does not transfer cleanly, for one reason: **the
underlying capability is depreciating rapidly in your favour.** Anything you
build today on top of a model must assume the model gets materially better and
cheaper within twelve months. That assumption should push you toward building
*thin* and buying *deep*.

A workable heuristic:

- **Buy the frontier.** Do not build foundation models. Do not fine-tune when
  prompting plus retrieval will do. The frontier labs are spending more on a
  single training run than your entire AI budget.
- **Buy the horizontal.** Enterprise assistants, coding assistants, meeting
  tools, and general document processing are commodity categories with real
  vendors. Building these internally is almost always a mistake.
- **Build the middle.** Orchestration, evaluation harnesses, retrieval over
  proprietary data, prompt and policy libraries, and the integration layer into
  your systems of record. This is where your specific advantage is expressible
  and where no vendor knows your business.
- **Partner at the edge.** Where the domain is narrow and regulated and a
  specialist has already absorbed the compliance cost (clinical coding, legal
  review, actuarial), partnering beats both.

The questions that actually decide it:

1. **Is this differentiating?** If a competitor buying the same product gets the
   same result, buy it and spend the attention elsewhere.
2. **Do we have a data advantage here?** Proprietary data that is genuinely hard
   to replicate is the strongest argument for building.
3. **How fast is the category moving?** In fast-moving categories, building
   means committing to a maintenance treadmill. Buying is a way of renting
   somebody else's R&D.
4. **What is the switching cost?** Deep integration into one vendor's
   proprietary orchestration layer is a strategic decision, not a technical one.
   Preserve the ability to change model providers; that optionality has real
   value while price-performance is moving this fast.
5. **What is the true TCO?** For build, that means engineering, evaluation,
   monitoring, security review, and the ongoing cost of keeping up. Build costs
   are chronically underestimated by a factor of two to three because the
   ongoing evaluation and maintenance burden is invisible at approval time.

## Vendor and platform selection

Distinguish two decisions that get conflated:

**Platform decisions** (which model providers, which enterprise assistant, which
cloud, which orchestration layer) are few, expensive to reverse, and should be
made centrally with a multi-year view.

**Point-solution decisions** (a contract-review tool, a support co-pilot) are
many, cheaper to reverse, and should be delegated with guardrails. Centralising
these creates a bottleneck that pushes business units into shadow AI.

For the enterprise assistant decision specifically - the Claude Enterprise vs.
Microsoft Copilot vs. ChatGPT Enterprise class of choice - the criteria that
actually differentiate:

- **Where the work already happens.** Deep native integration into the existing
  productivity suite is worth a great deal of raw model quality, because
  adoption is the binding constraint, not capability.
- **Data handling and residency.** Training-on-your-data terms, retention
  periods, regional hosting, and whether admin controls are real or aspirational.
- **Model quality on your actual tasks.** Run a bake-off on a hundred real
  prompts from real workflows, blind-scored by the people who do the work. Do
  not rely on public benchmarks; they are weakly correlated with your use.
- **Admin, audit, and DLP surface.** What can a security team actually see and
  control?
- **IP indemnity and contractual risk allocation.**
- **Commercial shape.** Per-seat pricing rewards broad shallow use; consumption
  pricing rewards deep narrow use. Match the shape to the deployment pattern, and
  model the cost of success, not the cost of the pilot.
- **Model deprecation policy.** How much notice before a model you have built
  on is retired, and what is the migration path?

A pattern worth knowing: many large enterprises end up **multi-vendor on
purpose** - one assistant bundled with the productivity suite for breadth, plus
a second provider's models available through an internal API layer for
build teams who need a different quality or cost profile. This is defensible if
the internal orchestration layer is genuinely provider-agnostic, and expensive
theatre if it is not.

## ROI, and the harvest problem

AI ROI claims fall apart under scrutiny for predictable reasons, and being the
person in the room who can say why is disproportionately valuable.

**The measurement stack.** Four layers, each necessary and none sufficient:

1. **Activity** - licences deployed, prompts sent. Vanity, but a leading
   indicator of nothing happening.
2. **Adoption** - weekly active use as a share of eligible users, depth of use,
   retention past week four. The honest early metric.
3. **Task effect** - measured time or quality change on a specific task,
   ideally against a baseline captured *before* deployment and a control group
   that did not get the tool.
4. **Business outcome** - cost-to-serve, cycle time, conversion, error rate,
   revenue. The only layer that survives a CFO.

Most programmes report layer 1, imply layer 4, and never measure layers 2 and 3.

**The harvest problem.** This is the crux. Suppose you demonstrate that 4,000
knowledge workers each save three hours a week. That is roughly 300 full-time
equivalents of released capacity. It shows up in the P&L only if the
organisation does one of three things with it: reduce headcount, redeploy people
to work that generates revenue, or absorb growth without hiring. Absent an
explicit harvest decision, released capacity is simply reabsorbed - meetings
expand, review cycles lengthen, the saved time disappears. The strategy work is
deciding the harvest mechanism *before* deployment, and naming who owns it. A
Head of AI Strategy who raises this in an interview is immediately credible,
because almost every large deployment has this problem and almost nobody says it
out loud.

**Attribution discipline.** Insist on a pre-deployment baseline, a
counterfactual (a comparable team without the tool, or a staged rollout by
region), and a named finance partner who signs off on the methodology before
the numbers are needed. Retrofitted ROI is never believed.

**Cost modelling.** Inference cost scales with usage, unlike licensed software.
Model the cost of enthusiastic success, not of the pilot. Include evaluation,
monitoring, and human review in the run cost - review capacity is frequently the
real constraint on scaling an AI workflow, not the model.

## Operating model in one paragraph

Three archetypes. A **centralised CoE** owns platform, standards and delivery;
fast to start, becomes a bottleneck. A **fully federated** model puts capability
in the business units; fast locally, produces duplicated spend, inconsistent
risk posture and no leverage. **Hub-and-spoke** - a small central team owning
platform, governance, evaluation standards, vendor relationships and scarce
talent, with embedded practitioners in the units owning use cases and P&L
outcomes - is where most large organisations converge, and is the right default
answer. The central team should be small and opinionated, and its scarcest
output is *standards other people can use without asking permission*.

## What "good" looks like on one page

A credible AI strategy fits on a page and answers: the theory of advantage; the
three-to-five workflows being rebuilt and who owns each; the platform decisions
made and the ones deliberately deferred; the capability build order for data,
governance and talent; the harvest mechanism; the funding split across horizons;
and the explicit refusals. Everything else is appendix.

## Interview-grade positions worth holding

- Pilots are not the problem; the absence of a harvest mechanism is.
- Consolidate around workflows, not use cases.
- Build thin, buy deep, and preserve provider optionality.
- Adoption, not model capability, is the binding constraint in almost every
  enterprise deployment today.
- The central team's product is standards, not projects.

## Glossary

- **Horizon 1 / 2 / 3** — A portfolio framing: deployed capability, workflow redesign, and speculative bets, funded and governed separately.
- **Harvest mechanism** — The explicit decision about how released capacity becomes a financial outcome: headcount reduction, redeployment, or absorbing growth without hiring.
- **Cost-to-serve** — The fully loaded cost of delivering a unit of service to a customer; the most common target metric for efficiency-driven AI programmes.
- **Counterfactual** — A comparison group or period without the intervention, used to separate the effect of the tool from everything else changing at the same time.
- **Total cost of ownership (TCO)** — Full lifetime cost including build, integration, evaluation, monitoring, security review and ongoing maintenance, not just licence or inference cost.
- **Hub-and-spoke operating model** — A small central team owning platform, standards and governance, with embedded practitioners in business units owning use cases and outcomes.
- **Centre of Excellence (CoE)** — A centralised team owning AI capability, standards and often delivery; effective early, prone to becoming a delivery bottleneck at scale.
- **Shadow AI** — Unsanctioned use of AI tools by employees outside approved channels, typically a symptom of central provisioning being too slow or too restrictive.
- **Bake-off** — A structured head-to-head evaluation of vendors on a fixed set of real tasks, blind-scored by practitioners rather than assessed on public benchmarks.
- **Model deprecation** — A provider retiring a model version, forcing migration of anything built against it; a contractual and architectural risk in vendor selection.
- **Provider optionality** — Retaining the practical ability to switch model providers, preserved through a provider-agnostic internal orchestration layer.
- **Consumption pricing** — Charging based on usage (typically tokens processed) rather than per seat; rewards deep narrow deployments and penalises unmanaged broad ones.
- **Value/feasibility matrix** — The standard two-axis prioritisation grid; useful as an input, insufficient as a strategy because "feasibility" conflates several distinct constraints.
