-- AI Career Platform - database schema (SQLite, phase 1).
--
-- Written to migrate cleanly to Postgres later:
--   * no SQLite-only column types (everything is TEXT / INTEGER / REAL)
--   * timestamps stored as ISO-8601 UTC strings, not SQLite date functions
--   * booleans stored as INTEGER 0/1
--   * no reliance on implicit rowid behaviour
--
-- Every table that holds model-generated content keeps the raw source URL and a
-- generated_at timestamp so nothing in the app is an unattributable assertion.

PRAGMA foreign_keys = ON;


-- ---------------------------------------------------------------------------
-- Module A: job scanner
-- ---------------------------------------------------------------------------

-- One row per scan run, so a run can be kicked off in the background and its
-- progress polled from the browser.
CREATE TABLE IF NOT EXISTS scan_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at     TEXT    NOT NULL,
    finished_at    TEXT,
    status         TEXT    NOT NULL DEFAULT 'running',  -- running | complete | failed
    -- Free-text line shown in the UI while the run is in flight.
    progress_note  TEXT,
    sources_run    INTEGER NOT NULL DEFAULT 0,
    sources_total  INTEGER NOT NULL DEFAULT 0,
    jobs_found     INTEGER NOT NULL DEFAULT 0,  -- postings returned by sources
    jobs_new       INTEGER NOT NULL DEFAULT 0,  -- postings that survived dedupe
    error          TEXT
);

-- Every posting ever seen. Nothing is deleted; the "new this week" view is a
-- query over this table, and the archive is the same table unfiltered.
CREATE TABLE IF NOT EXISTS jobs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity / dedupe
    fingerprint         TEXT    NOT NULL UNIQUE,  -- normalised company+title+location
    url                 TEXT,
    url_hash            TEXT,

    -- Core posting facts
    company             TEXT    NOT NULL,
    title               TEXT    NOT NULL,
    location            TEXT,
    remote_policy       TEXT,                     -- remote | hybrid | onsite | unknown
    posted_at           TEXT,                     -- ISO date if the source gave one
    posted_at_is_exact  INTEGER NOT NULL DEFAULT 0,
    description         TEXT,                     -- summary or excerpt of the JD
    requirements        TEXT,                     -- newline-delimited extracted requirements

    -- Classification
    track               TEXT,                     -- ai_native | traditional_transformation | pe_vc | consulting
    seniority           TEXT,

    -- Compensation, per spec 1.3: never hard-filtered, always confidence-flagged
    comp_min            INTEGER,
    comp_max            INTEGER,
    comp_currency       TEXT    DEFAULT 'USD',
    comp_confidence     TEXT    NOT NULL DEFAULT 'Unknown',  -- Confirmed | Estimated | Unknown
    comp_note           TEXT,

    -- Fit
    fit_score           REAL    NOT NULL DEFAULT 0,
    fit_rationale       TEXT,
    ai_mandate          INTEGER NOT NULL DEFAULT 0,  -- explicit AI transformation mandate in the JD
    mandate_evidence    TEXT,

    -- Provenance
    source_name         TEXT    NOT NULL,
    source_kind         TEXT,
    first_seen_at       TEXT    NOT NULL,
    last_seen_at        TEXT    NOT NULL,
    scan_run_id         INTEGER REFERENCES scan_runs(id),

    -- Jeff's decision. NULL = undecided and still in the review queue.
    decision            TEXT,                     -- shortlisted | dismissed
    decided_at          TEXT,
    decision_note       TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_decision    ON jobs(decision);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen  ON jobs(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company     ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_track       ON jobs(track);

-- Append-only decision history. `jobs.decision` holds the current state; this
-- table remembers that Jeff dismissed something before he changed his mind.
CREATE TABLE IF NOT EXISTS job_decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    decision    TEXT    NOT NULL,
    note        TEXT,
    decided_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_job_decisions_job ON job_decisions(job_id);

-- Skill phrases pulled out of scanned job descriptions. This is the "live
-- layer" input to the gap engine (spec 1.6).
CREATE TABLE IF NOT EXISTS job_skill_signals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id       INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    module_key   TEXT    NOT NULL,   -- which academy module this maps to
    phrase       TEXT    NOT NULL,   -- the requirement text that triggered it
    weight       REAL    NOT NULL DEFAULT 1.0,
    created_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_signals_module ON job_skill_signals(module_key);
CREATE INDEX IF NOT EXISTS idx_skill_signals_job    ON job_skill_signals(job_id);

-- Hiring / funding / leadership-move signals that suggest unadvertised roles.
-- Feeds the networking module more than the job list (spec 1.4, last bullet).
CREATE TABLE IF NOT EXISTS market_signals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint   TEXT    NOT NULL UNIQUE,
    company       TEXT    NOT NULL,
    signal_type   TEXT    NOT NULL,  -- funding | leadership_hire | ai_initiative | practice_launch
    headline      TEXT    NOT NULL,
    detail        TEXT,
    url           TEXT,
    signal_date   TEXT,
    strength      REAL    NOT NULL DEFAULT 0.5,
    scan_run_id   INTEGER REFERENCES scan_runs(id),
    created_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_signals_company ON market_signals(company);


-- ---------------------------------------------------------------------------
-- Module B: academy
-- ---------------------------------------------------------------------------

-- The five fixed modules (spec 2.1). Rows are seeded once and never deleted or
-- renamed; only their content and weights change.
CREATE TABLE IF NOT EXISTS academy_modules (
    key            TEXT PRIMARY KEY,
    name           TEXT    NOT NULL,
    blurb          TEXT    NOT NULL,
    sort_order     INTEGER NOT NULL,
    -- Deliberate damping so change management stays lighter (spec 2.3).
    weight_damping REAL    NOT NULL DEFAULT 1.0
);

-- The stable, substantial written explainer. Versioned so a refresh never
-- destroys the previous text.
CREATE TABLE IF NOT EXISTS primers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key    TEXT    NOT NULL REFERENCES academy_modules(key),
    version       INTEGER NOT NULL DEFAULT 1,
    body          TEXT    NOT NULL,   -- markdown
    source        TEXT    NOT NULL DEFAULT 'builtin',  -- builtin | refreshed
    is_current    INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL,
    UNIQUE (module_key, version)
);

