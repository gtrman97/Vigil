from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from app.database import Base, engine
from app import models

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

    results = []

    for path, methods in spec.get("paths", {}).items():
        if "get" not in methods:
            continue

        resolved_path = path
        for param in methods["get"].get("parameters", []):
            if param.get("in") == "path":
                resolved_path = resolved_path.replace(f"{{{param['name']}}}", "1")

        url = base_url + resolved_path

        try:
            response = httpx.get(url, timeout=10.0)
            results.append({
                "endpoint": path,
                "method": "GET",
                "status_code": response.status_code,
            })
        except httpx.HTTPError as e:
            results.append({
                "endpoint": path,
                "method": "GET",
                "status_code": None,
                "error": str(e),
            })

    return {"tested": len(results), "results": results}