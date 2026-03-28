"""Main FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings, is_databricks_app
from app.database import db
from app.llm import llm
from app.models import HealthResponse
from app.routers import (
    customers_router,
    recommendations_router,
    chat_router,
    admin_router,
)

# Image directory for car photos
def find_images_dir() -> Optional[Path]:
    """Find _images folder."""
    possible_paths = [
        # Databricks Apps: _images is at root level
        Path(__file__).parent.parent.parent.parent / "_images",
        Path.cwd() / "_images",
        Path.cwd().parent / "_images",
    ]
    for path in possible_paths:
        if path.exists():
            print(f"Found images at: {path}")
            return path
    print("Images directory not found")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting IDOM Car AI Backend...")
    await db.initialize()
    llm.initialize()
    print("Initialization complete")

    yield

    # Shutdown
    print("Shutting down...")
    await db.close()


# Create FastAPI application
app = FastAPI(
    title="IDOM Car AI API",
    description="AI-powered vehicle recommendation system for IDOM sales teams",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customers_router)
app.include_router(recommendations_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        database="demo" if db.is_demo_mode else "connected",
        llm="demo" if llm.is_demo_mode else "connected",
    )


@app.get("/api/debug/db")
async def debug_db():
    """Temporary debug endpoint to diagnose DB connection."""
    import os, httpx
    result = {
        "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST", "NOT SET"),
        "DATABRICKS_TOKEN": "SET" if os.environ.get("DATABRICKS_TOKEN") else "NOT SET",
        "DATABRICKS_CLIENT_ID": "SET" if os.environ.get("DATABRICKS_CLIENT_ID") else "NOT SET",
        "DATABRICKS_APP_NAME": os.environ.get("DATABRICKS_APP_NAME", "NOT SET"),
        "warehouse_id": db._warehouse_id,
        "host": db._host,
        "demo_mode": db._demo_mode,
        "initialized": db._initialized,
        "auth_headers": {},
        "query_result": None,
        "query_error": None,
    }
    # Test auth
    try:
        headers = db._get_auth_headers()
        result["auth_headers"] = {k: v[:20] + "..." if len(v) > 20 else v for k, v in headers.items()}
    except Exception as e:
        result["auth_error"] = str(e)
    # Test basic query
    try:
        rows = await db.execute_query("SELECT 1 AS test")
        result["query_result"] = rows
    except Exception as e:
        result["query_error"] = str(e)
    # Test actual insights query for C001
    try:
        from app.config import get_full_table_name
        insights_table = get_full_table_name("customer_insights")
        insights_rows = await db.execute_query(
            f"SELECT customer_id, persona_summary, deep_needs FROM {insights_table} WHERE customer_id = 'C001' LIMIT 1"
        )
        result["insights_query_result"] = insights_rows
        result["insights_query_count"] = len(insights_rows)
    except Exception as e:
        result["insights_query_error"] = str(e)
    # Check DEMO_MODE env var
    result["DEMO_MODE_env"] = os.environ.get("DEMO_MODE", "NOT SET")
    # Test recommendations query for all customers
    try:
        from app.config import get_full_table_name
        rec_table = get_full_table_name("recommendations")
        rec_rows = await db.execute_query(
            f"SELECT customer_id, LENGTH(recommendations_json) as json_len FROM {rec_table} ORDER BY customer_id"
        )
        result["rec_table_rows"] = rec_rows
    except Exception as e:
        result["rec_table_error"] = str(e)
    # Test actual C001 parse
    try:
        import json as _json
        rec_rows2 = await db.execute_query(
            f"SELECT recommendations_json FROM {rec_table} WHERE customer_id = 'C001' LIMIT 1"
        )
        if rec_rows2:
            parsed = _json.loads(rec_rows2[0]["recommendations_json"])
            result["c001_rec_count"] = len(parsed)
            result["c001_rec_models"] = [r["vehicle"]["model"] for r in parsed]
        else:
            result["c001_rec_count"] = "EMPTY - no rows returned"
    except Exception as e:
        result["c001_rec_error"] = str(e)
    return result


# Mount images directory
_images_dir = find_images_dir()
if _images_dir:
    app.mount("/api/images", StaticFiles(directory=str(_images_dir)), name="images")
    print(f"Images mounted at /api/images from {_images_dir}")


# Find frontend dist path
def find_frontend_dist() -> Optional[Path]:
    """Find frontend dist folder."""
    possible_paths = [
        # Databricks Apps: dist is at root level (same level as backend/)
        Path(__file__).parent.parent.parent / "dist",
        Path.cwd() / "dist",
        # Local development: frontend/dist
        Path(__file__).parent.parent.parent / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
    ]
    for path in possible_paths:
        print(f"Checking frontend path: {path}")
        if path.exists() and (path / "index.html").exists():
            print(f"Found frontend at: {path}")
            return path
    print("Frontend dist not found in any location")
    return None


# Set up frontend serving
_frontend_dist = find_frontend_dist()

if _frontend_dist:
    # Mount static assets
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")
        print("Static assets mounted at /assets")

    # Serve SPA for all non-API routes (including root)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for all non-API routes."""
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"error": "Frontend not built"}, 404

    print("SPA catch-all route configured")
else:
    # Fallback: API-only mode
    @app.get("/")
    async def root():
        """Root endpoint when frontend is not available."""
        return {
            "message": "IDOM Car AI API",
            "docs": "/docs",
            "health": "/api/health",
        }
    print("Running in API-only mode (no frontend)")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    port = int(os.environ.get("PORT", settings.port))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
    )
