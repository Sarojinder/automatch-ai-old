from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.ml_ranker import model_status
from app.service import DATA_SOURCE, VEHICLES, run_recommendation, vehicle_summaries


WEB_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=12)
    overrides: dict[str, Any] | None = None


app = FastAPI(
    title="AutoMatch AI",
    description="Canada-first AI vehicle recommendation API.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "vehicle_count": len(VEHICLES),
        "data_source": DATA_SOURCE,
        "model": model_status(),
    }


@app.get("/api/model")
def model() -> dict[str, Any]:
    return model_status()


@app.get("/api/vehicles")
def vehicles() -> dict[str, Any]:
    return {"vehicles": vehicle_summaries()}


@app.post("/api/recommend")
def recommend(request: RecommendationRequest) -> dict[str, Any]:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return run_recommendation(query, limit=request.limit, overrides=request.overrides)


@app.post("/recommendations")
def legacy_recommend(request: RecommendationRequest) -> dict[str, Any]:
    return recommend(request)


@app.get("/health")
def legacy_health() -> dict[str, Any]:
    return health()


if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")


@app.get("/", response_model=None)
def index():
    index_file = WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AutoMatch AI API is running. Build the web app to serve the UI."}


@app.get("/{path:path}", response_model=None)
def spa_fallback(path: str):
    requested = WEB_DIST / path
    if requested.exists() and requested.is_file():
        return FileResponse(requested)
    index_file = WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AutoMatch AI API is running."}
