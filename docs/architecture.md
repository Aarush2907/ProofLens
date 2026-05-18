# Architecture

ProofLens is split into a web desk and an API. The desk is where a person writes a research question. The API stores the question, runs five agents, and is the only part of the system allowed to talk to the database.

```
Browser
  -> Next.js desk
  -> POST /api/research
  -> FastAPI saves the question and starts the graph
  -> Researcher searches Tavily and fetches pages
  -> Extractor, fact-checker, contradiction detector
  -> Pause for claim review (LangGraph checkpoint, thread id = question id)
  -> POST /api/research/{id}/review
  -> Writer
  -> PostgreSQL
  -> GET /api/research/{id} and GET /api/research/{id}/graph
```

The HTTP request returns as soon as the question is saved with status `running`. The graph keeps writing intermediate rows. The desk does not invent a stage that the API has not saved.

## The five agents

Each agent is a function in its own module under `backend/app/research/agents`. They share one typed state and run in this order:

1. **Researcher** plans one or two search queries, calls the search API, drops duplicate URLs, and fetches page text when a page answers.
2. **Extractor** reads those passages and returns claims tied to a retrieved URL. Opinions are labelled and kept separate from factual claims.
3. **Fact-checker** reads each factual claim beside its passage. A verdict of Verified or Partially supported is kept only when a supporting excerpt actually appears in that passage. An opinion is recorded as Insufficient evidence without being treated as a fact.
4. **Contradiction detector** compares factual claims from different sources. A different publication date, or a different definition, is not stored as a contradiction.
5. **Review** pauses the graph. The person approves or rejects each claim, or sends the researcher back with a note. A rejected claim stays on the run and is left out of the report. The checkpoint thread id is the question id, so two sessions do not resume each other.
6. **Writer** drafts a report from the approved claims, verdicts, and disagreements. A citation that was not retrieved is removed. A finding left with no citation moves into the limitations.

If search returns nothing, or no claim survives, the graph still reaches review and then the writer with that empty result instead of inventing sources. A missing API key stops the run. A temporary search or model failure is tried once more, then the run is marked failed.

Source quality is computed from the saved domain, author, publication date, and passage. The reasons are shown beside the label. There is no numeric reliability score, and a primary-style label does not mean a claim is verified.

## Backend

`backend/main.py` is the process entry point. The application itself is built in `backend/app/main.py`.

- `app/core/config.py` reads settings with Pydantic. Environment variables override the root `.env` file. Model name, base URL, search provider, and the attempt limit live there.
- `app/core/logging.py` configures one text log format. The database URL is never written to the log, because it can contain a password.
- `app/core/database.py` opens SQLAlchemy. Route functions are ordinary `def` functions, not `async def`. The database driver blocks, and FastAPI runs a normal function in a worker thread so the event loop stays free.
- `app/research/graph.py` builds the LangGraph workflow. `app/research/runner.py` streams it and saves each snapshot. `app/research/model.py` calls the chat API. `app/research/search.py` calls Tavily.
- `app/api` holds HTTP routes. `app/services` loads a saved run. `app/schemas` is the JSON contract.

Routes:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Reports whether the process and the database are up |
| GET | `/api/research` | Lists saved questions, newest first |
| POST | `/api/research` | Validates a question, saves it, and starts the workflow |
| GET | `/api/research/{id}` | Reads one run, including sources, claims, evidence, checks, disagreements, and the report |
| GET | `/api/research/{id}/graph` | Reads the evidence graph built from those rows |
| POST | `/api/research/{id}/review` | Approves or rejects claims, or asks for another search |

`GET /api/health` returns `200` with `"status": "ok"` when PostgreSQL answers `SELECT 1`. It returns `503` with `"status": "degraded"` when the database does not answer. The process stays up either way, so the desk can show the real state.

Other database failures return `503` and a short message. Validation problems return `422`. A missing question returns `404`. Unexpected errors return `500`. The response body does not include the Python traceback. A failed research run is still a successful HTTP read: the question row has status `failed` and a short `error_message` that does not include the raw provider response.

## Data

`research_questions` holds the question, status (`submitted`, `running`, `completed`, `failed`), stage, and error message.

Child rows are replaced each time a step saves:

- `research_sources` — original URL, domain, title, author, publication date when retrieved, retrieval time, snippet, and page text
- `research_claims` — claim text, category, source id, source URL, and review status
- `research_verifications` — status, explanation, and the excerpts used
- `research_evidence` — one supporting or opposing passage, tied to the claim and the source URL
- `research_contradictions` — the two claims and why they disagree
- `research_reports` — summary, findings, uncertainties, and limitations

The readable SQL is `database/schema.sql`. SQLAlchemy creates the same tables on startup when the database is reachable, and adds the new question columns if an older table is already there. There is no second copy of the data in the browser.

Tests point `DATABASE_URL` at in-memory SQLite before the app is imported. That exercises the API and the model without a PostgreSQL server. It is not a second production database. The graph tests replace search and the model with fixtures. `pytest -m e2e` is the test that calls the configured APIs, and it skips when the keys are absent.

## Frontend

The Next.js app is a desk, not a chat transcript.

- `/` is the composer and the five most recent questions.
- `/history` is the longer list. Each question links to its run.
- `/research/[id]` shows the review form, evidence graph, sources, claims, verification, contradictions, and report. It reloads while the status is `running`. The graph is loaded from `GET /api/research/{id}/graph`.
- `lib/api.ts` is the only place that calls the backend.
- The header polls `/api/health` and shows whether the API and the database are actually reachable.

Empty lists stay empty. The page does not draw an agent checklist or sample findings.

## Deliberately not here

Vector retrieval, a human review pause, evaluation scores, MCP tools, and deployment packaging belong to later milestones. They are not stubbed as if they already worked.
