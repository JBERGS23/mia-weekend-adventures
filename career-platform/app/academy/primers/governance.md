# AI Governance & Regulation

> **A standing caveat.** This is the fastest-moving area in the whole field, and
> effective dates in particular have repeatedly slipped. Treat every date below
> as "verify before you cite it in a room" - the deeper-dive links under this
> primer are refreshed precisely because this section ages fastest. What does
> *not* age is the structure: the risk-tier logic, the role definitions, the
> obligation categories, and the control apparatus.

## Why this is the module that separates candidates

Almost every senior AI strategy candidate can talk about use-case
prioritisation. Far fewer can hold a fluent conversation about the EU AI Act's
role definitions, why a US state patchwork is a genuine operating problem, or
what a risk-tiered control catalogue actually contains. In regulated industries
this is frequently the deciding competence, because the person hiring already
has strategists and needs someone who can get things *approved*.

There is a useful reframe here for anyone who has built a risk-tiering framework
for a client: **you have already built the spine.** Risk tiering is the
organising structure of essentially every AI governance regime in the world. The
gap is not conceptual; it is knowing what the specific regimes call the tiers,
what obligations attach to each, and which regulators enforce them.

## Three layers, kept separate

Sloppy conversation collapses these; keeping them distinct is itself a signal of
fluency.

1. **Internal governance** - the company's own apparatus: inventory, intake,
   risk tiering, control requirements, approval gates, monitoring, incident
   response. Voluntary in form, and where nearly all of the actual work is.
2. **Horizontal regulation** - law that applies to AI as such, regardless of
   sector. The EU AI Act is the archetype; US state statutes are the emerging
   version.
3. **Sector regulation** - existing regulators applying existing authority to AI
   within their remit. This is where enforcement is actually happening today,
   and it is systematically underestimated.

## Frameworks: the internal spine

**NIST AI Risk Management Framework (AI RMF 1.0).** Voluntary, US, and the most
widely adopted internal scaffolding. Four functions:

- **Govern** - the cross-cutting culture, policies, roles and accountability
  that the other three sit inside. Not a phase; a continuous function.
- **Map** - establish context: what the system is for, who it affects, what
  could go wrong, and in what setting it operates.
- **Measure** - assess, benchmark and monitor the identified risks with
  quantitative and qualitative methods.
- **Manage** - allocate resources to treat risks, decide on deployment, and
  respond to incidents.

The **Generative AI Profile (NIST AI 600-1)** extends this with risks
characteristic of generative systems: confabulation, dangerous or violent
content recommendations, data privacy leakage, harmful bias, information
integrity, information security, intellectual property, obscene content,
environmental impact, human-AI configuration issues, and value-chain opacity.
Knowing that this profile exists, and that it is the practical bridge from the
generic RMF to generative deployments, is a fast credibility marker.

**ISO/IEC 42001** is the certifiable one, and that distinction matters
commercially. It specifies an **AI Management System** - the auditable
management-system pattern familiar from ISO 27001 (scope, policy, roles, risk
assessment, objectives, operational controls, internal audit, management review,
continual improvement). Because it is certifiable, it functions as a
*procurement asset*: it is increasingly requested in enterprise and public-sector
RFPs, so the business case for pursuing it is often commercial rather than
compliance-driven. **ISO/IEC 23894** is the companion AI risk-management
guidance and is not certifiable.

Also worth knowing by name: the **OECD AI Principles** and the OECD's definition
of an AI system, which the EU AI Act's definition was aligned to; the **Council
of Europe Framework Convention on AI**, the first binding international treaty
on AI; and the **EU AI Act's** own harmonised standards work, which determines
how high-risk obligations are actually demonstrated in practice.

## The EU AI Act

The world's first comprehensive horizontal AI law, and the reference point every
other regime is measured against. Even for a US-centric role, fluency here is
expected, because it sets the de facto global floor for multinationals - the
"Brussels effect".

**Scope and extraterritoriality.** It applies to providers placing AI systems on
the EU market *and* to providers and deployers outside the EU where the output
is used in the EU. A US company with EU operations or EU customers is in scope.
Excluded: purely military/defence/national-security uses, pure scientific
research and development, and personal non-professional use.

