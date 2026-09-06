# Technical Fluency for Non-Technical Leaders

## What the goal actually is

The goal is not to write code. It is to be the person in the room who can ask
the question that changes the decision, and who cannot be sold something absurd.
Concretely, fluency means you can:

- explain in plain language why a model produced a confident wrong answer, and
  what class of fix addresses it;
- tell the difference between a problem that needs better retrieval, better
  prompting, better data, or a different model - because those have wildly
  different costs;
- read a vendor's benchmark claim and know why it may be irrelevant;
- estimate roughly what something will cost to run at scale, not just to pilot;
- know when an engineer is describing a real constraint versus a preference.

Everything below is calibrated to that bar.

## How a language model actually works

**Tokens.** Text is split into tokens - roughly word-fragments. A rule of thumb
for English is about 0.75 words per token, or ~1.3 tokens per word. Everything
in the economics and the limits of these systems is denominated in tokens:
context windows, pricing, latency.

**Next-token prediction.** A language model is a very large function that takes a
sequence of tokens and outputs a probability distribution over what the next
token should be. It samples one, appends it, and repeats. That is the entire
mechanism at inference time. Everything else - reasoning, coding, summarising -
is a behaviour that emerges from doing this extremely well over a vast amount of
text.

**The transformer and attention.** The architecture that made this work is the
transformer, and the key mechanism is **attention**: when processing each token,
the model computes how much every other token in the context should influence
it. This is why these models handle long-range dependencies well, and also why
cost grows steeply with context length - attention is computed across the
sequence. "Parameters" are the learned weights; more parameters mean more
capacity, though the relationship to capability is far from linear and has been
overtaken as a headline number by training data quality and post-training.

**Embeddings.** Tokens and passages are represented as vectors - long lists of
numbers - positioned such that semantically similar things are near each other.
This is the mechanism behind semantic search and retrieval. An embedding model
is a different, much smaller and cheaper model than a generative one, and
confusing the two is a common tell.

**How models are trained**, in three stages worth naming:

1. **Pretraining** - predict the next token across an enormous corpus. This is
   where knowledge and general capability come from, and where nearly all the
   compute is spent. It costs a great deal and happens rarely.
2. **Supervised fine-tuning (SFT)** - training on curated examples of desired
   input-output behaviour. Turns a text predictor into something that follows
   instructions.
3. **Preference-based training (RLHF and relatives)** - using human or
   AI-generated preference comparisons to shape the model toward helpful,
   accurate, appropriately cautious responses. This stage does most of the work
   in making a model usable and safe, and it is why two models trained on
   similar data can behave very differently.

**Why models hallucinate.** The model is producing plausible continuations, not
looking anything up. When the training data is thin, ambiguous, or the question
presupposes something false, the most plausible continuation can be confidently
wrong. Note the asymmetry that matters operationally: **fluency is uncorrelated
with accuracy**. There is no internal signal in the output that distinguishes a
well-grounded answer from a fabricated one, which is exactly why grounding via
retrieval, citation, and verification is architectural rather than optional.

**Sampling and temperature.** Because the model outputs a distribution, you
choose how to sample. Low temperature makes it pick high-probability tokens -
more deterministic, more repetitive. Higher temperature increases variety and
error rate. For extraction and classification, low. For ideation, higher. Note
that even at low temperature the output is not guaranteed identical run to run,
which surprises people who expect software to be deterministic.

**Context window.** The total tokens the model can attend to at once - prompt,
retrieved documents, conversation history, tool results, and the response.
Modern frontier models offer very large windows (hundreds of thousands to a
million tokens). Large does not mean free or uniformly effective: cost scales
with what you put in, and models attend less reliably to material buried in the
middle of very long contexts. Curating what goes into the window - **context
engineering** - is a real discipline.

**Reasoning and test-time compute.** The significant recent shift: models can be
trained to produce an extended internal reasoning process before answering, and
to spend *more computation at inference time* on harder problems. This is a
different scaling axis from making the model bigger - you buy accuracy with
inference tokens rather than training runs. Practically, it means the same model
can be dialled between fast-and-cheap and slow-and-more-accurate, and that
"which model" is now a less complete question than "which model at what effort".

