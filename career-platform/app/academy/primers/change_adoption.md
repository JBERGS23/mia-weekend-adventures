# AI-Specific Change Management & Adoption

> **What this primer deliberately skips.** Stakeholder mapping, sponsorship
> coalitions, communication cadences, ADKAR, Kotter, resistance management as a
> general discipline - all assumed. This module covers only what is *different*
> about AI adoption, because that is where the gap is. If a section feels like
> generic change management, it has failed its brief.

## Why AI adoption does not behave like other technology change

Four differences drive almost everything else:

1. **The tool is non-deterministic.** Users cannot build a reliable mental model
   of "what it does" the way they can with a CRM. Same input, different output.
   Trust has to be formed under genuine uncertainty, which is a psychological
   problem, not a training problem.
2. **It targets judgement, not process steps.** Previous waves automated
   transactions and record-keeping. This wave touches drafting, analysis,
   diagnosis, and advice - the parts of the job people attach their professional
   identity to. Resistance is therefore often identity defence, not effort
   avoidance, and it responds to entirely different interventions.
3. **Capability is discovered, not specified.** Nobody can hand users a complete
   list of what it is good at, because the boundary is irregular and moves with
   every model release. Adoption depends on users personally discovering where
   the boundary sits for their work.
4. **The existential frame is present from the first conversation.** Every
   previous system promised to help people do their jobs. This one is publicly
   discussed as a replacement for jobs. That frame is in the room whether or not
   anyone says it out loud.

## Trust: two opposite failure modes

The literature is genuinely two-sided, and knowing both sides is what makes
someone sound like they have read it rather than skimmed a blog post.

**Algorithm aversion.** Dietvorst, Simmons and Massey (2015) showed that people
who have *seen an algorithm err* abandon it far more readily than they abandon a
human forecaster who made comparable errors - even when they have just watched
the algorithm outperform the human. The mechanism is an asymmetric error
standard: human mistakes are read as normal variance, machine mistakes as
evidence of fundamental brokenness. The operational implication is sharp and
counter-intuitive: **a single visible failure early in a rollout can cost more
adoption than a dozen quiet successes gain.** Pilot sequencing should therefore
start where errors are cheap and visible-but-correctable, not where value is
highest.

The same authors' follow-up (2018) found the most useful intervention:
**letting people modify the algorithm's output, even slightly, substantially
restores their willingness to use it.** Perceived control, not accuracy, was the
lever. This is a direct design instruction - draft-and-edit interfaces beat
accept-or-reject ones, and "the AI proposes, you dispose" is not just
reassurance framing, it measurably drives use.

**Algorithm appreciation.** Logg, Minson and Moore (2019) found the opposite in
other conditions: people often weight algorithmic advice *more* heavily than
human advice, particularly for tasks perceived as objective and quantitative,
and particularly when they are not themselves experts. The moderators that
reconcile the two literatures are worth memorising:

- **Task subjectivity.** Objective/numeric tasks get appreciation; tasks
  perceived as requiring human judgement, taste or morality get aversion.
- **User expertise.** Experts discount algorithmic advice in their own domain
  more than novices do - which means the people you most need to adopt often
  resist hardest.
- **Error visibility.** Aversion is triggered by observed failure, not
  anticipated failure.
- **Perceived uniqueness of the case.** Longoni and colleagues (2019) found
  resistance to medical AI is driven substantially by **uniqueness neglect** -
  the belief that "my case is special and a statistical system cannot account
  for me." This generalises well beyond medicine to any personalised service.

**Automation bias** is the mirror-image failure and gets far less airtime in
enterprise programmes. Users over-accept machine output, stop verifying, and
miss errors they would have caught unaided - documented across aviation,
clinical decision support and now generative tools. It compounds over time as
complacency sets in, and it produces the worst outcomes precisely where a system
is *mostly* right, because vigilance decays with rarity of failure.

**The target is calibrated trust, not maximal trust.** This reframing is worth
stating explicitly to executives who describe adoption purely as a
persuasion problem. The goal is that users accept output where the system is
reliable and scrutinise it where it is not. That means training and messaging
must teach the *shape of the failure boundary*, not simply enthusiasm - and it
means an adoption programme that only pushes usage upward is optimising the
wrong variable.

## The jagged frontier, and what it implies for training

The most useful single finding for practical rollout design comes from
Dell'Acqua and colleagues' field experiment with BCG consultants (2023).
Consultants using a frontier model on tasks *inside* the model's capability
boundary completed significantly more work, faster, at meaningfully higher
quality. On a task deliberately chosen to sit *outside* that boundary - where
the model produced plausible but wrong analysis - those with AI were
**substantially more likely to reach the wrong answer** than those without it.

