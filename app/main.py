from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from app.database import Base, engine
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vigil")


class SpecRequest(BaseModel):
    spec_url: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/specs")
def upload_spec(request: SpecRequest):
    try:
        response = httpx.get(request.spec_url, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch spec: {e}")

    spec = response.json()

    if "openapi" not in spec or "paths" not in spec:
        raise HTTPException(status_code=400, detail="URL does not point to a valid OpenAPI spec")

    return {
        "title": spec.get("info", {}).get("title", "unknown"),
        "version": spec.get("info", {}).get("version", "unknown"),
        "endpoint_count": len(spec.get("paths", {})),
    }