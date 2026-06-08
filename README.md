# ProofLens

ProofLens researches a question with five agents, then waits for a person to approve or reject the claims before the report is written. The desk shows the sources, evidence passages, verification, an evidence graph built from the saved rows, and the agent activity from the run itself.

## What works in this milestone

- A FastAPI backend with configuration, logging, and error responses.
- A health check at `GET /api/health`.
- A research workflow: search, extract claims, check them against retrieved passages, and look for disagreements.
- An MCP server the workflow calls over stdio. The tools are `search_web`, `retrieve_source`, `extract_claims`, `verify_claim`, and `search_evidence`.
- Qdrant storage for source passages. The fact-checker can search that store for a claim. Passages keep the source id, original URL, title, and research session.
- Research memory. A fresh copy of a URL is not downloaded again. A passage from an earlier session is returned only when it is similar to the query, and it is labelled with that session. A passage older than the freshness window is marked as possibly outdated.
- A human review checkpoint. You approve or reject each claim, or send the researcher back with a note. The report is written after you continue.
- Source records with the original URL, domain, retrieval time, and publication details when the search result included them.
- Evidence passages linked to the claim and source they were checked against.
- An evidence graph at `GET /api/research/{id}/graph`, drawn in the desk from those saved relationships.
- Live agent activity at `GET /api/research/{id}/events`. The desk shows the agent, the current step, and the event history. The events are written by the running workflow.
- A source record that explains why a page is labelled primary-style, secondary, or unclear. That label is not a reliability score, and it is separate from whether a claim was verified.
- LangGraph checkpoints so a waiting review can be resumed. PostgreSQL keeps the checkpoint across an API restart. Tests use an in-memory checkpoint for the life of the test process.

A question starts as `running`. It stays `running` with stage `awaiting_review` until you continue. It becomes `completed` when a report is saved, or `failed` when a step stops the run.

## What you need installed

- Python 3.11 or newer
- Node.js 20 or newer
- PostgreSQL 15 or newer, running locally
- An OpenAI API key and a Tavily search key, if you want a live research run
- No separate Qdrant installation. The API stores vectors in `.qdrant` unless `QDRANT_URL` is set. The first live retrieval downloads the embedding model.

The API still starts if PostgreSQL is down. The health check then reports the database as unavailable, and saving a question returns an error instead of a made-up success.

Automated tests do not call OpenAI or Tavily. A live run is a separate command, and it skips when the keys are missing.

## Configure

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env` if your PostgreSQL user, password, or database name differ. Create the database before the first real save:

```sql
CREATE USER prooflens WITH PASSWORD 'prooflens';
CREATE DATABASE prooflens OWNER prooflens;
```

The password in `.env.example` is a local placeholder. Change it if anyone else can reach that database.

For a live run, set these in `.env`. Leave them empty if you only want to save questions and run the automated tests.

```
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
SEARCH_PROVIDER=tavily
SEARCH_API_KEY=
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
QDRANT_URL=
QDRANT_PATH=
```

`OPENAI_MODEL` chooses the chat model. `EMBEDDING_MODEL` chooses the vector model and is not the chat model. `OPENAI_BASE_URL` is optional and is there so a compatible endpoint can be used later without rewriting the agents. `SEARCH_PROVIDER` is `tavily` today. Leave `QDRANT_URL` empty to use the local `.qdrant` directory.

On startup the API creates the research tables if it can connect, and adds `stage` and `error_message` to an older `research_questions` table. The same structure is written out in `database/schema.sql`.

## Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

The API listens on http://localhost:8000. Interactive docs are at http://localhost:8000/docs while `ENVIRONMENT` is not `production`.

`POST /api/research` saves the question and starts the workflow in the background. The API starts the MCP tool server for that run. The run pauses after claims are checked. `POST /api/research/{id}/review` approves or rejects those claims, or asks for another search. `GET /api/research/{id}` returns the sources, claims, evidence, contradictions, and report saved so far. `GET /api/research/{id}/graph` returns the nodes and edges for the evidence graph. `GET /api/research/{id}/events` streams the agent activity.

## Run the frontend

In a second terminal, from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The desk calls http://localhost:8000. To point it somewhere else, create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start research from the desk. The run page reloads while the status is `running` and shows only the rows the API has saved. The activity panel follows the event stream and reconnects if the stream drops. When the stage is `awaiting_review`, approve or reject every claim, then continue. The graph and the claim cards use the same saved passages.

## Tests

Backend, from `backend` with the virtual environment active:

```powershell
pytest
```

Those tests use an in-memory SQLite database, an in-memory Qdrant store, a hashing embedder, and stand-ins for search and the model. They do not need PostgreSQL, OpenAI, Tavily, or a downloaded embedding model. One test starts the MCP server as a subprocess. The application code still targets PostgreSQL and fastembed when you run it.

To call the real APIs once, from `backend`:

```powershell
pytest -m e2e
python -m app.research.live "What evidence links consistent sleep to memory consolidation in adults?"
```

`pytest -m e2e` skips unless both `OPENAI_API_KEY` and `SEARCH_API_KEY` are set. The live command prints the saved sources, claims, checks, disagreements, and report as JSON. It exits with an error if a key is missing or a step fails. It does not fill in a report when the tools fail.

Frontend, from `frontend`:

```powershell
npm test
```

## Layout

```
backend/app/research/   LangGraph workflow, the five agents, review checkpoint, search, retrieval, and persistence
backend/app/mcp/       MCP server, tool schemas, and the stdio client
backend/               FastAPI application, settings, database access, and API tests
frontend/              Next.js research desk
database/              PostgreSQL schema
docs/                  Architecture notes
```

`explanation.txt` and `scripts/push.ps1` are local files. They are listed in `.gitignore` and are not part of the repository.

## Not in this milestone

Evaluation scores and deployment packaging come later. They are not stubbed as if they already worked. The review step is the claim checkpoint before the report, not a scored evaluation. Source-quality labels are still not a reliability score.
