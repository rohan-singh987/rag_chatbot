"""
Main FastAPI application for the RAG Chatbot.
Combines all routers and middleware for the complete API.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.core.config import settings
from backend.core.logging import RAGLogger, logger
from backend.routers.chat import router as chat_router
from backend.routers.demo import router as demo_router
from backend.routers.health import router as health_router

# Initialize logger
rag_logger = RAGLogger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    logger.info("🚀 Starting RAG Chatbot API...")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"📊 Embedding model: {settings.embedding_model}")
    logger.info(f"🤖 LLM model: {settings.openai_model}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down RAG Chatbot API...")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Educational RAG chatbot for NCERT Class 9 Science",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(demo_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🎓 RAG Educational Chatbot API",
        "description": "AI-powered tutor for NCERT Class 9 Science",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "demo": "/demo", 
            "health": "/health"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error("Unhandled exception: {}", str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Application startup completed")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Application shutdown completed")

# Run the application
if __name__ == "__main__":
    logger.info(f"🌐 Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