## The adaptation ladder: getting a model to do your task

This is the single most useful mental model in this primer, because the rungs
differ by orders of magnitude in cost and are routinely confused.

1. **Prompting.** Clear instructions, role, constraints, and output format.
   Free, instant, and the answer far more often than people expect.
2. **Few-shot examples.** Include several worked examples in the prompt. Very
   effective for format and style consistency; costs context, not engineering.
3. **Retrieval-augmented generation (RAG).** Fetch relevant documents at query
   time and put them in the context. **This is how you give a model knowledge it
   does not have.** Days to weeks of work.
4. **Tool use.** Let the model call functions - query a database, hit an API,
   run code. This is how you give a model *capabilities* and access to live
   state rather than static knowledge.
5. **Fine-tuning.** Continue training on your examples to change *behaviour*:
   tone, format adherence, domain-specific classification, following an unusual
   procedure. Weeks, real cost, and a maintenance commitment.
6. **Continued pretraining.** Training on a large domain corpus. Rare,
   expensive, and almost never the right answer for an enterprise.

**The decision rule that prevents most expensive mistakes: use retrieval to add
knowledge, use fine-tuning to change behaviour.** Fine-tuning a model to "know"
your product catalogue is the classic costly error - it is slow, it is stale the
day the catalogue changes, it produces confident errors on the gaps, and
retrieval does it better for a fraction of the cost. Fine-tuning earns its keep
when you need consistent adherence to a specific output format or process, when
you want a small cheap model to imitate a large one on a narrow task
(**distillation**, which is often the strongest ROI case), or when prompt length
has itself become the cost problem.

Also worth knowing: **LoRA / parameter-efficient fine-tuning** trains a small
number of additional weights rather than the whole model, which is why
fine-tuning is far cheaper than it was and why serving many task-specific
variants is practical.

## RAG in enough detail to interrogate it

The pipeline: **ingest** documents, **chunk** them into passages, **embed** each
chunk into a vector, **store** the vectors in an index, then at query time
**embed the query**, **retrieve** the nearest chunks, optionally **rerank** them,
and **generate** an answer conditioned on the retrieved text, ideally with
citations.

Where it actually goes wrong, in order of frequency:

- **Retrieval quality, not generation quality.** If the right passage was never
  retrieved, no model can save the answer. When a RAG system is disappointing,
  the diagnosis is nearly always retrieval. Ask to see retrieval measured
  separately from end-to-end answer quality; teams that cannot do this are
  guessing.
- **Chunking.** Split too small and context is lost; too large and retrieval
  gets imprecise. Chunking on document structure beats fixed-size splitting.
- **Pure semantic search misses exact terms.** Embeddings are bad at part
  numbers, error codes, and names. **Hybrid search** - combining keyword search
  with vector search - is the standard fix and its absence is a common cause of
  poor results.
- **Reranking.** A second-stage model that reorders candidates for relevance.
  Cheap to add and usually a large quality gain.
- **Stale or ungoverned corpora.** Retrieval faithfully surfaces the outdated
  policy document nobody deleted. Retrieval inherits every content-governance
  problem the organisation already had, and it also inherits its **permissions
  problem**: an index built without per-document access control will happily
  quote a document the asker was never allowed to see.

A live architectural debate worth being able to reference: as context windows
grow and models get better at using tools, some workloads are shifting from
classic pre-indexed RAG toward **agentic search**, where the model iteratively
searches and reads, more like a person. Classic RAG remains cheaper and lower
latency at scale; agentic retrieval handles messy, multi-hop questions better.

## Evaluation: the topic that most repays a leader's attention

If you take one technical discipline seriously, take this one, because it is
where enterprise deployments most often lack rigour and where a leader's
insistence changes outcomes.

- **Public benchmarks are weak evidence for your use case.** They are general,
  frequently contaminated by training data, and measure things adjacent to what
  you need. Never select a vendor on a leaderboard.
