from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
import os

from backend.logging_setup import setup_comprehensive_logging
import time
from .scheduler import scheduler, start_scheduler, stop_scheduler

setup_comprehensive_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger(__name__)
    logger.info("Starting up APScheduler...")
    if not scheduler.running:
        scheduler.start()
        
    yield
    
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()

app = FastAPI(
    title="AI Translation Service API", 
    description="Secure translation service with rate limiting and authentication",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:8080,http://127.0.0.1:8080,http://localhost:3001,http://127.0.0.1:3001,http://localhost:4173,http://127.0.0.1:4173,http://127.0.0.1:8002,http://127.0.0.1:8001").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex=None,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

def _rate_limit_exceeded_handler(request, exc):
    """Custom rate limit exceeded handler"""
    from slowapi.errors import RateLimitExceeded
    from fastapi.responses import JSONResponse
    from fastapi import status
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Rate limit exceeded", "retry_after": getattr(exc, "retry_after", 60)}
    )

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

import logging

from slowapi.middleware import SlowAPIMiddleware
from .database import init_db
from .routers import auth, user, admin, translate, workspace
from .routers import api_keys
from .routers import pricing

app.add_middleware(SlowAPIMiddleware)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(translate.router, prefix="/translate", tags=["translate"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
app.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
app.include_router(pricing.router, prefix="/pricing", tags=["pricing"])


@app.get("/")
def read_root():
    return {"message": "AI Translation Service API"}

@app.get("/metrics")
def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": int(time.time())}

