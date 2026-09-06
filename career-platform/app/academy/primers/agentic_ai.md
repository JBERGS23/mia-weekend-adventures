# Agentic AI & Orchestration

## Getting the definition right

"Agent" is used loosely enough that the first job in any senior conversation is
to say what you mean. The useful distinction is about **who controls the flow**:

- A **workflow** is a system where an LLM is called at predefined points along a
  path that *you* wrote in code. The steps, the order, and the exit conditions
  are fixed. The model fills in the intelligence; the engineer owns the control
  flow.
- An **agent** is a system where the model *directs its own process*: it decides
  which tools to call, in what order, and when the task is done. The control
  flow is emergent.

Everything else - "assistant", "copilot", "autonomous agent" - is marketing on
top of that axis. The strategically important consequence: workflows are
predictable, testable, cheap and boring; agents are flexible, expensive,
harder to evaluate, and occasionally do something nobody anticipated. **The
correct default is the simplest thing that works, and most production value in
enterprises today comes from workflows, not agents.** Being able to say that
clearly, without sounding like a sceptic, marks out someone who has actually
deployed this.

## The underlying loop

Under every agent is one mechanic, and it is worth being able to describe it
precisely:

1. The application sends the model a request containing the conversation plus a
   set of **tool definitions** - each a name, a description, and a JSON schema
   for its inputs.
2. The model responds either with a final answer, or with one or more **tool
   use** blocks: the name of a tool and arguments matching the schema.
3. The application executes those tools - a database query, an API call, a file
   write - and sends the results back as **tool results** in the next request.
4. The model reads the results and either produces a final answer or calls more
   tools. Repeat.

The model never executes anything itself. It emits structured requests; your
code decides what actually runs. That single fact is the foundation of every
security and governance control in agentic systems, and it is the point most
executives get wrong. The question "can we stop the agent doing X?" always
resolves to "does our code implement X as a callable tool, and under what
checks?"

Two refinements that matter in practice. **Parallel tool use**: a single model
turn can request several tools at once, which you execute concurrently and
return together. **Server-side tools**: some tools (web search, code execution)
run on the provider's infrastructure inside the same call, so there is no local
execution loop for them at all.

## The workflow patterns worth knowing by name

These cover the large majority of real deployments, and naming them is a fast
way to demonstrate fluency.

- **Prompt chaining.** Decompose into fixed sequential steps, each model call
  working on the previous output, often with a programmatic gate between steps.
  Use when a task cleanly decomposes and you want accuracy over latency.
- **Routing.** Classify the input, then send it to a specialised prompt, model,
  or path. Use when categories are distinct and handling them separately beats
  one prompt trying to do everything. Also the main lever for cost: route easy
  traffic to a cheaper model.
- **Parallelisation.** Two flavours: *sectioning* (split a task into
  independent subtasks run at once) and *voting* (run the same task several
  times and aggregate for confidence). Voting is underused for high-stakes
  classification.
- **Orchestrator-workers.** A central model breaks a task into subtasks
  dynamically, delegates each to a worker, and synthesises the results. This is
  the pattern behind most credible "multi-agent" systems.
- **Evaluator-optimiser.** One model produces, another critiques against
  explicit criteria, loop until the critique passes. Works when you can
  articulate what good looks like well enough to grade it.

## Tool design is the real engineering

An agent is only as good as the tools it is given, and tool design is where
most agent projects quietly fail. The failure is rarely model capability; it is
that the tools are a thin wrapper over an internal API designed for programmers,
returning 4,000 tokens of nested JSON with no indication of what matters.

Principles that hold up:

- **Design tools for the model, not for the API.** Fewer, higher-level tools
  that match how a human would describe the job beat a faithful mirror of your
  REST endpoints.
- **The description is the interface.** The model has only the name,
  description, and schema. Ambiguity there produces wrong calls, and the fix is
  almost always better documentation rather than a better model.
- **Return compact, meaningful results.** Truncate, summarise, and signal
  errors explicitly. Tool results are the largest consumer of the context
  window in most agent runs.
- **Make errors instructive.** A returned error that says what to do next
  ("no records matched; try a broader date range") lets the model recover; a
  stack trace does not.
- **Make destructive tools narrow and gated.** Separate `read_x` from
  `delete_x`, and put approval in front of the second.

## MCP: what it is and why it matters strategically