**Roles - get these right, they carry the obligations.**

- **Provider** - develops an AI system or general-purpose model and places it on
  the market under its own name or trademark. Carries the heaviest obligations.
- **Deployer** - uses an AI system under its own authority in a professional
  capacity. This is what most enterprises are for most systems, and the
  obligations are real but much lighter.
- **Importer** and **distributor** - the usual product-law supply-chain roles.

The trap worth knowing: **a deployer can become a provider.** Putting your own
name on a system, substantially modifying it, or repurposing a general system
into a high-risk use flips you into provider obligations. Enterprises that
heavily customise a vendor model can cross this line without noticing, and
saying so in an interview demonstrates real familiarity rather than a summary
read.

**The risk tiers.**

- **Unacceptable risk - prohibited.** Social scoring by public authorities;
  manipulative or exploitative techniques causing significant harm; exploiting
  vulnerabilities of specific groups; untargeted scraping of facial images to
  build recognition databases; emotion inference in workplaces and education
  (narrow exceptions); biometric categorisation to infer protected attributes;
  and real-time remote biometric identification in public spaces for law
  enforcement, subject to narrow, authorised exceptions.
- **High risk.** Two routes in: **Annex I**, AI as a safety component of a
  product already covered by EU product legislation (medical devices,
  machinery, vehicles, lifts, toys); and **Annex III**, listed use cases -
  biometrics, critical infrastructure, education and vocational training,
  employment and worker management, access to essential private and public
  services (including creditworthiness and life/health insurance pricing), law
  enforcement, migration and border control, and administration of justice.
  There is a filter allowing systems that perform only narrow preparatory or
  procedural tasks to escape the tier, but it requires documented assessment
  and registration, not a unilateral assumption.
- **Limited risk - transparency obligations.** Disclose that a user is
  interacting with an AI system; mark synthetic content in a machine-readable
  way; disclose deepfakes; disclose emotion-recognition and biometric
  categorisation use.
- **Minimal risk.** The large majority of systems. No obligations beyond
  general law, though voluntary codes are encouraged.

Sitting across all tiers: an **AI literacy** obligation on providers and
deployers to ensure staff dealing with AI systems have a sufficient level of
understanding. This one is frequently missed, is cheap to satisfy, and is a
sensible thing for an incoming AI leader to own.

**High-risk obligations** are, for providers: a risk management system across
the lifecycle; data and data governance requirements covering training,
validation and testing sets; technical documentation; automatic logging;
transparency and instructions for use; human oversight design; accuracy,
robustness and cybersecurity; a quality management system; conformity
assessment and CE marking; and registration in the EU database. For
**deployers**, materially lighter but not nothing: use the system per the
instructions, assign competent human oversight with the authority to intervene,
ensure input data is relevant, monitor operation and report serious incidents,
retain logs, and inform affected workers. Public bodies and certain private
deployers must also complete a **fundamental rights impact assessment (FRIA)**.

**General-purpose AI (GPAI) models** have their own layer: technical
documentation, information for downstream providers, a copyright policy, and a
public summary of training content. Models presenting **systemic risk** -
identified by very high training compute, with a presumption threshold set at
10^25 floating-point operations, or by Commission designation - additionally
face model evaluation and adversarial testing, systemic risk assessment and
mitigation, serious incident reporting, and cybersecurity protection. A **GPAI
Code of Practice** provides the route to demonstrate compliance, and the **AI
Office** oversees GPAI enforcement.

**Penalties** are tiered: up to €35m or 7% of worldwide annual turnover for
prohibited practices; up to €15m or 3% for most other breaches; and up to €7.5m
or 1% for supplying incorrect or misleading information to authorities, with
lower caps for SMEs.

