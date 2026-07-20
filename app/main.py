from fastapi import FastAPI

app = FastAPI(title="Vigil")


@app.get("/health")
def health_check():
    return {"status": "ok"}