CREATE INDEX IF NOT EXISTS idx_primers_current ON primers(module_key, is_current);

CREATE TABLE IF NOT EXISTS glossary_terms (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key   TEXT NOT NULL REFERENCES academy_modules(key),
    term         TEXT NOT NULL,
    definition   TEXT NOT NULL,
    UNIQUE (module_key, term)
);

-- Living external resources layered under the primer (spec 2.2).
CREATE TABLE IF NOT EXISTS resources (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key    TEXT    NOT NULL REFERENCES academy_modules(key),
    title         TEXT    NOT NULL,
    url           TEXT    NOT NULL,
    format        TEXT    NOT NULL DEFAULT 'article',  -- article | video | podcast | course | paper
    publisher     TEXT,
    published_at  TEXT,
    why           TEXT,                                -- one line on why it earns a slot
    rank          REAL    NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL DEFAULT 'active',   -- active | retired
    added_at      TEXT    NOT NULL,
    retired_at    TEXT,
    UNIQUE (module_key, url)
);

CREATE INDEX IF NOT EXISTS idx_resources_module ON resources(module_key, status);

CREATE TABLE IF NOT EXISTS quiz_questions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key        TEXT    NOT NULL REFERENCES academy_modules(key),
    question          TEXT    NOT NULL,
    -- JSON array of option strings, stored as text for Postgres portability.
    options_json      TEXT    NOT NULL,
    correct_index     INTEGER NOT NULL,
    explanation       TEXT    NOT NULL,
    style             TEXT    NOT NULL DEFAULT 'scenario',  -- scenario | recall
    difficulty        TEXT    NOT NULL DEFAULT 'core',
    primer_version    INTEGER,
    source            TEXT    NOT NULL DEFAULT 'builtin',   -- builtin | generated
    status            TEXT    NOT NULL DEFAULT 'active',
    created_at        TEXT    NOT NULL,
    UNIQUE (module_key, question)
);

CREATE INDEX IF NOT EXISTS idx_quiz_questions_module ON quiz_questions(module_key, status);

-- One row per served question, so rotation can avoid repeats and the gap
-- engine can read real accuracy per module.
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id   INTEGER NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    module_key    TEXT    NOT NULL REFERENCES academy_modules(key),
    quiz_date     TEXT    NOT NULL,   -- the local date this was served for
    served_at     TEXT    NOT NULL,
    answered_at   TEXT,
    chosen_index  INTEGER,
    is_correct    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_date   ON quiz_attempts(quiz_date);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_module ON quiz_attempts(module_key);

