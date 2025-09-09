import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import alt, value, download, parts, aliases
from app.db.mongo import connect_to_mongo, close_mongo_connection, ping_mongodb

# Ensure DATA_DIR exists
os.makedirs(settings.DATA_DIR, exist_ok=True)

app = FastAPI(
    title="CE AI Assistant",
    description="包含 SSE 和檔案處理的範例",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(alt.router, prefix="/api/alt", tags=["alt"])
app.include_router(value.router, prefix="/api/value", tags=["value"])
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(parts.router, prefix="/api/parts", tags=["parts"])
app.include_router(aliases.router, prefix="/api/aliases", tags=["aliases"])

@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}

@app.get("/api/health/db", tags=["Health Check"])
async def db_health_check():
    return await ping_mongodb()

# SPA static files
STATIC_DIR = (Path(__file__).resolve().parent.parent / "static")

# Mount the assets directory specifically
if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=(STATIC_DIR / "assets")), name="assets")

# Catch-all route to serve index.html for any other path
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    # This fallback should ideally not be hit if your frontend build is correct
    return FileResponse(status_code=404)
