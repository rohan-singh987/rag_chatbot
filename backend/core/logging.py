"""
Logging configuration for the RAG Chatbot
Handles structured logging of queries, retrievals, and responses
"""

from loguru import logger
from backend.core.config import settings
import sys
import json
from typing import Dict, Any, List
from datetime import datetime

def setup_logging():
    """
    Configure loguru for structured logging
    This is crucial for tracking RAG pipeline performance
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file logger
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    return logger

# Initialize logging
setup_logging()

class RAGLogger:
    """
    Structured logger for RAG pipeline operations
    Tracks the complete query → retrieval → response flow
    """
    
    @staticmethod
    def log_query(
        user_query: str,
        user_type: str = "general",
        weak_subjects: List[str] = None,
        session_id: str = None
    ):
        """Log incoming user query with metadata"""
        log_data = {
            "event": "user_query",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_query": user_query,
            "user_type": user_type,
            "weak_subjects": weak_subjects or []
        }
        logger.info(f"USER_QUERY: {json.dumps(log_data)}")
        
    @staticmethod
    def log_retrieval(
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        retrieval_scores: List[float],
        total_chunks_in_db: int
    ):
        """Log retrieval results and performance"""
        log_data = {
            "event": "chunk_retrieval", 
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "num_retrieved": len(retrieved_chunks),
            "total_chunks_available": total_chunks_in_db,
            "avg_similarity_score": sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0,
            "retrieved_sources": [chunk.get("metadata", {}).get("chapter", "unknown") for chunk in retrieved_chunks]
        }
        logger.info(f"RETRIEVAL: {json.dumps(log_data)}")
        
    @staticmethod
    def log_llm_response(
        query: str,
        retrieved_context: str,
        llm_response: str,
        user_type: str,
        processing_time: float,
        tokens_used: int = None
    ):
        """Log LLM response generation"""
        log_data = {
            "event": "llm_response",
            "timestamp": datetime.now().isoformat(), 
            "query": query,
            "user_type": user_type,
            "response_length": len(llm_response),
            "context_length": len(retrieved_context),
            "processing_time_seconds": processing_time,
            "tokens_used": tokens_used
        }
        logger.info(f"LLM_RESPONSE: {json.dumps(log_data)}")
        
    @staticmethod
    def log_personalization(
        user_type: str,
        weak_subjects: List[str],
        matched_topics: List[str],
        personalization_applied: bool
    ):
        """Log personalization decisions"""
        log_data = {
            "event": "personalization",
            "timestamp": datetime.now().isoformat(),
            "user_type": user_type,
            "weak_subjects": weak_subjects,
            "matched_topics": matched_topics,
            "personalization_applied": personalization_applied
        }
        logger.info(f"PERSONALIZATION: {json.dumps(log_data)}")
        
    @staticmethod
    def log_error(
        operation: str,
        error_message: str,
        query: str = None,
        stack_trace: str = None
    ):
        """Log errors in the RAG pipeline"""
        log_data = {
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "error_message": error_message,
            "query": query,
            "stack_trace": stack_trace
        }
        logger.error(f"ERROR: {json.dumps(log_data)}")

# Create global logger instance
rag_logger = RAGLogger() 