**Timing.** The Act entered into force in August 2024 with staggered
application: prohibitions and AI literacy first, then GPAI obligations, then
high-risk obligations, with the Annex I product route later still. **This
timeline has been the subject of active simplification and delay proposals, and
some obligations have moved.** Do not quote a specific high-risk application date
from memory in an interview; say the phasing runs from prohibitions through GPAI
to high-risk, note that the high-risk dates have been subject to amendment, and
that you track it. That answer is stronger than a confidently wrong date.

## The United States: no comprehensive law, plenty of regulation

**Federal.** There is no comprehensive federal AI statute. The executive-branch
posture shifted sharply in January 2025, when the prior administration's
executive order on AI was rescinded and replaced by a deregulatory,
innovation-and-competitiveness framing, subsequently elaborated in a national AI
action plan through 2025. Practical consequences: less federal prescriptive
rulemaking, continued sectoral enforcement under existing authority, and an
active push toward federal preemption of state AI laws - which as of this
writing has not comprehensively displaced them. The **FTC** remains the most
active general enforcer, using Section 5 authority against deceptive AI claims
(including a sweep specifically targeting AI-related deception) and against
unfair algorithmic practices. Existing law applies with no AI exception: if a
model produces a discriminatory lending outcome, it is a fair-lending violation
regardless of the technology.

**States - the patchwork, which is a genuine operating problem.**

- **Colorado** enacted the first comprehensive state AI statute, targeting
  *algorithmic discrimination* in **consequential decisions** (employment,
  lending, housing, insurance, healthcare, education, legal services). It splits
  duties between **developers** and **deployers**, requires reasonable care,
  impact assessments, risk management programmes, disclosures to affected
  individuals, and adverse-action notices with a right to correct data and
  appeal to human review. Its effective date has been delayed more than once and
  the text amended - a live example of why you verify dates.
- **Texas** enacted an AI governance act taking a notably different approach:
  largely **intent-based** prohibitions (intentional discrimination, behavioural
  manipulation, unlawful biometric use) rather than disparate-impact duties, plus
  a regulatory sandbox and attorney-general enforcement with a cure period.
- **Illinois** amended its Human Rights Act to address AI in employment
  decisions, prohibiting use that produces discriminatory effects and requiring
  notice; it also has the long-standing **BIPA** biometric statute, which carries
  a private right of action and has produced very large settlements.
- **California** has layered several statutes rather than one: automated
  decision-making technology rules under its privacy regime; training-data
  transparency for generative developers; provenance and detection-tool
  requirements for large generative providers; frontier-model transparency and
  safety-incident reporting for the largest developers; and a law restricting
  AI-driven denials in health-plan utilisation review.
- **New York City** requires annual independent **bias audits** and candidate
  notice for automated employment decision tools - narrow, but the first
  meaningfully enforced US AI audit mandate.
- **Utah** requires disclosure of generative AI use in regulated professions and
  on request in consumer interactions.

The operating consequence: a national employer running one hiring model faces
overlapping notice, audit, impact-assessment and appeal duties across several
states with different triggers and definitions. The mature response is to
**govern to the strictest applicable standard** and treat the patchwork as a
design constraint, rather than maintaining state-by-state variants of a model.

## Sector regulation beyond financial services

This is where enforcement actually bites today, and it is the part most
strategy candidates cannot speak to.

**Healthcare.** The **FDA** regulates AI-enabled software that meets the device
definition, and the important concept is the **Predetermined Change Control
Plan** - a mechanism for authorising a model that will be updated after
clearance, without a new submission for every change. That is the regulatory
answer to continuously learning models, and it is worth knowing by name.
Separately, US health-IT certification rules impose transparency requirements on
**decision support interventions** in certified electronic health records,
including disclosure of source attributes for predictive models. State laws
increasingly restrict AI in **utilisation review**, typically requiring that a
licensed clinician, not an algorithm, makes a coverage denial. HIPAA governs the
underlying data throughout.

**Employment and HR.** Title VII disparate-impact doctrine applies to
algorithmic screening with no AI exception; the **EEOC** has issued guidance on
AI under Title VII and the ADA, notably on adverse impact and on reasonable
accommodation in AI-mediated assessment. Add the NYC audit rule, the Illinois
amendment, and Colorado's consequential-decision duties, and hiring is the most
heavily regulated enterprise AI use case in the US.

