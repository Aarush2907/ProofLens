from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "database" / "schema.sql"


def test_postgres_schema_matches_the_model():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS research_questions" in schema
    assert "id UUID PRIMARY KEY" in schema
    assert "question TEXT NOT NULL" in schema
    assert "status VARCHAR(32) NOT NULL" in schema
    assert "created_at TIMESTAMPTZ NOT NULL" in schema
    assert "updated_at TIMESTAMPTZ NOT NULL" in schema
    assert "ck_research_questions_question_not_blank" in schema
    assert "ix_research_questions_created_at" in schema
