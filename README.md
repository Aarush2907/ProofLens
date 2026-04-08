# ProofLens

ProofLens is a research desk. You write a question, the API saves it, and the dashboard shows it in your history. Later milestones will add a team of AI agents that research the question, check evidence, and write a cited report. That work is not built yet, and the app does not invent findings to fill the gap.

## What works in this milestone

- A FastAPI backend with configuration, logging, and error responses.
- A health check at `GET /api/health`.
- Saving and listing research questions in PostgreSQL.
- A Next.js dashboard with a research desk, history, and an empty state.
- Backend and frontend tests.

A saved question has the status `submitted`. It does not have sources, claims, or a report.

## What you need installed

- Python 3.11 or newer
- Node.js 20 or newer
- PostgreSQL 15 or newer, running locally

The API still starts if PostgreSQL is down. The health check then reports the database as unavailable, and saving a question returns an error instead of a made-up success.

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

On startup the API creates the `research_questions` table if it can connect. The same structure is written out in `database/schema.sql`.

## Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

The API listens on http://localhost:8000. Interactive docs are at http://localhost:8000/docs while `ENVIRONMENT` is not `production`.

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

## Tests

Backend, from `backend` with the virtual environment active:

```powershell
pytest
```

Those tests use an in-memory SQLite database so they do not need PostgreSQL. The application code still targets PostgreSQL when you run it.

Frontend, from `frontend`:

```powershell
npm test
```

## Layout

```
backend/     FastAPI application, settings, database access, and API tests
frontend/    Next.js research desk
database/    PostgreSQL schema
docs/        Architecture notes for this milestone
```

`explanation.txt` and `scripts/push.ps1` are local files. They are listed in `.gitignore` and are not part of the repository.
