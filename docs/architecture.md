# Architecture

ProofLens is split into a web desk and an API. The desk is where a person writes a research question. The API checks that question, stores it, and is the only part of the system allowed to talk to the database.

```
Browser  ->  Next.js desk  ->  FastAPI  ->  PostgreSQL
                                 |
                                 research_questions
```

Nothing in this milestone calls a language model. A question moves from the form to a row in `research_questions` and back to the history list. Its status is `submitted`.

## Backend

`backend/main.py` is the process entry point. The application itself is built in `backend/app/main.py`.

- `app/core/config.py` reads settings with Pydantic. Environment variables override the root `.env` file.
- `app/core/logging.py` configures one text log format. The database URL is never written to the log, because it can contain a password.
- `app/core/database.py` opens SQLAlchemy. Route functions are ordinary `def` functions, not `async def`. The database driver blocks, and FastAPI runs a normal function in a worker thread so the event loop stays free.
- `app/api` holds HTTP routes. `app/services` holds the rules for a valid question and for saving it. `app/schemas` is the JSON contract.

Routes:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Reports whether the process and the database are up |
| GET | `/api/research` | Lists saved questions, newest first |
| POST | `/api/research` | Saves one question |
| GET | `/api/research/{id}` | Reads one saved question |

`GET /api/health` returns `200` with `"status": "ok"` when PostgreSQL answers `SELECT 1`. It returns `503` with `"status": "degraded"` when the database does not answer. The process stays up either way, so the desk can show the real state.

Other database failures return `503` and a short message. Validation problems return `422`. A missing question returns `404`. Unexpected errors return `500`. The response body does not include the Python traceback.

## Data

One table, `research_questions`:

- `id` — UUID
- `question` — the text the person wrote, trimmed, 10 to 2000 characters
- `status` — `submitted`
- `created_at`, `updated_at` — UTC timestamps

The readable SQL is `database/schema.sql`. SQLAlchemy creates the same table on startup when the database is reachable. There is no second copy of the data in the browser.

Tests point `DATABASE_URL` at in-memory SQLite before the app is imported. That exercises the API and the model without a PostgreSQL server. It is not a second production database.

## Frontend

The Next.js app is a desk, not a chat transcript.

- `/` is the composer and the five most recent questions.
- `/history` is the longer list.
- `lib/api.ts` is the only place that calls the backend.
- The header polls `/api/health` and shows whether the API and the database are actually reachable.

The interface says when research has not run. It does not show sample reports or agent activity.

## Deliberately not here

Agents, LangGraph, tool calling, retrieval, citations, contradiction checks, human review, evaluation, MCP, and deployment packaging belong to later milestones. They are not stubbed as if they already worked.
