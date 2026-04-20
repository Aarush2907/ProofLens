-- ProofLens research schema.
--
-- The API creates the same tables on startup. This file is the PostgreSQL
-- contract. Columns added after milestone 1 are also applied with ALTER so an
-- existing research_questions table can be updated.

CREATE TABLE IF NOT EXISTS research_questions (
    id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    stage VARCHAR(32) NOT NULL DEFAULT 'submitted',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_research_questions_question_not_blank CHECK (length(trim(question)) > 0)
);

ALTER TABLE research_questions ADD COLUMN IF NOT EXISTS stage VARCHAR(32) DEFAULT 'submitted';
ALTER TABLE research_questions ADD COLUMN IF NOT EXISTS error_message TEXT;

CREATE INDEX IF NOT EXISTS ix_research_questions_created_at
    ON research_questions (created_at);

CREATE TABLE IF NOT EXISTS research_sources (
    id UUID PRIMARY KEY,
    research_question_id UUID NOT NULL REFERENCES research_questions (id),
    position INTEGER NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    search_query TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_research_sources_question
    ON research_sources (research_question_id);

CREATE TABLE IF NOT EXISTS research_claims (
    id UUID PRIMARY KEY,
    research_question_id UUID NOT NULL REFERENCES research_questions (id),
    position INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    text TEXT NOT NULL,
    kind VARCHAR(32) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_research_claims_question
    ON research_claims (research_question_id);

CREATE TABLE IF NOT EXISTS research_verifications (
    id UUID PRIMARY KEY,
    research_question_id UUID NOT NULL REFERENCES research_questions (id),
    claim_id UUID NOT NULL REFERENCES research_claims (id),
    status VARCHAR(32) NOT NULL,
    explanation TEXT NOT NULL DEFAULT '',
    supporting_excerpt TEXT NOT NULL DEFAULT '',
    opposing_excerpt TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_research_verifications_question
    ON research_verifications (research_question_id);

CREATE TABLE IF NOT EXISTS research_contradictions (
    id UUID PRIMARY KEY,
    research_question_id UUID NOT NULL REFERENCES research_questions (id),
    claim_id UUID NOT NULL,
    other_claim_id UUID NOT NULL,
    explanation TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_research_contradictions_question
    ON research_contradictions (research_question_id);

CREATE TABLE IF NOT EXISTS research_reports (
    id UUID PRIMARY KEY,
    research_question_id UUID NOT NULL UNIQUE REFERENCES research_questions (id),
    summary TEXT NOT NULL,
    findings JSON NOT NULL,
    uncertainties JSON NOT NULL,
    limitations JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
