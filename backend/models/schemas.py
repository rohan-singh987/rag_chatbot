"""
Pydantic models for the RAG Chatbot API
Defines request/response schemas and internal data structures
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class StudentType(str, Enum):
    """Student proficiency levels for personalization"""
    WEAK_PHYSICS = "weak_physics"
    WEAK_CHEMISTRY = "weak_chemistry" 
    WEAK_BIOLOGY = "weak_biology"
    STRONG_PHYSICS = "strong_physics"
    STRONG_CHEMISTRY = "strong_chemistry"
    STRONG_BIOLOGY = "strong_biology"
    GENERAL = "general"

class ChatRequest(BaseModel):
    """
    Request schema for chat endpoint
    Contains user query and metadata for personalization
    """
    query: str = Field(..., description="User's question or query")
    user_metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="User metadata for personalization (e.g., weak subjects)"
    )
    user_type: StudentType = Field(default=StudentType.GENERAL, description="Student's proficiency type")
    weak_subjects: List[str] = Field(default=[], description="List of subjects student is weak in")
    session_id: Optional[str] = Field(default=None, description="Session identifier for conversation tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Why does a ball thrown upwards come back down?",
                "user_type": "weak_physics",
                "weak_subjects": ["physics"],
                "session_id": "user123_session456"
            }
        }

class RetrievedChunk(BaseModel):
    """
    Schema for text chunks retrieved from vector database
    """
    content: str = Field(..., description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata (chapter, page, topic)")
    similarity_score: float = Field(..., description="Similarity score with query", ge=0.0, le=1.0)

class ChatResponse(BaseModel):
    """
    Response schema for chat endpoint
    Contains generated answer and retrieval information
    """
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer from RAG pipeline")
    retrieved_chunks: List[str] = Field(..., description="Text chunks used for generation")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the response")
    user_type: StudentType = Field(..., description="Student type used for personalization")
    matched_topics: List[str] = Field(default=[], description="Topics identified in the query")
    personalization_applied: bool = Field(default=False, description="Whether personalization was applied")
    processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Why does a ball thrown upwards come back down?",
                "answer": "When you throw a ball upwards, gravity pulls it back down. Gravity is a force that attracts objects toward Earth...",
                "retrieved_chunks": ["Newton's law of universal gravitation states..."],
                "metadata": {"chapter": "Gravitation", "page": 134, "topic": "gravity"},
                "user_type": "weak_physics",
                "matched_topics": ["gravity", "motion"],
                "personalization_applied": True,
                "processing_time": 2.34,
                "timestamp": "2024-01-15T10:30:45"
            }
        }

class ProcessPDFRequest(BaseModel):
    """Request schema for PDF processing endpoint"""
    pdf_path: str = Field(..., description="Path to PDF file")
    chunk_size: int = Field(default=1000, description="Size of text chunks", gt=100, le=2000)
    chunk_overlap: int = Field(default=200, description="Overlap between chunks", ge=0, le=500)

class ProcessPDFResponse(BaseModel):
    """Response schema for PDF processing"""
    success: bool = Field(..., description="Whether processing was successful")
    total_chunks: int = Field(..., description="Number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")
    message: str = Field(..., description="Status message")

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Status message")
    services: Dict[str, bool] = Field(..., description="Status of individual services")

# Internal data structures for services

class DocumentChunk(BaseModel):
    """
    Internal model for document chunks before embedding
    """
    text: str = Field(..., description="Chunk text content")
    metadata: Dict[str, Any] = Field(default={}, description="Metadata about the chunk")
    chunk_id: str = Field(..., description="Unique identifier for the chunk")

class EmbeddingRequest(BaseModel):
    """Internal model for embedding generation requests"""
    texts: List[str] = Field(..., description="List of texts to embed")
    model_name: str = Field(..., description="Embedding model to use")

class RetrievalQuery(BaseModel):
    """Internal model for retrieval queries"""
    query_text: str = Field(..., description="Query text")
    k: int = Field(default=5, description="Number of chunks to retrieve", gt=0, le=20)
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity threshold", ge=0.0, le=1.0)

class LLMPrompt(BaseModel):
    """Internal model for LLM prompting"""
    system_prompt: str = Field(..., description="System prompt for LLM")
    user_query: str = Field(..., description="User query")
    context: str = Field(..., description="Retrieved context")
    user_type: StudentType = Field(..., description="Student type for personalization")
    temperature: float = Field(default=0.7, description="LLM temperature", ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, description="Maximum tokens in response", gt=0, le=2000)

class DemoResponse(BaseModel):
    """Response model for demo endpoint."""
    message: str = Field(..., description="Demo message")
    sample_queries: List[str] = Field(..., description="List of sample queries")
    configuration: Dict[str, Any] = Field(..., description="Current system configuration")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information") 