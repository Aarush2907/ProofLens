# Tests

Backend tests live in `backend/tests`. Frontend tests live in `frontend/tests`.

`pytest` covers the agents, the shared-state checks, the graph, the API, and database persistence with stand-ins for search and the model. `pytest -m e2e` is the live path and skips unless `OPENAI_API_KEY` and `SEARCH_API_KEY` are set. `python -m app.research.live` from `backend` runs one real question and prints the saved report.

This directory does not start both applications together. The desk is checked against the API during local verification, and the automated suites cover the contracts those two sides share.
