"""
TicketGenie - RAG Service (FastAPI)

REST API that suggests resolutions for IT support tickets using
Retrieval-Augmented Generation, and serves the built React frontend.
"""
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

load_dotenv()

from metrics import metrics_tracker  # noqa: E402  (needs env loaded first)
from rag_engine_tfidf import RAGEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TicketGenie RAG Service",
    description="Retrieval-Augmented Generation service for IT ticket resolutions",
    version="1.1.0",
)

# CORS: comma-separated list in CORS_ORIGINS, "*" by default for local development.
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # no cookies are used; "*" + credentials is not allowed by browsers
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

try:
    rag_engine: Optional[RAGEngine] = RAGEngine()
    logger.info("RAG Engine initialized successfully")
except Exception as e:
    logger.error("Failed to initialize RAG engine: %s", e)
    rag_engine = None


# ----------------------------------------------------------------- models
class TicketRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    priority: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=5, max_length=2000)

    @field_validator("category", "priority", "description")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class SimilarTicket(BaseModel):
    ticket_id: Optional[str] = None
    category: str
    description: str
    resolution: str
    priority: Optional[str] = None
    similarity_score: float


class Timing(BaseModel):
    search_time_ms: float
    generation_time_ms: float
    total_time_ms: float


class ResolutionResponse(BaseModel):
    suggested_resolution: str
    confidence: float
    similar_tickets: List[SimilarTicket]
    method: str
    timing: Optional[Timing] = None
    metadata: Optional[Dict] = None


class FeedbackRequest(BaseModel):
    feedback: str = Field(default="", max_length=1000)
    helpful: Optional[bool] = None


def _require_engine() -> RAGEngine:
    if not rag_engine or not rag_engine.is_ready():
        raise HTTPException(
            status_code=503,
            detail="RAG engine not ready. Check that backend/data/demo_tickets.xlsx exists "
            "(run: python scripts/generate_demo_dataset.py).",
        )
    return rag_engine


# -------------------------------------------------------------- endpoints
@app.get("/api")
def api_info():
    """API information endpoint."""
    return {
        "service": "TicketGenie RAG Service",
        "version": app.version,
        "status": "running" if rag_engine and rag_engine.is_ready() else "initializing",
        "endpoints": {
            "suggest_resolution": "POST /api/suggest-resolution",
            "categories": "GET /api/categories",
            "feedback": "POST /api/feedback/{ticket_id}",
            "health": "GET /health",
            "stats": "GET /api/stats",
            "metrics": "GET /api/metrics",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
def health_check():
    """Health check used by the deployment platform."""
    engine = _require_engine()
    return {
        "status": "healthy",
        "knowledge_base_size": engine.get_knowledge_base_size(),
        "ai_available": engine.has_ai_client(),
    }


# Declared as a plain "def" so FastAPI runs it in a worker thread:
# the (slow) AI call does not block other requests.
@app.post("/api/suggest-resolution", response_model=ResolutionResponse)
def suggest_resolution(request: TicketRequest):
    """Suggest a resolution for a ticket (category, priority, description)."""
    engine = _require_engine()
    try:
        result = engine.suggest_resolution(
            category=request.category,
            priority=request.priority,
            description=request.description,
        )
        return ResolutionResponse(**result)
    except Exception as e:
        logger.exception("Error suggesting resolution")
        metrics_tracker.record_error(request.category)
        raise HTTPException(status_code=500, detail=f"Failed to generate resolution: {e}") from e


@app.post("/api/feedback/{ticket_id}")
def submit_feedback(ticket_id: str, request: FeedbackRequest):
    """Record whether a suggested resolution was helpful (kept in memory, shown in /api/metrics)."""
    if not request.feedback.strip() and request.helpful is None:
        raise HTTPException(status_code=422, detail="Provide feedback text or a helpful rating")
    metrics_tracker.record_feedback(ticket_id[:50], request.feedback.strip(), request.helpful)
    return {"status": "success", "message": "Thank you for your feedback"}


@app.get("/api/categories")
def get_categories():
    """Ticket categories present in the knowledge base (used by the form dropdown)."""
    return {"categories": _require_engine().get_categories()}


@app.get("/api/stats")
def get_stats():
    """Statistics about the knowledge base."""
    engine = _require_engine()
    return {
        "total_tickets": engine.get_knowledge_base_size(),
        "top_categories": engine.get_top_categories(),
        "ai_available": engine.has_ai_client(),
        "dataset": engine.loaded_from.name if engine.loaded_from else None,
        "service_status": "operational",
    }


@app.post("/api/reload-knowledge-base")
def reload_knowledge_base(x_admin_token: Optional[str] = Header(default=None)):
    """Reload the dataset from disk. Requires the X-Admin-Token header to match ADMIN_TOKEN."""
    admin_token = os.getenv("ADMIN_TOKEN", "").strip()
    if not admin_token:
        raise HTTPException(status_code=403, detail="Reload is disabled (ADMIN_TOKEN not configured)")
    if x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    engine = _require_engine()
    try:
        engine.reload_knowledge_base()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed, previous knowledge base kept: {e}") from e
    return {
        "status": "success",
        "message": "Knowledge base reloaded successfully",
        "total_tickets": engine.get_knowledge_base_size(),
    }


@app.get("/api/metrics")
def get_metrics():
    """Performance and quality metrics since the service started."""
    return metrics_tracker.get_summary()


@app.get("/api/metrics/realtime")
def get_realtime_metrics():
    """Metrics for the last 100 queries."""
    return metrics_tracker.get_realtime_stats()


# ------------------------------------------------- serve built frontend
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.isdir(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        """Serve the React single-page app for every non-API route."""
        if full_path.startswith("api") or full_path in ("health", "docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        requested = os.path.normpath(os.path.join(frontend_dist, full_path))
        if full_path and requested.startswith(os.path.normpath(frontend_dist)) and os.path.isfile(requested):
            return FileResponse(requested)  # e.g. /vite.svg, /favicon.ico
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    logger.warning("Frontend build not found at %s (run 'npm run build' in frontend/)", frontend_dist)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting RAG Service on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
