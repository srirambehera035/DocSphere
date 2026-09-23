import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.database import init_db
from app.services.seed_data import seed_sample_documents
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        await seed_sample_documents(overwrite=False)
    except Exception as e:
        print(f"Error seeding documents on startup: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

frontend_dist = Path(__file__).resolve().parent.parent / "static"
if not (frontend_dist / "index.html").exists():
    alt_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if (alt_dist / "index.html").exists():
        frontend_dist = alt_dist

if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return FileResponse(frontend_dist / "index.html")
        target = frontend_dist / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(frontend_dist / "index.html")
