"""
Chat API Router
Provides endpoints for the RAG chatbot functionality
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    ProcessPDFRequest, 
    ProcessPDFResponse,
    HealthResponse
)
from backend.services.rag_service import rag_service
from backend.core.config import settings
from backend.core.logging import rag_logger, logger
import uuid

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Main chat endpoint - processes user queries through RAG pipeline
    """
    try:
        # Add session ID if not provided
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        
        # Process through RAG pipeline
        response = rag_service.process_chat_query(request)
        return response
        
    except Exception as e:
        rag_logger.log_error("chat_endpoint", str(e), request.query)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/initialize", response_model=ProcessPDFResponse)
async def initialize_knowledge_base(
    background_tasks: BackgroundTasks,
    request: ProcessPDFRequest = None
):
    """
    Initialize knowledge base by processing PDF and creating embeddings
    This is typically run once or when updating the knowledge base
    """
    try:
        pdf_path = request.pdf_path if request else None
        
        # Process in background for large PDFs
        result = rag_service.initialize_knowledge_base(pdf_path)
        
        return ProcessPDFResponse(
            success=result["success"],
            total_chunks=result.get("total_chunks", 0),
            processing_time=result.get("processing_time", 0),
            message=result["message"]
        )
        
    except Exception as e:
        rag_logger.log_error("initialize_endpoint", str(e))
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.get("/stats")
async def get_statistics():
    """
    Get system statistics and collection information
    """
    try:
        system_status = rag_service.get_system_status()
        return {
            "success": True,
            "data": system_status
        }
    except Exception as e:
        rag_logger.log_error("stats_endpoint", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/demo")
async def run_demo_queries():
    """
    Run sample queries for demonstration
    As required by the task - minimum 3 sample queries
    """
    try:
        # Sample queries demonstrating different student types
        from backend.models.schemas import StudentType
        
        sample_requests = [
            ChatRequest(
                query="Why does a ball thrown upwards come back down?",
                user_type=StudentType.WEAK_PHYSICS,
                weak_subjects=["physics"],
                session_id="demo_1"
            ),
            ChatRequest(
                query="What is the difference between an atom and a molecule?",
                user_type=StudentType.WEAK_CHEMISTRY,
                weak_subjects=["chemistry"],
                session_id="demo_2"
            ),
            ChatRequest(
                query="How do cells divide and grow?",
                user_type=StudentType.STRONG_BIOLOGY,
                weak_subjects=[],
                session_id="demo_3"
            )
        ]
        
        results = []
        for i, request in enumerate(sample_requests, 1):
            logger.info(f"Processing demo query {i}: {request.query}")
            response = rag_service.process_chat_query(request)
            
            results.append({
                "sample_number": i,
                "request": request.dict(),
                "response": response.dict()
            })
        
        return {
            "success": True,
            "message": "Demo queries completed successfully",
            "results": results
        }
        
    except Exception as e:
        rag_logger.log_error("demo_endpoint", str(e))
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.get("/debug-search/{query}")
async def debug_search(query: str):
    """Debug endpoint to test raw retrieval without threshold"""
    try:
        from backend.services.embedding_service import embedding_service
        
        # Get raw results without threshold filtering
        query_embedding = embedding_service.generate_embeddings([query])[0]
        
        results = embedding_service.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        if results['documents'] and results['documents'][0]:
            documents = results['documents'][0]
            distances = results['distances'][0]
            
            debug_results = []
            for i, (doc, distance) in enumerate(zip(documents, distances)):
                similarity_score = 1 / (1 + distance)
                debug_results.append({
                    "chunk_index": i,
                    "similarity_score": round(similarity_score, 4),
                    "distance": round(distance, 4),
                    "content_preview": doc[:100] + "..." if len(doc) > 100 else doc
                })
            
            return {
                "query": query,
                "total_chunks_in_db": embedding_service.collection.count(),
                "results": debug_results,
                "similarity_threshold": settings.similarity_threshold
            }
        else:
            return {
                "query": query,
                "error": "No results returned from ChromaDB",
                "total_chunks_in_db": embedding_service.collection.count()
            }
            
    except Exception as e:
        return {"error": str(e)} 