The **Model Context Protocol** is an open standard for how applications expose
context and capability to language models. Rather than every AI product writing
a bespoke integration to every internal system, MCP defines a client-server
protocol: a **server** exposes *tools* (things the model can do), *resources*
(data it can read), and *prompts* (reusable templates); a **host** application
runs an MCP **client** that connects to those servers and makes their
capabilities available to the model. Transports are typically local process
(stdio) or HTTP for remote servers.

The strategic content, which is what an executive needs:

- It converts an **N x M integration problem into N + M**. Write one MCP server
  for your CRM and every MCP-capable AI application can use it, instead of every
  vendor building a separate connector.
- It **shifts build/buy**. Internal connector work becomes reusable
  infrastructure rather than per-vendor integration cost, which strengthens the
  case for building the middle layer and buying at the ends.
- It **preserves provider optionality**, because the integration layer is no
  longer coupled to one vendor's proprietary plugin format.
- It **creates a new governance surface.** Each server is an access path into a
  system of record. Who may run one, what credentials it holds, what it logs,
  and how a compromised or malicious server is contained are now real questions.
  Treating MCP servers as a managed internal catalogue with review and
  least-privilege credentials is the mature posture; letting every team run
  their own against production data is not.

## Multi-agent: when it earns its cost

Multi-agent systems - an orchestrator delegating to sub-agents with their own
context windows and tools - genuinely help in a narrow band of cases:

- The task **decomposes into independent parallel branches**, especially
  breadth-first research where each branch needs its own large context.
- Sub-tasks need **different tools or permissions**, and separating them is a
  security boundary rather than an architectural preference.
- **Context isolation** is the point: keeping a noisy sub-task's tokens out of
  the main thread's window.

They hurt when the work is sequential and interdependent, because coordination
overhead is real, errors compound across handoffs, and token cost multiplies -
a multi-agent run can consume several times the tokens of a single well-designed
agent for the same task. The honest position, and the one worth holding in an
interview: *multi-agent is an optimisation for parallel, context-heavy,
read-mostly work; it is not a default architecture, and reaching for it early is
a reliable sign a team is solving the wrong problem.*

## Context engineering

The operative discipline has shifted from prompt engineering to **context
engineering**: deciding what information occupies the model's limited attention
at each step. The levers:

- **Retrieval** - fetching only the relevant material rather than stuffing
  everything in.
- **Compaction** - summarising earlier turns when a long-running task
  approaches the window limit, preserving decisions and discarding transcript.
- **Context editing** - clearing stale tool results outright.
- **Memory** - persisting durable facts outside the context window and reading
  them back on demand.
- **Sub-agents** - isolating token-heavy exploration in a separate window and
  returning only conclusions.

Long-horizon agents fail far more often from context mismanagement - relevant
instructions crowded out, stale results treated as current - than from
insufficient model intelligence.

## Reliability, security, and the trust problem

**Prompt injection is the defining security issue.** Because tool results
re-enter the model's context as text, any untrusted content the agent reads - a
web page, an email, a support ticket, a PDF - can contain instructions aimed at
the model. The widely used framing is the **lethal trifecta**: an agent that
simultaneously has (1) access to private data, (2) exposure to untrusted
content, and (3) the ability to communicate externally can be induced to
exfiltrate. Removing any one leg breaks the attack. This is a design constraint,
not a bug to patch, and the mitigations are architectural: separate agents with
different trust levels, strip or sandbox untrusted content, restrict outbound
channels, and require human approval before irreversible or outbound actions.

Beyond injection, the reliability toolkit:

- **Evaluations before deployment and continuously after.** A held-out set of
  real tasks with automated grading. Without this you cannot tell whether a
  prompt change, a model upgrade, or a new tool made things worse.
- **Least privilege and non-human identity.** Agents act with delegated
  authority. Each needs its own scoped credential, not a shared service account
  with broad rights, and its actions need to be attributable.
- **Spend and step caps.** Bounded iterations and a token or dollar budget per
  run, so a loop cannot run up an unbounded bill.
- **Idempotency and reversibility.** Design tools so a retry does not double-
  charge a customer, and prefer reversible actions.
- **Observability.** Full traces of every tool call and result. Debugging an
  agent without traces is guesswork.

## Operating model for agentic deployment

This is the material that separates a strategist from an enthusiast, and it is
where the exec-level conversation actually lives.

