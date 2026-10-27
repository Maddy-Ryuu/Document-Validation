import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.endpoints import router as api_router

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aicte_backend")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Regulatory application validation, document verification and compliance platform backend for AICTE.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error occurred at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact system administrator."},
    )


# Include endpoints under /api
app.include_router(api_router, prefix=settings.API_V1_STR)

# Locate frontend static bundle directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.isdir(STATIC_DIR):
    alt_dir = os.path.join(os.getcwd(), "static")
    if os.path.isdir(alt_dir):
        STATIC_DIR = alt_dir

# Mount static assets directory
assets_dir = os.path.join(STATIC_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon_svg():
    f = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.isfile(f):
        return FileResponse(f)
    raise HTTPException(status_code=404)


@app.get("/icons.svg", include_in_schema=False)
async def icons_svg():
    f = os.path.join(STATIC_DIR, "icons.svg")
    if os.path.isfile(f):
        return FileResponse(f)
    raise HTTPException(status_code=404)


@app.get("/vite.svg", include_in_schema=False)
async def vite_svg():
    f = os.path.join(STATIC_DIR, "vite.svg")
    if os.path.isfile(f):
        return FileResponse(f)
    raise HTTPException(status_code=404)


@app.get("/", include_in_schema=False)
async def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file, media_type="text/html")
    return {
        "message": "AICTE Application Validation API",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_frontend(full_path: str):
    # Do not intercept API, docs, or schema paths
    if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
        raise HTTPException(status_code=404, detail="API route not found")

    candidate = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(candidate) and not full_path.endswith((".py", ".env", ".db", ".key")):
        return FileResponse(candidate)

    # SPA client-side fallback
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file, media_type="text/html")

    raise HTTPException(status_code=404, detail="Resource not found")