-- Lightweight "more of this / less of this" per module (spec 2.4).
CREATE TABLE IF NOT EXISTS module_feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key   TEXT NOT NULL REFERENCES academy_modules(key),
    signal       TEXT NOT NULL,   -- more | less
    note         TEXT,
    created_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_module_feedback_module ON module_feedback(module_key);


-- ---------------------------------------------------------------------------
-- Gap engine (spec 1.6) - not a user-facing module, it drives the academy
-- ---------------------------------------------------------------------------

-- Current computed state, one row per module. Overwritten on each recompute.
CREATE TABLE IF NOT EXISTS gap_state (
    module_key       TEXT PRIMARY KEY REFERENCES academy_modules(key),
    baseline_level   TEXT NOT NULL,   -- weak | developing | moderate | intermediate | strong
    baseline_score   REAL NOT NULL,   -- 0..1 proficiency from the spec 2.5 baseline
    baseline_note    TEXT,
    demand_score     REAL NOT NULL DEFAULT 0,  -- share of live job demand
    quiz_accuracy    REAL,                     -- NULL until enough attempts exist
    quiz_attempts    INTEGER NOT NULL DEFAULT 0,
    feedback_bias    REAL NOT NULL DEFAULT 1.0,
    priority         REAL NOT NULL DEFAULT 0,  -- normalised 0..1, sums to 1 across modules
    updated_at       TEXT NOT NULL
);

-- The "reference layer": a stable sense of what senior AI strategy roles
-- require, refreshed by web search rather than hardcoded (spec 1.6).
CREATE TABLE IF NOT EXISTS reference_requirements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key    TEXT    NOT NULL REFERENCES academy_modules(key),
    requirement   TEXT    NOT NULL,
    importance    REAL    NOT NULL DEFAULT 0.5,
    source_url    TEXT,
    source_title  TEXT,
    quality_note  TEXT,      -- why this source passed the quality bar
    refreshed_at  TEXT    NOT NULL,
    UNIQUE (module_key, requirement)
);

-- Audit trail of recomputes so weight changes are explainable.
CREATE TABLE IF NOT EXISTS gap_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    module_key   TEXT NOT NULL REFERENCES academy_modules(key),
    priority     REAL NOT NULL,
    demand_score REAL NOT NULL,
    reason       TEXT,
    recorded_at  TEXT NOT NULL
);


-- ---------------------------------------------------------------------------
-- Module C: networking
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS networking_targets (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint       TEXT    NOT NULL UNIQUE,

    company           TEXT    NOT NULL,
    person_name       TEXT,
    person_title      TEXT,
    profile_url       TEXT,

    -- One of the three recommendation types in spec 3.3. The third type
    -- (warm_intro) is deliberately not generated in phase 1, but the schema
    -- carries it so it can be switched on without a migration.
    rec_type          TEXT    NOT NULL,  -- person | engagement | warm_intro
    rationale         TEXT    NOT NULL,
    suggested_action  TEXT,
    evidence_url      TEXT,
    evidence_note     TEXT,

    -- Why this company is in play at all.
    job_id            INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    is_latent         INTEGER NOT NULL DEFAULT 0,  -- strong signal, no posting yet
    signal_id         INTEGER REFERENCES market_signals(id) ON DELETE SET NULL,

    score             REAL    NOT NULL DEFAULT 0,
    status            TEXT    NOT NULL DEFAULT 'active',  -- active | aged_out | done | dismissed
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL,
    status_changed_at TEXT,
    note              TEXT,

    -- Placeholders for the deferred warm-intro phase (spec 3.3 item 3). Kept
    -- null in phase 1; no code reads them yet.
    connector_name    TEXT,
    connector_context TEXT
);

CREATE INDEX IF NOT EXISTS idx_targets_status  ON networking_targets(status, score);
CREATE INDEX IF NOT EXISTS idx_targets_company ON networking_targets(company);


-- ---------------------------------------------------------------------------
-- Housekeeping
-- ---------------------------------------------------------------------------

-- Small key/value store for things like "when did we last refresh resources".
CREATE TABLE IF NOT EXISTS app_state (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT NOT NULL
);

-- Every call to the research layer, for cost visibility and debugging.
CREATE TABLE IF NOT EXISTS research_calls (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    purpose        TEXT    NOT NULL,
    model          TEXT,
    input_tokens   INTEGER,
    output_tokens  INTEGER,
    web_searches   INTEGER,
    duration_ms    INTEGER,
    ok             INTEGER NOT NULL DEFAULT 1,
    error          TEXT,
    created_at     TEXT    NOT NULL
);