- **Build a golden set.** A hundred or more real inputs from real workflows with
  agreed correct outputs, curated by the people who do the work. This is the
  single highest-leverage artefact an AI programme owns, and it is a
  *business* deliverable, not an engineering one.
- **LLM-as-judge.** Using a strong model to grade outputs against a rubric.
  Scales evaluation enormously and correlates well with human judgement when the
  rubric is specific. Validate the judge against human ratings before trusting
  it, and know its biases (it tends to favour longer, more confident answers).
- **Regression testing.** Every prompt change, model upgrade, or new tool must
  be re-run against the golden set. Without this, systems silently degrade and
  nobody can say when or why.
- **Measure the pipeline in parts.** For RAG: retrieval precision and recall
  separately from answer quality. For agents: per-tool success rates. Aggregate
  end-to-end scores tell you something is wrong but never what.

## Data infrastructure, honestly

"Our data isn't ready" is usually true, but it is used to justify far more delay
than it should, because people imagine a multi-year data transformation is a
prerequisite. What actually has to be true, roughly in order:

- **Accessibility.** The data can be reached programmatically without a ticket
  and a week. This is the most common real blocker.
- **Permissions that travel.** Whatever governs who can see a document must be
  enforceable at retrieval time, or you have built a leak.
- **Sufficient quality for the specific use.** Not perfect - sufficient. A
  support-deflection use case tolerates messiness that a pricing model does not.
- **Lineage and freshness.** You can say where a number came from and how old it
  is.

The vocabulary: a **data warehouse** stores structured, modelled data for
analytics; a **data lake** stores raw files of any shape cheaply; a
**lakehouse** is the now-dominant convergence, adding warehouse-style
transactions and governance over lake storage. **ETL/ELT** moves and reshapes
data between them. A **data catalogue** records what exists and what it means;
**lineage** records where it came from. A **feature store** serves consistent
inputs to models in training and production. **Vector databases** store
embeddings for retrieval; note that most established databases have added vector
search, so a separate vector database is a choice rather than a necessity.

The pragmatic position: do not sequence the entire AI programme behind a data
platform rebuild. Pick the first two workflows, fix the data those specifically
need, and let real use cases pull the platform work in a prioritised order. A
data programme with no consuming use case is how a company spends three years
and gets a catalogue nobody opens.

## Inference economics and deployment

- **You pay per token**, with input tokens typically much cheaper than output
  tokens. Cost therefore scales with usage rather than seats, which breaks the
  budgeting instincts of anyone who grew up with licensed software. Model the
  cost of *success*.
- **Prompt caching** stores a stable prefix (a long system prompt, a large
  document) so repeated calls do not reprocess it, often cutting cost on that
  portion by an order of magnitude. Requires the stable content to come first
  and stay byte-identical - a timestamp in the system prompt silently defeats it.
- **Batch processing** is materially cheaper for anything not latency-sensitive.
- **Latency** has two parts: time to first token (what makes it feel responsive)
  and tokens per second (throughput). Streaming hides latency and is why chat
  interfaces feel fast.
- **API versus self-hosting.** APIs win on capability, operational simplicity,
  and keeping pace with model improvements. Self-hosting open-weight models wins
  on data residency, extreme volume economics, and full control - at the price of
  real MLOps capability and a permanent upgrade treadmill. For most enterprises,
  API-first with a self-hosted option for specific constrained workloads is the
  defensible answer.
- **Quantisation** reduces model precision to run faster and cheaper on smaller
  hardware, with some quality loss; relevant only if you are self-hosting.

## Questions a fluent leader asks

- What is the golden set, who curated it, and what does the current system score
  on it?
- Are retrieval and generation measured separately?
- What is the cost per completed task at projected volume, not per API call?
- Is the failure mode here a wrong answer or a missing answer, and which can the
  business tolerate?
- What happens when the underlying model is upgraded or deprecated?
- Do the retrieval permissions match the source-system permissions?
- Is this a knowledge problem or a behaviour problem? (Retrieval or fine-tuning.)

## Nonsense detectors

