# ProofLens

ProofLens researches a question with five agents. You write the question, the API starts a LangGraph workflow, and the desk shows the sources, claims, checks, disagreements, and report that the run actually saved.

## What works in this milestone

- A FastAPI backend with configuration, logging, and error responses.
- A health check at `GET /api/health`.
- A research workflow: search, extract claims, check them against retrieved passages, look for disagreements, and write a cited report.
- Saving each step of a run in PostgreSQL.
- A Next.js desk that starts a run and opens the saved result. It does not invent sources or a report.

A question starts as `running`. It becomes `completed` when a report is saved, or `failed` when a step stops the run. Older rows may still say `submitted` if they were saved before this workflow existed.

## What you need installed

- Python 3.11 or newer
- Node.js 20 or newer
- PostgreSQL 15 or newer, running locally
- An OpenAI API key and a Tavily search key, if you want a live research run

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
```

`OPENAI_MODEL` chooses the chat model. `OPENAI_BASE_URL` is optional and is there so a compatible endpoint can be used later without rewriting the agents. `SEARCH_PROVIDER` is `tavily` today.

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

`POST /api/research` saves the question and starts the workflow in the background. `GET /api/research/{id}` returns the sources, claims, verification, contradictions, and report saved so far.

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

Start research from the desk. The run page reloads while the status is `running` and shows only the rows the API has saved.

## Tests

Backend, from `backend` with the virtual environment active:

```powershell
pytest
```

Those tests use an in-memory SQLite database and stand-ins for search and the model. They do not need PostgreSQL, OpenAI, or Tavily. The application code still targets PostgreSQL when you run it.

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
backend/app/research/   LangGraph workflow, the five agents, search, and persistence
backend/               FastAPI application, settings, database access, and API tests
frontend/              Next.js research desk
database/              PostgreSQL schema
docs/                  Architecture notes
```

`explanation.txt` and `scripts/push.ps1` are local files. They are listed in `.gitignore` and are not part of the repository.

## Not in this milestone

Vector retrieval, a human review step, evaluation scores, MCP tools, and deployment packaging come later. They are not stubbed as if they already worked.
