"""
RAG Orchestration Service
Main service that coordinates the entire RAG pipeline
"""

import time
from typing import Dict, Any
from backend.core.config import settings
from backend.core.logging import rag_logger, logger
from backend.models.schemas import ChatRequest, ChatResponse, StudentType
from backend.services.pdf_processor import pdf_processor
from backend.services.embedding_service import embedding_service
from backend.services.llm_service import llm_service

class RAGService:
    """Main orchestrator for the RAG pipeline"""
    
    def __init__(self):
        self.pdf_processor = pdf_processor
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    def initialize_knowledge_base(self, pdf_path: str = None) -> Dict[str, Any]:
        """Initialize knowledge base by processing PDF and storing embeddings"""
        start_time = time.time()
        
        try:
            logger.info("Starting knowledge base initialization")
            
            # Process PDF
            pdf_result = self.pdf_processor.process_pdf(pdf_path)
            if not pdf_result["success"]:
                return {"success": False, "message": f"PDF processing failed: {pdf_result['message']}"}
            
            chunks = pdf_result["chunks"]
            
            # Clear existing collection
            if not self.embedding_service.is_collection_empty():
                self.embedding_service.clear_collection()
            
            # Store embeddings
            embedding_success = self.embedding_service.store_chunks(chunks)
            if not embedding_success:
                return {"success": False, "message": "Failed to store embeddings"}
            
            return {
                "success": True,
                "message": "Knowledge base initialized successfully",
                "total_chunks": len(chunks),
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            rag_logger.log_error("knowledge_base_initialization", str(e))
            return {"success": False, "message": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get embedding service stats
            collection_stats = self.embedding_service.get_collection_stats()
            
            # Check if knowledge base is initialized
            is_initialized = not self.embedding_service.is_collection_empty()
            
            return {
                "status": "healthy" if is_initialized else "not_initialized",
                "knowledge_base_initialized": is_initialized,
                "collection_stats": collection_stats,
                "services": {
                    "pdf_processor": "healthy",
                    "embedding_service": "healthy",
                    "llm_service": "healthy"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def process_chat_query(self, chat_request: ChatRequest) -> ChatResponse:
        """Process chat query through complete RAG pipeline"""
        start_time = time.time()
        
        try:
            # Log query
            rag_logger.log_query(
                chat_request.query,
                chat_request.user_type.value,
                chat_request.weak_subjects,
                chat_request.session_id
            )
            
            # Retrieve chunks
            retrieved_chunks = self.embedding_service.search_chunks(chat_request.query)
            
            if not retrieved_chunks:
                return ChatResponse(
                    query=chat_request.query,
                    answer="No relevant information found in the textbook.",
                    retrieved_chunks=[],
                    metadata={"message": "no_relevant_chunks"},
                    user_type=chat_request.user_type,
                    processing_time=time.time() - start_time
                )
            
            # Extract just the content strings for the response schema
            chunk_contents = [chunk.content for chunk in retrieved_chunks]
            
            # Generate response
            llm_result = self.llm_service.generate_response(
                chat_request.query,
                retrieved_chunks,  # Pass full objects to LLM service
                chat_request.user_type,
                chat_request.weak_subjects
            )
            
            return ChatResponse(
                query=chat_request.query,
                answer=llm_result["answer"],
                retrieved_chunks=chunk_contents,  # Use string contents
                metadata=llm_result.get("metadata", {}),
                user_type=chat_request.user_type,
                matched_topics=llm_result.get("matched_topics", []),
                personalization_applied=llm_result.get("personalization_applied", False),
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            rag_logger.log_error("chat_query_processing", str(e), chat_request.query)
            return ChatResponse(
                query=chat_request.query,
                answer=f"Error processing query: {str(e)}",
                retrieved_chunks=[],
                metadata={"message": "query_processing_error"},
                user_type=chat_request.user_type,
                processing_time=time.time() - start_time
            )

# Global instance
rag_service = RAGService() 