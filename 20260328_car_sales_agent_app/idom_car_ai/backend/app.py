"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from idom_car_ai.backend.config import get_settings
from idom_car_ai.backend.database import db
from idom_car_ai.backend.llm import llm
from idom_car_ai.backend.models import HealthResponse
from idom_car_ai.backend.routers import (
    customers_router,
    recommendations_router,
    chat_router,
    admin_router,
)


def find_images_dir() -> Optional[Path]:
    """Find _images folder."""
    possible_paths = [
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
    print("Starting IDOM Car AI Backend...")
    await db.initialize()
    llm.initialize()
    print("Initialization complete")
    yield
    print("Shutting down...")
    await db.close()


app = FastAPI(
    title="IDOM Car AI API",
    description="AI-powered vehicle recommendation system for IDOM sales teams",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers_router)
app.include_router(recommendations_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        database="demo" if db.is_demo_mode else "connected",
        llm="demo" if llm.is_demo_mode else "connected",
    )


# Mount images directory
_images_dir = find_images_dir()
if _images_dir:
    app.mount("/api/images", StaticFiles(directory=str(_images_dir)), name="images")
    print(f"Images mounted at /api/images from {_images_dir}")


def find_frontend_dist() -> Optional[Path]:
    """Find frontend dist / __dist__ folder."""
    possible_paths = [
        # apx layout: src/idom_car_ai/__dist__
        Path(__file__).parent.parent / "__dist__",
        # Legacy layout
        Path(__file__).parent.parent.parent.parent / "dist",
        Path.cwd() / "dist",
    ]
    for path in possible_paths:
        if path.exists() and (path / "index.html").exists():
            print(f"Found frontend at: {path}")
            return path
    print("Frontend dist not found")
    return None


_frontend_dist = find_frontend_dist()

if _frontend_dist:
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"error": "Frontend not built"}, 404

    print("SPA catch-all route configured")
else:
    @app.get("/")
    async def root():
        return {"message": "IDOM Car AI API", "docs": "/docs", "health": "/api/health"}
    print("Running in API-only mode (no frontend)")
