"""
Configuration management for the RAG Chatbot
Handles environment variables, API keys, and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    This centralizes all configuration in one place
    """
    
    # Application Settings
    app_name: str = "RAG Educational Chatbot"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # API Configuration
    api_host: str = Field(default="127.0.0.1", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # LLM Configuration - OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    openai_temperature: float = Field(default=0.7, description="LLM temperature for creativity")
    max_tokens: int = Field(default=500, description="Maximum tokens in LLM response")
    
    # Embedding Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension")
    
    # ChromaDB Configuration
    chroma_db_path: str = Field(default="./data/chroma_db", description="ChromaDB storage path")
    collection_name: str = Field(default="ncert_science_class9", description="ChromaDB collection name")
    
    # PDF Processing Configuration - Updated for multiple PDFs
    pdf_directory: str = Field(default="./data", description="Directory containing NCERT PDF files")
    pdf_pattern: str = Field(default="iesc*.pdf", description="Pattern to match PDF files")
    chunk_size: int = Field(default=1000, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    
    # Retrieval Configuration
    retrieval_k: int = Field(default=5, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.4, description="Minimum similarity for retrieval")
    
    # Student Personalization
    enable_personalization: bool = Field(default=True, description="Enable student-specific responses")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/rag_chatbot.log", description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings()

# Ensure required directories exist
def create_directories():
    """Create necessary directories for the application"""
    directories = [
        os.path.dirname(settings.chroma_db_path),
        os.path.dirname(settings.log_file),
        settings.pdf_directory  # Directory for PDFs
    ]
    
    for directory in directories:
        if directory:  # Only create non-empty directory paths
            os.makedirs(directory, exist_ok=True)

# Initialize directories on import
create_directories() 