The authors' term, **the jagged technological frontier**, captures the core
problem: capability is not a smooth gradient from easy to hard. Tasks of
apparently similar difficulty fall on opposite sides of the boundary, and the
boundary is not visible from outside. They also identified two successful user
patterns: **centaurs**, who divide tasks and hand the model the parts it is good
at, and **cyborgs**, who interleave with it continuously, checking as they go.

The training implication is the thing to say in an interview: **the highest-value
enablement content is not prompt technique, it is task-boundary literacy** -
teaching people where the frontier sits for *their* work and how to verify near
it. Almost every enterprise enablement programme gets this backwards and spends
its budget on prompt libraries.

## The skill gradient, and why it is politically awkward

Multiple field studies converge on a consistent pattern: **generative tools
compress the performance distribution.** In a large customer-support deployment
(Brynjolfsson, Li and Raymond), average productivity rose meaningfully while
gains concentrated overwhelmingly among the least experienced and lowest-skilled
agents, with minimal or no gain for the most experienced. Noy and Zhang found
the same compression on professional writing tasks: large average time savings,
quality gains concentrated among initially weaker writers.

Two consequences a strategist should be ready to discuss:

- **Your senior people gain least and are asked to change most.** The
  cost-benefit for a twenty-year expert is genuinely worse than for a
  six-month hire, so their resistance is often *rational* rather than
  emotional. Treating it as a mindset problem is both wrong and insulting.
- **It compresses the value of experience**, which is a live threat to the
  status hierarchy of professional organisations, and it disrupts the
  apprenticeship model - if juniors' output is AI-lifted, the traditional path
  by which they built judgement through repetitive early work is disrupted, and
  nobody has a settled answer for what replaces it. Being able to raise this
  question thoughtfully signals seniority.

## Disclosure, stigma, and shadow use

A distinctive and under-discussed dynamic: **people hide their AI use.**

Two mechanisms drive it. First, **evaluative penalty** - a growing body of work
finds that workers who disclose AI assistance are judged by peers and managers
as less competent, less diligent, or less deserving of credit for the output.
Where that perception exists, disclosure is individually costly even when use is
officially encouraged. Second, **displacement fear** - visibly demonstrating that
your job can be done faster with a tool is not obviously in your interest when
headcount decisions are pending.

The result is systematically distorted data. Reported adoption understates real
adoption, and the gap is largest exactly where anxiety is highest. Programmes
that measure adoption by survey get a picture skewed by who feels safe
answering. Meanwhile the hidden use runs outside sanctioned tooling - personal
accounts, personal devices, corporate data in consumer products - which converts
a cultural problem into a security incident.

Interventions that actually address this:

- **Make disclosure normatively safe by demonstrating it upward.** Senior
  leaders visibly and specifically describing their own use, including where it
  failed, does more than any policy document.
- **Give explicit credit rules.** State that AI-assisted work is the author's
  work and is evaluated on its quality, full stop.
- **Separate usage telemetry from performance management, and say so credibly.**
  If people believe usage data feeds appraisals, both the data and the trust are
  destroyed. This commitment has to be real, because it will be tested.
- **Provision sanctioned tools generously and quickly.** Shadow use is mostly a
  provisioning-speed problem wearing a culture costume.

## Workforce fear, handled honestly

The instinct to reassure - "this augments, it doesn't replace" - fails whenever
the strategy actually does contemplate a headcount harvest, and employees are
good at detecting the gap between the message and the operating plan. Once that
gap is visible, every subsequent communication is discounted.

The defensible posture:

- **Be specific about what is decided and what is not.** "No decisions have been
  made about roles in this function, and here is when that will be reviewed and
  who will be consulted" is credible. "Nobody will lose their job" usually is
  not, and cannot be retracted gracefully.
- **Commit to the transition, not to the outcome.** Retraining, redeployment
  priority, notice periods, and internal mobility are commitments a company can
  actually keep.
- **Name the harvest mechanism openly** (see the Strategy Fundamentals module).
  If released capacity is going to absorb growth rather than reduce headcount,
  saying so specifically is far more persuasive than a general reassurance.
- **Expect anxiety to be uneven and predictable.** It concentrates in roles whose
  core task is visibly demonstrable by the tool, and among mid-career staff with
  high firm-specific capital and limited external mobility.

## Middle management is the actual bottleneck

Senior sponsorship is necessary and usually present; front-line curiosity is
usually present too. Adoption stalls in the middle layer, for reasons specific
to this technology:

