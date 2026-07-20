# Vigil

Automated API testing tool. Upload an OpenAPI spec, and Vigil generates requests against every endpoint, validates responses against the schema, measures response times, and logs every run to Postgres, with a simple HTML report summarizing results.

## Why I built this

As a QA/SDET-focused engineer, I wanted a tool that goes beyond writing individual API tests by hand: one that can take any OpenAPI spec and automatically generate and validate a full test run against it, then track results over time in a real database rather than a one-off console output.

## Tech Stack

- **FastAPI** — backend/API framework
- **PostgreSQL** — stores test run history and results
- **SQLAlchemy** — database ORM
- **Pydantic** — request/response and schema validation
- **httpx** — sends generated API requests
- **pytest** — automated tests for Vigil itself
- **Docker Compose** — app + database, one command to run
- **GitHub Actions** — CI, scheduled test runs

## How it works

1. Upload an OpenAPI (Swagger) spec
2. Vigil parses the spec and auto-generates requests for each endpoint
3. Requests are sent via `httpx`, and responses are validated against the spec's schemas using Pydantic
4. Every run (endpoint, status, response time, pass/fail, schema violations) is logged to Postgres
5. An HTML report summarizes the results

## Getting Started

\`\`\`bash
git clone https://github.com/<your-username>/vigil.git
cd vigil
docker compose up
\`\`\`

The app will be available at `http://localhost:8000`.

## Roadmap

- [ ] JWT authentication
- [ ] CSV export of results
- [ ] Breaking-change detection between spec versions
- [ ] React dashboard
- [ ] File upload UI (currently API-only)

## License

MIT
