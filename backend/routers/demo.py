"""
Demo router for the RAG Chatbot API.
Provides sample queries and system demonstration endpoints.
"""

from fastapi import APIRouter
from backend.models.schemas import DemoResponse
from backend.core.config import settings
from loguru import logger

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.get("/", 
            response_model=DemoResponse,
            summary="Demo information",
            description="Get demo information and sample queries for the RAG chatbot")
async def get_demo_info():
    """
    Demo endpoint with sample queries and configuration.
    
    Returns:
        DemoResponse with sample queries and system information
    """
    try:
        sample_queries = [
            "Why does a ball thrown upwards come back down?",
            "What is the difference between mass and weight?",
            "Explain how sound travels through different materials",
            "What happens during photosynthesis in plants?",
            "How do forces affect motion in everyday life?",
            "What is the structure of an atom?",
            "Explain the water cycle in nature",
            "How do our digestive system work?"
        ]
        
        configuration = {
            "embedding_model": settings.embedding_model,
            "llm_model": settings.openai_model,
            "chunk_size": settings.chunk_size,
            "retrieval_k": settings.retrieval_k,
            "collection_name": settings.collection_name,
            "personalization_enabled": settings.enable_personalization
        }
        
        logger.info("Demo information requested")
        
        return DemoResponse(
            message="Welcome to the RAG Educational Chatbot! Here are some sample queries you can try.",
            sample_queries=sample_queries,
            configuration=configuration
        )
        
    except Exception as e:
        logger.error(f"Demo endpoint error: {e}")
        return DemoResponse(
            message=f"Demo endpoint error: {str(e)}",
            sample_queries=[],
            configuration={}
        ) 