- "We fine-tuned it on our data so it knows our products." Usually the wrong
  tool, and a sign nobody senior asked why.
- "It's 95% accurate." On what task, measured against what, on how many
  examples, and what does the 5% look like?
- "It beats GPT-class models on benchmark X." Irrelevant without your tasks.
- "It doesn't hallucinate." Nothing eliminates hallucination; grounding and
  citation reduce and expose it.
- "We need a vector database first." Occasionally true, usually a solution
  arriving before a problem.
- "It learns from every interaction." Almost never literally true in enterprise
  deployments, and if it were, that would be a governance problem, not a feature.

## Glossary

- **Token** — The unit of text a model processes, roughly a word fragment; the denomination of context limits, pricing and latency.
- **Next-token prediction** — The core inference mechanism: repeatedly sample the most plausible next token given everything so far.
- **Transformer** — The neural architecture underlying modern language models, built around the attention mechanism.
- **Attention** — The mechanism by which each token's processing is influenced by every other token in context; the source of long-range coherence and of steep cost growth with context length.
- **Parameters** — The learned weights of a model; a capacity indicator, but a weak proxy for capability compared with data quality and post-training.
- **Embedding** — A vector representation placing semantically similar text near each other; the basis of semantic search.
- **Pretraining** — The large, expensive stage where a model learns general capability by predicting tokens across a vast corpus.
- **Supervised fine-tuning (SFT)** — Training on curated input-output examples to make a model follow instructions or adopt a behaviour.
- **RLHF** — Reinforcement learning from human feedback; preference-based post-training that shapes helpfulness, accuracy and caution.
- **Hallucination (confabulation)** — A fluent, confident output that is not grounded in fact; unavoidable in principle because fluency and accuracy are produced by the same mechanism.
- **Temperature** — The sampling parameter trading determinism against variety; low for extraction and classification, higher for ideation.
- **Context window** — The maximum tokens a model can attend to at once, spanning prompt, retrieved content, history, tool results and response.
- **Test-time compute** — Spending more computation at inference on harder problems to buy accuracy, a scaling axis distinct from model size.
- **Retrieval-augmented generation (RAG)** — Fetching relevant documents at query time and conditioning generation on them; the correct way to give a model knowledge it lacks.
- **Chunking** — Splitting documents into retrievable passages; structure-aware chunking outperforms fixed-size splitting.
- **Hybrid search** — Combining keyword and vector search, the standard fix for embeddings' weakness on exact terms like part numbers and codes.
- **Reranking** — A second-stage relevance model that reorders retrieved candidates; cheap and usually a large quality gain.
- **Agentic search** — Iterative model-driven searching and reading in place of a pre-indexed retrieval pipeline; better on multi-hop questions, more expensive.
- **LoRA / PEFT** — Parameter-efficient fine-tuning that trains a small set of added weights rather than the full model, making fine-tuning and multi-variant serving affordable.
- **Distillation** — Training a smaller, cheaper model to imitate a larger one on a narrow task; often the strongest fine-tuning business case.
- **Golden set** — A curated collection of real inputs with agreed correct outputs, used to evaluate and regression-test a system; a business deliverable, not an engineering one.
- **LLM-as-judge** — Using a strong model to grade outputs against a rubric, validated against human ratings before being trusted.
- **Regression testing** — Re-running the golden set after every prompt, model or tool change to catch silent degradation.
- **Data lakehouse** — The convergence of data lake storage with warehouse-style transactions and governance; the dominant modern pattern.
- **Data lineage** — The record of where a data element came from and how it was transformed.
- **Feature store** — Infrastructure serving consistent model inputs across training and production.
- **Vector database** — A store optimised for embedding similarity search; increasingly a feature of existing databases rather than a separate product.
- **Prompt caching** — Reusing a stable, byte-identical prompt prefix across calls to cut cost and latency substantially.
- **Quantisation** — Reducing numerical precision to run a model faster and cheaper, with some quality loss; relevant to self-hosting.
- **Time to first token** — The latency component that determines perceived responsiveness, distinct from overall throughput.
