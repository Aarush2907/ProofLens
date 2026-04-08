-- ProofLens milestone 1 schema.
--
-- The API also creates this table on startup through SQLAlchemy. This file is
-- the readable PostgreSQL contract, and the names match the model in
-- backend/app/models/research_question.py.
--
-- Apply it with:
--   psql "postgresql://prooflens:prooflens@localhost:5432/prooflens" -f database/schema.sql

CREATE TABLE IF NOT EXISTS research_questions (
    id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_research_questions_question_not_blank CHECK (length(trim(question)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_research_questions_created_at
    ON research_questions (created_at);
