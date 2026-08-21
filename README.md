# Vigil

Automated API contract-testing tool. Point Vigil at a live OpenAPI spec URL, and it generates requests against every documented GET endpoint, validates the responses against the spec's full JSON Schema contract, logs every run to Postgres, and produces a simple HTML report summarizing results.

## Why I built this

I wanted a tool that goes beyond writing individual API tests by hand: one that can take any OpenAPI spec and automatically generate and validate a full test run against it, then track results over time in a real database rather than a one-off console output.

## Live Demo

🔗 [https://vigil-production-51f6.up.railway.app/report](https://vigil-production-51f6.up.railway.app/report)

## Tech Stack

- **FastAPI** — backend/API framework
- **PostgreSQL** — stores test run history and results
- **SQLAlchemy** — database ORM
- **Pydantic** — request body validation
- **jsonschema** — full JSON Schema validation of API responses against the spec's contract
- **httpx** — sends generated API requests
- **Jinja2** — renders the HTML report
- **pytest** — automated tests for Vigil itself
- **Docker Compose** — app + database, one command to run
- **GitHub Actions** — CI on every push, plus a scheduled daily test run against a live public API

## How it works

1. Give Vigil the URL of a public OpenAPI (Swagger) spec via `POST /specs`
2. Vigil fetches and parses the spec, auto-generating a request for each documented **GET** endpoint (path parameters are filled with placeholder values)
3. Requests are sent via `httpx` against the real live API
4. Each response is checked against the spec: is the status code documented, and does the response body fully conform to the documented JSON Schema (required fields, types, and nested structure) using the `jsonschema` library?
5. Every result (endpoint, method, status code, pass/fail, error detail, timestamp) is logged to Postgres
6. `GET /report` renders an HTML summary of all results, color-coded by pass/fail

## Current limitations

- **GET endpoints only** — POST/PUT/DELETE request generation isn't implemented yet (see Roadmap)
- **Path parameters use a fixed placeholder value** rather than real/valid IDs, so some results (e.g. 404s) reflect that rather than an actual API defect

## Getting Started

```bash
git clone https://github.com/gtrman97/Vigil.git
cd Vigil
docker compose up --build
```

Once running, the app is available at `http://localhost:8000`:

```bash
# Fetch and validate a spec
curl -X POST http://localhost:8000/specs \
  -H "Content-Type: application/json" \
  -d '{"spec_url": "https://api.weather.gov/openapi.json"}'

# Run tests against every GET endpoint in the spec
curl -X POST http://localhost:8000/run-tests \
  -H "Content-Type: application/json" \
  -d '{"spec_url": "https://api.weather.gov/openapi.json"}'
```

Then view the results in a browser at `http://localhost:8000/report`.

## Running Tests

Vigil's own test suite runs inside the app container:

```bash
docker exec vigil-app-1 pytest
```

## Roadmap

- [ ] POST/PUT/DELETE request generation
- [ ] JWT authentication
- [ ] CSV export of results
- [ ] Breaking-change detection between spec versions
- [ ] React dashboard
- [ ] Response time measurement
- [ ] AI-assisted test suggestions / failure summaries

## License

MIT