**An agent in production is closer to a role than to a feature.** It has a
scope, a set of permissions, an owner, a performance history, and a cost. The
governance question is not "did we approve this software?" but "who is
accountable for what this thing does, and how would we know if it started doing
it badly?" A named human owner per deployed agent, with an explicit scope
statement and a review cadence, is the single most useful control to insist on.

**The autonomy ladder.** Deployments should climb it deliberately, one rung at a
time, with evidence at each step:

1. **Suggest** - the agent proposes, a human does the work.
2. **Draft** - the agent produces the artefact, a human reviews and submits.
3. **Act with approval** - the agent executes on a per-action human approval.
4. **Act with logging** - the agent executes autonomously inside a bounded
   scope, with full logs and sampled review.
5. **Act autonomously** - unattended within hard limits, with exception routing.

**The reversibility rule.** Automate the reversible; gate the irreversible.
Sending an internal draft is reversible. Issuing a refund, sending an external
email, or changing a customer record is not. Almost every sensible approval
boundary follows this line rather than a notional risk score.

**Review capacity is the real constraint on scale.** An agent that drafts ten
times faster than a human but still requires human approval scales only to the
limit of that reviewer's throughput. Programmes that fail to plan the review
tier hit a wall at pilot scale and mistake it for a technology problem. Either
the review tier is resourced, or the autonomy ladder is climbed with evidence,
or the deployment does not scale. Say this out loud early.

**Economics.** Agentic runs consume dramatically more tokens than single calls -
a long tool-using run can be one to two orders of magnitude more expensive than
a chat completion. Cost per *completed task* is the only meaningful unit,
because a cheaper model that needs more turns is not cheaper. Latency is a
genuine product constraint: a thirty-second agent run is unusable in an
interactive support flow and perfectly fine in an overnight batch.

## Interview-grade positions worth holding

- Most enterprise value today is in workflows, not agents; reach for an agent
  only when the task is genuinely open-ended.
- Tool design and context engineering, not model choice, determine whether an
  agent works.
- MCP matters less as a technology than as a change to the integration economics
  and a new governance surface.
- Multi-agent is an optimisation for parallel context-heavy work, not a default.
- Review capacity, not model capability, caps how far an agentic deployment
  scales.
- Automate the reversible; gate the irreversible.

## Glossary

- **Agent** — A system in which the model directs its own control flow, choosing which tools to call and when the task is complete.
- **Workflow** — A system in which LLM calls occur at predefined points along a path defined in code; predictable and testable, unlike an agent.
- **Tool use (function calling)** — The mechanic by which a model emits a structured request to call a named tool with schema-valid arguments, which the application executes and returns as a tool result.
- **Tool result** — The output of an executed tool, returned into the model's context on the next turn; the largest consumer of context in most agent runs and the main prompt-injection surface.
- **Model Context Protocol (MCP)** — An open client-server standard for exposing tools, resources and prompts to AI applications, turning an N x M integration problem into N + M.
- **MCP server** — A process exposing capabilities over MCP; from a governance perspective, a credentialed access path into a system of record.
- **Orchestrator-workers** — A pattern where a central model decomposes a task, delegates subtasks to workers, and synthesises the results.
- **Evaluator-optimiser** — A loop in which one model produces output and another critiques it against explicit criteria until the critique passes.
- **Prompt chaining** — Decomposing a task into fixed sequential model calls, often with programmatic checks between steps.
- **Routing** — Classifying an input and dispatching it to a specialised prompt, model, or path; the main lever for cost control.
- **Context engineering** — The discipline of curating what occupies a model's limited attention at each step, via retrieval, compaction, context editing, memory and sub-agents.
- **Compaction** — Summarising earlier conversation when a long-running task approaches the context limit, preserving decisions while discarding transcript.
- **Prompt injection** — An attack in which instructions embedded in content the model reads are treated as directions, hijacking the agent's behaviour.
- **Lethal trifecta** — The dangerous combination of private data access, exposure to untrusted content, and an external communication channel; removing any one leg breaks the exfiltration path.
- **Autonomy ladder** — The staged progression from suggest, to draft, to act-with-approval, to act-with-logging, to bounded autonomy.
- **Reversibility rule** — Automate actions that can be undone; require human approval for those that cannot.
- **Non-human identity** — A scoped, attributable credential issued to an agent rather than a shared service account, so its actions carry least privilege and an audit trail.
- **Cost per completed task** — The correct unit of agent economics, since a cheaper model requiring more turns is not actually cheaper.