**Insurance.** The **NAIC model bulletin on the use of AI systems by insurers**
has been adopted by a large number of states and expects a written **AI systems
programme** governing development, acquisition and use, with vendor oversight
and documentation - and it is enforceable through market-conduct examinations.
Colorado's insurance regulator went further with quantitative testing
requirements for unfair discrimination in life insurance underwriting.

**Consumer protection and advertising.** FTC Section 5 covers both deceptive
claims *about* AI ("AI-powered" products that are not) and unfair practices
*using* AI. This catches marketing organisations that never thought of
themselves as regulated.

**Housing, credit and education.** Fair-housing and fair-lending law applies to
tenant-screening and underwriting models; adverse-action notice requirements
mean a lender must give specific reasons even when a complex model produced the
decision, which is a real constraint on model choice. Education is an Annex III
high-risk category under the EU Act and increasingly a state-law focus in the US.

**Financial services** - for completeness, since it is the one area of existing
strength: model risk management supervisory guidance (the SR 11-7 lineage) is
the template much internal AI governance imitates, with its three-lines model,
independent validation, and inventory discipline.

## Building the apparatus: what actually gets implemented

A governance programme that works is a small number of mechanisms, run properly.

1. **An AI inventory.** A single register of every AI system in use, including
   vendor features that arrived by upgrade. You cannot govern what you cannot
   enumerate, and almost every organisation underestimates its inventory by a
   wide margin. This is always the first deliverable.
2. **Intake and triage.** One front door for new use cases, with a short
   screening questionnaire that assigns a risk tier. The design goal is that
   most things pass quickly; a process that treats a meeting summariser like a
   credit model will be routed around within a quarter.
3. **Risk tiering.** Typically three or four internal tiers, mapped explicitly
   to the external regimes that matter (EU Act tier, consequential-decision
   status, sector rules). The mapping is what turns an internal framework into a
   compliance artefact rather than a parallel exercise.
4. **A control catalogue by tier.** For each tier, the required controls:
   documentation, evaluation and bias testing, human oversight design, logging
   and retention, monitoring thresholds, disclosure language, approval level.
   The catalogue is the product; the committee is the delivery mechanism.
5. **Impact assessments.** DPIA where personal data is involved, FRIA where the
   EU Act requires it, algorithmic impact assessment where state law does.
   Standardise one template that satisfies all three.
6. **Third-party and vendor risk.** Most enterprise AI risk arrives through
   procurement. Standard diligence questions, contractual terms on training use,
   retention, indemnity, evaluation evidence, incident notice, and model-change
   notification.
7. **Pre-deployment evaluation and red-teaming.** Task-level accuracy on real
   data, bias testing on protected attributes where lawful, adversarial and
   prompt-injection testing for anything tool-using.
8. **Monitoring and drift detection**, with defined thresholds that trigger
   review rather than a dashboard nobody reads.
9. **Incident response.** A defined AI incident class, a severity scale,
   escalation path, and regulatory notification triggers - which now exist under
   several regimes.
10. **Audit and assurance.** Internal audit coverage, and external certification
    where it has commercial value.

## Common failure modes

- **Governance as a committee rather than a catalogue.** If the output is
  meeting minutes rather than reusable standards, teams route around it.
- **Uniform process for non-uniform risk.** The fastest way to lose credibility
  is to make low-risk deployments expensive.
- **No inventory.** Everything else is theatre without it.
- **Ignoring vendor-delivered AI.** Features that arrive in an existing SaaS
  product are the largest ungoverned surface in most enterprises.
- **Confusing model risk with use risk.** The same model is minimal risk in a
  drafting tool and high risk in a hiring screen. Tier the *use*.
- **Treating governance as a cost centre.** In regulated sectors it is the
  thing that lets deployment happen at all, and framing it that way is how the
  function gets funded.

## Interview-grade positions worth holding

- Risk tiering is the universal spine; the regimes differ mostly in what they
  call the tiers and what attaches to each.
- Deployer versus provider is the distinction that decides your obligations, and
  heavy customisation can quietly flip you into provider status.
