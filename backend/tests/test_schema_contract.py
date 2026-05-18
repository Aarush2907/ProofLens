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
    assert "CREATE TABLE IF NOT EXISTS research_sources" in schema
    assert "CREATE TABLE IF NOT EXISTS research_claims" in schema
    assert "CREATE TABLE IF NOT EXISTS research_verifications" in schema
    assert "CREATE TABLE IF NOT EXISTS research_contradictions" in schema
    assert "CREATE TABLE IF NOT EXISTS research_reports" in schema
    assert "CREATE TABLE IF NOT EXISTS research_evidence" in schema
    assert "review_status VARCHAR(32)" in schema
    assert "published_on TEXT" in schema
    assert "stage VARCHAR(32)" in schema
    assert "error_message TEXT" in schema
