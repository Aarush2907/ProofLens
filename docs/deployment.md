# Deployment

This describes a practical way to run ProofLens. It is not a record of a deployment. Nothing in this repository was deployed to a public host as part of the current release, and a public URL has not been verified.

## Shape

Keep one machine for the API, PostgreSQL, and Qdrant. Put the Next.js desk on that same machine, or on a static host only if you rebuild it with a browser-reachable `NEXT_PUBLIC_API_URL`. The browser cannot use a Docker name such as `http://backend:8000`.

```
Browser --HTTPS--> Next.js (port 3000)
Browser --HTTPS--> FastAPI (port 8000)
FastAPI --> PostgreSQL
FastAPI --> Qdrant HTTP
FastAPI --> MCP server over stdio (same container or process)
FastAPI --> OpenAI and Tavily, when keys are set
```

The MCP server is not a separate service. The API starts it. A second container that also opened a local Qdrant path would fight over the file lock, so Compose sets `QDRANT_URL` and leaves `QDRANT_PATH` empty.

## Cost

A small VPS with 2 GB of RAM can run Compose for a portfolio: Postgres, Qdrant, the API, and the desk. The embedding model is downloaded once into the `embedding_cache` volume. Model and search bills depend on how many questions you run. `MAX_RUN_COST_USD`, `MAX_CONCURRENT_RUNS`, and `MAX_RUN_STARTS` are there to stop a loop from spending without a limit. The stored cost is an estimate from the prices in the environment, not the provider invoice.

Managed Postgres and managed Qdrant are optional. They cost more and are worth it when you need backups and a host you do not administer. The API only needs `DATABASE_URL` and `QDRANT_URL` changed.

## Environment

Copy the variables from `.env.example`. On the server, set them in the process environment or a file that is not in the image.

- `DATABASE_URL` must use the production user and password. The Compose file's `prooflens` password is a local placeholder.
- `OPENAI_API_KEY` and `SEARCH_API_KEY` stay out of the image and out of git.
- `CORS_ORIGINS` must list the desk's public origin.
- `NEXT_PUBLIC_API_URL` is baked in when the frontend image is built. Rebuild the desk if the API origin changes.
- `ENVIRONMENT=production` turns off `/docs`.

## Database

There is no Alembic migration chain. On startup the API runs `create_all` and adds columns that an older `research_questions` table is missing. `database/schema.sql` is the PostgreSQL contract, including those `ALTER` statements. For a new database, starting the API is enough. Take a backup before upgrading an existing one, because `create_all` does not delete or rewrite old columns.

Checkpoints use Postgres when `DATABASE_URL` is a Postgres URL, so a review can resume after the API process restarts. An in-memory checkpoint cannot.

## HTTPS and the domain

Terminate TLS at Caddy, nginx, or the host's load balancer. Point the domain at that proxy. Proxy `/` to the desk and `/api` to the API, or serve the API on a subdomain and set `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` to match. Do not expose Postgres or Qdrant ports on the public interface. Compose publishes them for local use; on a VPS, bind them to localhost or drop the port mappings.

## What has not been done

`docker compose up` was started once on Docker Desktop for Windows and its four services became healthy. It was not run as a verified production deploy. Confirm Docker on the target host, set real secrets, open the health check, run one research question, and download the Markdown and PDF before treating the host as ready.

The Compose file sets health checks on every service, runs the API as a non-root user, and pins Qdrant to v1.20.2 to match the client library. The health checks, the non-root user and the Qdrant tag worked on a local Docker Desktop start. The start and concurrency limits are process-wide, so run one API process or put a rate limit in the proxy.

Bring-your-own-key: Compose sets REQUIRE_USER_KEYS=true, so the host holds no model or search key and pays nothing for visitors' runs. Keys arrive in request headers, so serve the API over TLS or they cross the network in clear text. The per-run cost cap still applies to the visitor's key.
