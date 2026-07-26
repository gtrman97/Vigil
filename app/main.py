from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from app.database import Base, engine, SessionLocal
from app import models

from typing import Optional, Tuple

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vigil")


class SpecRequest(BaseModel):
    spec_url: str


def fetch_spec(spec_url: str) -> dict:
    try:
        response = httpx.get(spec_url, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch spec: {e}")

    spec = response.json()

    if "openapi" not in spec or "paths" not in spec:
        raise HTTPException(status_code=400, detail="URL does not point to a valid OpenAPI spec")

    return spec

def validate_response(operation: dict, response: httpx.Response) -> Tuple[bool, Optional[str]]:
    documented_responses = operation.get("responses", {})
    status_str = str(response.status_code)

    if status_str not in documented_responses:
        return False, f"Status code {response.status_code} not documented in spec"

    response_spec = documented_responses[status_str]
    content = response_spec.get("content", {})
    json_content = content.get("application/json")

    if not json_content:
        return True, None

    expected_type = json_content.get("schema", {}).get("type")
    if not expected_type:
        return True, None

    try:
        body = response.json()
    except ValueError:
        return False, "Response body is not valid JSON"

    if isinstance(body, dict):
        actual_type = "object"
    elif isinstance(body, list):
        actual_type = "array"
    else:
        actual_type = type(body).__name__

    if expected_type != actual_type:
        return False, f"Expected response type '{expected_type}', got '{actual_type}'"

    return True, None

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/specs")
def upload_spec(request: SpecRequest):
    spec = fetch_spec(request.spec_url)
    return {
        "title": spec.get("info", {}).get("title", "unknown"),
        "version": spec.get("info", {}).get("version", "unknown"),
        "endpoint_count": len(spec.get("paths", {})),
    }


@app.post("/run-tests")
def run_tests(request: SpecRequest):
    spec = fetch_spec(request.spec_url)
    servers = spec.get("servers", [])
    if not servers:
        raise HTTPException(status_code=400, detail="Spec has no server URL defined")
    base_url = servers[0]["url"]
    if not base_url.startswith("http"):
        origin = httpx.URL(request.spec_url)
        base_url = f"{origin.scheme}://{origin.host}{base_url}"

    db = SessionLocal()
    results = []

    try:
        for path, methods in spec.get("paths", {}).items():
            if "get" not in methods:
                continue

            operation = methods["get"]
            resolved_path = path
            for param in operation.get("parameters", []):
                if param.get("in") == "path":
                    resolved_path = resolved_path.replace(f"{{{param['name']}}}", "1")

            url = base_url + resolved_path

            try:
                response = httpx.get(url, timeout=10.0)
                passed, error_message = validate_response(operation, response)
                status_code = response.status_code
            except httpx.HTTPError as e:
                passed = False
                error_message = str(e)
                status_code = 0

            result_row = models.TestResult(
                endpoint=path,
                method="GET",
                status_code=status_code,
                passed=passed,
                error_message=error_message,
            )
            db.add(result_row)

            results.append({
                "endpoint": path,
                "method": "GET",
                "status_code": status_code,
                "passed": passed,
                "error_message": error_message,
            })

        db.commit()
    finally:
        db.close()

    return {"tested": len(results), "results": results}