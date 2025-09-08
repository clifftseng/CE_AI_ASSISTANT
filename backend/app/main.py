import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import alt, value, download

# Ensure DATA_DIR exists
os.makedirs(settings.DATA_DIR, exist_ok=True)

app = FastAPI(
    title="CE AI Assistant", # Changed title
    description="包含 SSE 和檔案處理的範例",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alt.router, prefix="/api/alt", tags=["alt"])
app.include_router(value.router, prefix="/api/value", tags=["value"])
app.include_router(download.router, prefix="/api/download", tags=["download"])

@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}
