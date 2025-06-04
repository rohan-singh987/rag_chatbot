"""
Embedding Service for the RAG Chatbot
Handles text embeddings generation and vector database operations using ChromaDB
"""

import os
import time
import numpy as np
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
from backend.core.config import settings
from backend.core.logging import rag_logger, logger
from backend.models.schemas import DocumentChunk, RetrievedChunk

class EmbeddingService:
    """
    Manages embeddings generation and ChromaDB operations
    Provides semantic search capabilities for the RAG pipeline
    """
    
    def __init__(self):
        self.embedding_model_name = settings.embedding_model
        self.collection_name = settings.collection_name
        self.db_path = settings.chroma_db_path
        
        # Initialize embedding model
        self._load_embedding_model()
        
        # Initialize ChromaDB client
        self._initialize_chroma_client()
        
    def _load_embedding_model(self):
        """Load the sentence transformer model for embeddings"""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            rag_logger.log_error(
                operation="embedding_model_loading",
                error_message=f"Failed to load embedding model: {str(e)}"
            )
            raise
    
    def _initialize_chroma_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure directory exists
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialize ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "NCERT Class 9 Science textbook chunks"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
            logger.info(f"Collection contains {self.collection.count()} documents")
            
        except Exception as e:
            rag_logger.log_error(
                operation="chromadb_initialization",
                error_message=f"Failed to initialize ChromaDB: {str(e)}"
            )
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        Returns numpy array of embeddings
        """
        try:
            start_time = time.time()
            
            # Generate embeddings using sentence transformer
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Generated embeddings for {len(texts)} texts in {processing_time:.2f}s")
            
            return embeddings
            
        except Exception as e:
            rag_logger.log_error(
                operation="embedding_generation",
                error_message=f"Failed to generate embeddings: {str(e)}"
            )
            raise
    
    def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """
        Store document chunks with their embeddings in ChromaDB
        Returns True if successful
        """
        try:
            start_time = time.time()
            
            if not chunks:
                logger.warning("No chunks provided for storage")
                return False
            
            # Extract texts for embedding
            texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = texts
            metadatas = [chunk.metadata for chunk in chunks]
            embeddings_list = embeddings.tolist()
            
            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Stored {len(chunks)} chunks in ChromaDB in {processing_time:.2f}s")
            
            return True
            
        except Exception as e:
            rag_logger.log_error(
                operation="chunk_storage",
                error_message=f"Failed to store chunks: {str(e)}"
            )
            return False
    
    def search_chunks(
        self, 
        query: str, 
        k: int = None, 
        similarity_threshold: float = None
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks using semantic similarity
        Returns list of retrieved chunks with similarity scores
        """
        try:
            # Use default values if not provided
            k = k or settings.retrieval_k
            similarity_threshold = similarity_threshold or settings.similarity_threshold
            
            start_time = time.time()
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(k, self.collection.count()),  # Don't exceed available documents
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results
            retrieved_chunks = []
            
            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Convert distance to similarity score - ChromaDB returns cosine distance
                    # For cosine distance: similarity = (2 - distance) / 2, normalized to [0,1]
                    # But simpler: just use 1 / (1 + distance) for a meaningful similarity score
                    similarity_score = 1 / (1 + distance)
                    
                    # Debug: Log all scores to see what we're getting
                    logger.info(f"Debug - Chunk {i}: similarity_score={similarity_score:.4f}, threshold={similarity_threshold}")
                    
                    # Apply similarity threshold
                    if similarity_score >= similarity_threshold:
                        retrieved_chunk = RetrievedChunk(
                            content=doc,
                            metadata=metadata,
                            similarity_score=round(similarity_score, 4)
                        )
                        retrieved_chunks.append(retrieved_chunk)
            
            processing_time = time.time() - start_time
            
            # Log retrieval statistics
            rag_logger.log_retrieval(
                query=query,
                retrieved_chunks=[chunk.dict() for chunk in retrieved_chunks],
                retrieval_scores=[chunk.similarity_score for chunk in retrieved_chunks],
                total_chunks_in_db=self.collection.count()
            )
            
            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks for query in {processing_time:.2f}s"
            )
            
            return retrieved_chunks
            
        except Exception as e:
            rag_logger.log_error(
                operation="chunk_search",
                error_message=f"Failed to search chunks: {str(e)}",
                query=query
            )
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection"""
        try:
            total_chunks = self.collection.count()
            
            # Get sample metadata to understand chunk distribution
            if total_chunks > 0:
                sample_results = self.collection.get(limit=min(100, total_chunks), include=['metadatas'])
                
                # Analyze chapter distribution
                chapters = {}
                chunk_types = {}
                
                for metadata in sample_results['metadatas']:
                    chapter = metadata.get('chapter', 'Unknown')
                    chunk_type = metadata.get('chunk_type', 'content')
                    
                    chapters[chapter] = chapters.get(chapter, 0) + 1
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                return {
                    "total_chunks": total_chunks,
                    "chapters": chapters,
                    "chunk_types": chunk_types,
                    "embedding_model": self.embedding_model_name,
                    "collection_name": self.collection_name
                }
            else:
                return {
                    "total_chunks": 0,
                    "message": "No chunks stored in collection"
                }
                
        except Exception as e:
            rag_logger.log_error(
                operation="collection_stats",
                error_message=f"Failed to get collection stats: {str(e)}"
            )
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all data from the collection (useful for reprocessing)"""
        try:
            # Delete the collection
            self.chroma_client.delete_collection(name=self.collection_name)
            
            # Recreate empty collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "NCERT Class 9 Science textbook chunks"}
            )
            
            logger.info("Collection cleared successfully")
            return True
            
        except Exception as e:
            rag_logger.log_error(
                operation="collection_clear",
                error_message=f"Failed to clear collection: {str(e)}"
            )
            return False
    
    def is_collection_empty(self) -> bool:
        """Check if the collection is empty"""
        try:
            return self.collection.count() == 0
        except:
            return True

# Create global instance
embedding_service = EmbeddingService() 