- Middle managers are measured on short-term throughput, and adoption costs
  throughput during the learning period. Nobody has adjusted their targets.
- They are accountable for errors their teams make, and the error profile of AI
  output is unfamiliar, so the risk feels asymmetric to them.
- Many have not personally crossed the frontier-literacy threshold and cannot
  coach what they have not experienced.
- A layer whose value is partly coordination and summarisation is plausibly the
  most exposed to the technology, and is being asked to lead its deployment.

Practical response: give the middle layer explicit permission to trade
short-term output for learning time, adjust their metrics for a defined period,
give them use cases for *their own* work first so they experience the frontier
directly, and make peer exemplars from their own level rather than from a
central team.

## Measuring adoption without fooling yourself

- **Weekly active use as a share of eligible users**, not licences deployed.
- **Retention past week four.** The single best early signal. Curiosity produces
  a large week-one spike in every deployment; almost all of it is noise.
- **Depth** - sessions per active user, and whether use has moved beyond
  summarise-and-rewrite into workflow-embedded tasks.
- **Breadth across teams**, to find where it is working and copy it, rather than
  reporting a company average that hides everything interesting.
- **Task-level outcome measures on a sample**, since self-reported time savings
  are systematically inflated.
- Treat all self-report as directional given the disclosure problem above.

## What works and what does not

**Works:** peer exemplars from the same role and level; use-case libraries
contributed by colleagues rather than issued centrally; protected time to
practise on real work; leaders demonstrating their own use including failures;
redesigning the workflow rather than adding a tool alongside it; starting where
errors are cheap; giving users editorial control over output; teaching the
failure boundary.

**Does not work:** awareness campaigns; one-off training with no follow-up;
mandates without workflow change; prompt libraries as the primary enablement
asset; centrally chosen use cases with no local owner; measuring licences;
reassurance that contradicts the operating plan.

## Interview-grade positions worth holding

- The target is calibrated trust, not maximum adoption; over-reliance is a real
  and under-managed failure mode.
- Senior expert resistance is usually rational, because the evidence says they
  gain least.
- The highest-value enablement is task-boundary literacy, not prompt technique.
- Reported adoption understates real adoption, and the gap is a security
  problem as much as a cultural one.
- Middle management is the bottleneck, and their metrics, not their mindset, are
  the thing to change.
- Honesty about the harvest decision buys more trust than reassurance does.

## Glossary

- **Algorithm aversion** — The tendency to abandon an algorithm after seeing it err, more readily than a human advisor who erred comparably; documented by Dietvorst, Simmons and Massey (2015).
- **Outcome control effect** — The finding that allowing users to modify an algorithm's output, even slightly, substantially restores willingness to use it; the strongest known counter to algorithm aversion.
- **Algorithm appreciation** — The opposite tendency, in which people weight algorithmic advice above human advice, strongest for objective or quantitative tasks and among non-experts (Logg, Minson and Moore, 2019).
- **Uniqueness neglect** — Resistance driven by the belief that one's own case is too distinctive for a statistical system to handle; identified as a driver of resistance to medical AI.
- **Automation bias** — Over-acceptance of machine output and decayed verification, worst where a system is usually right and failures are rare.
- **Calibrated trust** — Trust proportional to actual reliability, accepting output where the system is dependable and scrutinising it where it is not; the correct adoption target.
- **Jagged technological frontier** — The irregular, invisible boundary of model capability, where tasks of similar apparent difficulty fall on opposite sides (Dell'Acqua et al., 2023).
- **Task-boundary literacy** — Users' practical understanding of where the capability frontier sits for their own work, and how to verify near it; the highest-value enablement content.
- **Centaur / cyborg** — Two effective usage patterns: dividing tasks between human and model (centaur) versus continuously interleaving with it (cyborg).
- **Performance compression** — The repeated field finding that generative tools raise the floor more than the ceiling, concentrating gains among less experienced workers.
- **Apprenticeship disruption** — The erosion of the traditional path by which junior professionals build judgement through repetitive early work now performed by AI.
- **Evaluative penalty for AI use** — The tendency of peers and managers to judge disclosed AI assistance as reflecting lower competence or diligence, which suppresses disclosure.
- **Shadow AI** — Unsanctioned use of AI tools outside approved channels; largely a symptom of slow provisioning and unsafe disclosure rather than of defiance.
- **Harvest mechanism** — The explicit decision about how released capacity becomes a financial outcome; naming it honestly is a trust intervention as well as a strategy one.
- **Week-four retention** — Sustained use one month in; the most reliable early adoption signal, since week-one curiosity spikes are near-universal and uninformative.
