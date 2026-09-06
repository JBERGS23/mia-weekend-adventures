# AI Career Platform

A local web app supporting an AI strategy / transformation job search. Three
connected parts:

- **Job Scanner** — searches widely for senior AI strategy and transformation
  roles, dedupes against everything you have already seen, flags compensation
  confidence, and keeps a searchable archive of every posting and decision.
- **Academy** — five permanent learning modules, each with a substantial
  built-in primer, a glossary, refreshed external deeper-dive links, and a
  daily quiz that rotates across all five.
- **Networking** — a short, ranked list of at most ten live targets, generated
  only for companies you have actually shortlisted, plus a couple of reserved
  slots for companies that look like they will need this leadership soon.

Underneath them sits a **skills-gap engine**. It is not a separate module and
has no screen of its own. It reads your diagnostic baseline, what scanned job
descriptions are asking for, and your quiz results, and turns them into a
priority weight per module that decides which topics the daily questions lean
toward and which content gets refreshed first.

---

## Getting started

You need Python 3.11 or newer. Check what you have:

```bash
python3 --version
```

### 1. Install the two dependencies

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `.venv` part creates a private folder for this app's dependencies so it
cannot interfere with anything else on your machine. You only do this once.
Every time you open a new terminal afterwards, run `source .venv/bin/activate`
again before starting the app. On Windows the activate command is
`.venv\Scripts\activate` instead.

### 2. Add your Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Get a key from the Anthropic Console. To avoid re-typing it every time, add
that line to the end of your `~/.zshrc` (or `~/.bashrc`) file.

**The app works without a key.** Browsing, the primers, the daily quiz,
shortlisting, the archive and the networking review all run offline. Only the
things that need the live internet are switched off: scanning for new roles,
refreshing the deeper-dive links, generating new quiz questions, and finding
networking targets. The app says so plainly rather than failing oddly.

### 3. Run it

```bash
python run.py
```

It opens `http://127.0.0.1:5001` in your browser. Stop it with `Ctrl-C`.

### Want to see it populated first?

```bash
python demo.py
```

This loads made-up example data so you can see what a working app looks like
before your first scan. Everything is prefixed `[DEMO]`, and it writes to a
completely separate file (`data/demo.db`), so demo data can never mix with your
real data. Delete `data/demo.db` to reset it.

---

## Using it

**Run scan** (top right) searches all eight sources. It takes several minutes,
runs in the background, and shows progress as it goes — you can keep using the
app while it runs.

**Today** is the daily landing page: what is new, what to study, who to talk to.

**Jobs** is the review queue. Each posting shows a fit score, its track, whether
it carries an explicit AI mandate, and a compensation figure that is always
labelled `Confirmed`, `Estimated` or `Unknown`. Shortlist or dismiss each one.
Dismissed roles stay in the archive; nothing is ever deleted.

Shortlisting is the trigger for the networking module — it is the only thing
that puts a company on that list.

**Academy** holds the five modules. Read a primer, follow the deeper-dive links,
and answer the day's questions. Use **More of this / Less of this** on any
module to nudge how much attention it gets.

**Networking** is deliberately short. Work a target, mark it done, and the list
makes room for the next one.

**Diagnostics** exists so nothing is a black box: exactly how each study
priority was derived, what every scan did, and what the API has cost.

---

## How the pieces fit together

```
   Job Scanner ──────► job requirements ──┐
                                          ├──► Gap Engine ──► quiz rotation
   Reference layer ───► role requirements ─┤                  content refresh
   (web search)                            │                  priority order
   Quiz results ──────────────────────────┤
   Your feedback ─────────────────────────┘

   Shortlist a job ──► Networking targets for that company
   Market signals ───► Latent-demand targets (reserved slots)
```

Two loops close:

1. **Scan → gap → quiz.** Scanned job descriptions are broken into requirements
   and mapped onto the five modules. Modules the market is asking for and you
   are weakest in get more of tomorrow's questions.
2. **Quiz → gap.** Your answers update measured proficiency, which lowers a
   module's priority as you get better at it.

---

## Configuration

Everything tunable is in `config.py` with a comment explaining it: the
compensation floor and target, how many days count as "new", how many questions
per day, the networking cap, and the mix between gap-weighted and retention
questions. Edit that file and restart.

You can also override any of them with environment variables without editing
code, for example:

```bash
CAREER_QUIZ_COUNT=8 python run.py
```

---

## Where things live

```
career-platform/
├── run.py               Start the app
├── demo.py              Start it with example data (separate database)
├── config.py            Every setting, in one place
├── data/career.db       Your data. Back it up by copying this file.
└── app/
    ├── schema.sql       The database structure
    ├── db.py            Database helpers
    ├── seed.py          Loads modules, primers, baseline and starter quizzes
    ├── research/        Web research via the Anthropic API (the only network code)
    ├── jobs/            Scanner: sources, extraction, scoring, storage
    ├── gap/             The skills-gap engine and its reference layer
    ├── academy/         Modules, primers, quizzes, feedback
    │   └── primers/     The five written primers, as markdown
    ├── networking/      Target generation, ranking, the cap
    └── web/             Routes, templates, one stylesheet
```

Your data is a single SQLite file at `data/career.db`. To back it up, copy that
file. To start completely fresh, delete it and restart the app.

---

## Running the tests

```bash
python -m pytest tests/ -q
```

The suite runs entirely offline against throwaway databases with a stubbed
research layer, so it costs nothing and touches none of your data.

---

## Notes and limits

- **Single user, local only.** No login, no hosting, no multi-user support. It
  binds to `127.0.0.1`, so it is not reachable from other machines.
- **Live research costs money.** Each scan makes eight API calls that use web
  search. Diagnostics shows the running token and search totals.
- **The scanner reports, it does not verify.** Every prompt tells the model to
  report only postings it actually found and never to invent one, and every row
  keeps its source URL so you can check. Treat an unusually good-looking role as
  worth clicking through before acting on it.
- **Compensation is never a filter.** Most senior postings do not state pay, so
  a strong role with `Unknown` compensation still surfaces. The confidence flag
  is always shown next to the number.
- **The governance primer ages fastest.** AI regulation moves quickly and
  effective dates in particular have repeatedly shifted. That primer carries a
  standing caveat about it; the deeper-dive links are the check.

### Deliberately not built (phase 2 candidates)

Hosted deployment, automated daily email or push notifications, LinkedIn
contacts import and warm-intro mapping, paid job-scraper APIs, and multi-user
support. The database already carries the columns warm intros will need, so
that can be added later without a rework.
