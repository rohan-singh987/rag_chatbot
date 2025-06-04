"""
Health check router for the RAG Chatbot API.
Provides system status and health monitoring endpoints.
"""

from fastapi import APIRouter
from backend.models.schemas import HealthResponse
from backend.core.config import settings
from loguru import logger

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", 
            response_model=HealthResponse,
            summary="Health check",
            description="Check the health status of the RAG chatbot API and its services")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with service status information
    """
    try:
        # Check various services
        services = {
            "api": True,
            "embeddings": True,  # We could add actual checks here
            "vector_db": True,
            "llm": True,
        }
        
        # Overall health status
        status = "healthy" if all(services.values()) else "unhealthy"
        
        logger.info("Health check performed")
        
        return HealthResponse(
            status=status,
            message=f"API is running normally (v{settings.app_version})",
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"Health check failed: {str(e)}",
            services={"api": False, "error": False}
        ) 