- The US has no comprehensive federal law but plenty of enforcement, and the
  state patchwork is an operating constraint best answered by governing to the
  strictest applicable standard.
- Sector regulators using existing authority are doing more enforcement today
  than any AI-specific statute.
- The first deliverable is always the inventory.
- Governance done well is an enabler of deployment velocity, not a brake.

## Glossary

- **Risk tiering** — Classifying AI uses into levels with different obligations; the organising structure of nearly every AI governance regime, internal and statutory.
- **NIST AI RMF** — A voluntary US risk-management framework built on four functions: Govern, Map, Measure, Manage.
- **Generative AI Profile (NIST AI 600-1)** — The NIST companion extending the AI RMF to risks characteristic of generative systems, including confabulation, information integrity and value-chain opacity.
- **ISO/IEC 42001** — The certifiable AI Management System standard; commercially useful because certification is increasingly requested in procurement.
- **ISO/IEC 23894** — Companion AI risk-management guidance; guidance only, not certifiable.
- **Provider (EU AI Act)** — The party that develops an AI system or general-purpose model and places it on the market under its own name; carries the heaviest obligations.
- **Deployer (EU AI Act)** — The party using an AI system under its own authority in a professional capacity; lighter obligations centred on oversight, monitoring and instructions.
- **Annex III** — The EU AI Act's list of high-risk use cases, including employment, education, essential services, creditworthiness, insurance pricing, law enforcement and justice.
- **General-purpose AI (GPAI) model** — A model with broad capability across tasks, carrying its own EU AI Act obligations for documentation, downstream information and copyright policy.
- **Systemic risk (GPAI)** — A designation for the most capable models, presumed at very high training compute (10^25 FLOP) or by Commission designation, adding evaluation, adversarial testing and incident-reporting duties.
- **Fundamental Rights Impact Assessment (FRIA)** — An assessment required of certain deployers of high-risk systems under the EU AI Act, covering effects on affected persons' rights.
- **Data Protection Impact Assessment (DPIA)** — A GDPR-mandated assessment for processing likely to result in high risk to individuals; the closest existing analogue to an AI impact assessment.
- **Brussels effect** — The tendency of EU regulation to become a de facto global standard because multinationals govern to the strictest applicable regime.
- **Consequential decision** — A US state-law concept covering decisions with material legal or similarly significant effect (employment, lending, housing, insurance, healthcare, education), which triggers heightened duties.
- **Algorithmic discrimination** — Differential treatment or impact on protected classes produced by an automated system; the target of Colorado-style state statutes.
- **Disparate impact** — A discrimination theory based on effects rather than intent; the reason a facially neutral screening model can still be unlawful.
- **Adverse action notice** — A requirement to give specific reasons for a negative credit or employment decision, constraining the use of models whose reasons cannot be articulated.
- **Predetermined Change Control Plan (PCCP)** — An FDA mechanism authorising anticipated post-clearance model updates without a new submission each time.
- **Decision support intervention (DSI)** — A regulated category in US health-IT certification covering predictive and evidence-based support in certified EHRs, with source-attribute transparency requirements.
- **Utilisation review** — Health-plan coverage determination; increasingly subject to state laws requiring a licensed clinician rather than an algorithm to issue denials.
- **NAIC model bulletin on AI** — A widely adopted US state insurance expectation that insurers maintain a written AI systems programme with vendor oversight, enforceable via market-conduct exams.
- **BIPA** — Illinois's biometric privacy statute, notable for a private right of action and very large settlements.
- **Bias audit** — An independent assessment of an automated employment tool's selection rates across demographic groups; mandated annually in New York City.
- **AI inventory** — The register of every AI system in use, including vendor-delivered features; the prerequisite for every other governance control.
- **Model risk management (SR 11-7 lineage)** — Banking supervisory guidance establishing inventory, independent validation and lifecycle controls; the template most enterprise AI governance imitates.
- **AI literacy obligation** — The EU AI Act duty on providers and deployers to ensure staff working with AI have sufficient understanding of it.
