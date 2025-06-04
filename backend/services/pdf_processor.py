"""
PDF Processing Service for the RAG Chatbot
Extracts and intelligently chunks text from multiple NCERT Science PDFs
Maintains structure (chapters, headings, definitions) for better retrieval
"""

import os
import re
import uuid
import glob
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
# Note: Using PyMuPDF (imported as fitz) for PDF processing
import fitz
from backend.core.config import settings
from backend.core.logging import rag_logger, logger
from backend.models.schemas import DocumentChunk
import time

class PDFProcessor:
    """
    Handles PDF ingestion, text extraction, and intelligent chunking
    Maintains document structure for better retrieval
    """
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence endings
                "! ",    # Exclamation endings
                "? ",    # Question endings
                "; ",    # Semicolon breaks
                ", ",    # Comma breaks
                " ",     # Word breaks
                ""       # Character level
            ]
        )
    
    def discover_pdf_files(self, pdf_directory: str = None, pattern: str = None) -> List[str]:
        """
        Discover all PDF files in the specified directory
        Returns sorted list of PDF file paths
        """
        pdf_directory = pdf_directory or settings.pdf_directory
        pattern = pattern or settings.pdf_pattern
        
        # Construct search pattern
        search_pattern = os.path.join(pdf_directory, pattern)
        
        # Find all matching PDF files
        pdf_files = glob.glob(search_pattern)
        
        # Sort files to ensure consistent processing order
        pdf_files.sort()
        
        logger.info(f"Discovered {len(pdf_files)} PDF files in {pdf_directory}")
        for pdf_file in pdf_files:
            logger.info(f"  - {os.path.basename(pdf_file)}")
        
        return pdf_files
    
    def extract_text_with_structure(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF while preserving structure
        Returns list of text sections with metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        sections = []
        
        # Extract chapter/file information from filename
        filename = os.path.basename(pdf_path)
        chapter_info = self._extract_chapter_from_filename(filename)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            
            # Skip empty pages
            if not text.strip():
                continue
            
            # Try to extract chapter information from text, fallback to filename
            text_chapter = self._extract_chapter_from_text(text)
            current_chapter = text_chapter or chapter_info
            
            # Process page text
            processed_text = self._clean_text(text)
            
            if processed_text:
                sections.append({
                    "text": processed_text,
                    "page_number": page_num + 1,
                    "chapter": current_chapter,
                    "source": pdf_path,
                    "filename": filename
                })
        
        doc.close()
        logger.info(f"Extracted text from {len(sections)} pages in {filename}")
        return sections
    
    def _extract_chapter_from_filename(self, filename: str) -> str:
        """Extract chapter information from filename"""
        # Pattern for NCERT PDF files like iesc101.pdf, iesc102.pdf etc.
        patterns = [
            r"iesc(\d+)\.pdf",           # iesc101.pdf -> Chapter 101
            r"iesc1an\.pdf",             # iesc1an.pdf -> Introduction/Annexure
            r"iesc1ps\.pdf",             # iesc1ps.pdf -> Preliminary/Preface
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if "1an" in filename.lower():
                    return "Annexure"
                elif "1ps" in filename.lower():
                    return "Preface"
                else:
                    chapter_num = match.group(1)
                    # Convert 101 -> Chapter 1, 102 -> Chapter 2, etc.
                    if chapter_num.startswith('10'):
                        actual_chapter = chapter_num[2:]
                        return f"Chapter {actual_chapter}"
                    else:
                        return f"Chapter {chapter_num}"
        
        # Fallback to filename without extension
        return os.path.splitext(filename)[0].upper()
    
    def _extract_chapter_from_text(self, text: str) -> str:
        """Extract chapter name from text using pattern matching"""
        # Common patterns for chapter headings in NCERT books
        patterns = [
            r"Chapter\s+(\d+)\s*[:\-]?\s*(.+?)(?:\n|$)",
            r"CHAPTER\s+(\d+)\s*[:\-]?\s*(.+?)(?:\n|$)",
            r"(\d+)\.\s+(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    chapter_num, chapter_name = match.groups()
                    return f"Chapter {chapter_num}: {chapter_name.strip()}"
                else:
                    return match.group(1).strip()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers (common patterns)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Page \d+', '', text, flags=re.MULTILINE)
        
        # Remove figure/table references that are standalone
        text = re.sub(r'^Fig\.\s*\d+.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Table\s*\d+.*$', '', text, flags=re.MULTILINE)
        
        # Clean up remaining whitespace
        text = text.strip()
        
        return text
    
    def create_chunks(self, sections: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        Create intelligent chunks from extracted sections
        Maintains context while splitting for optimal retrieval
        """
        all_chunks = []
        
        for section in sections:
            text = section["text"]
            metadata = {
                "chapter": section["chapter"],
                "page_number": section["page_number"],
                "source": section["source"],
                "filename": section["filename"]
            }
            
            # Use text splitter to create chunks
            text_chunks = self.text_splitter.split_text(text)
            
            for i, chunk_text in enumerate(text_chunks):
                # Skip very short chunks
                if len(chunk_text.strip()) < 50:
                    continue
                
                # Enhanced metadata for each chunk
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks_in_section": len(text_chunks),
                    "chunk_type": self._identify_chunk_type(chunk_text)
                }
                
                chunk = DocumentChunk(
                    text=chunk_text.strip(),
                    metadata=chunk_metadata,
                    chunk_id=str(uuid.uuid4())
                )
                
                all_chunks.append(chunk)
        
        logger.info(f"Created {len(all_chunks)} chunks from all sections")
        return all_chunks
    
    def _identify_chunk_type(self, text: str) -> str:
        """Identify the type of content in a chunk for better categorization"""
        text_lower = text.lower()
        
        # Definition patterns
        if any(word in text_lower for word in ["definition:", "define", "is defined as", "refers to"]):
            return "definition"
        
        # Question patterns
        if text.strip().endswith("?") or "question" in text_lower:
            return "question"
        
        # Example patterns
        if any(word in text_lower for word in ["example", "for instance", "such as"]):
            return "example"
        
        # Formula/equation patterns
        if any(char in text for char in ["=", "∝", "±", "°"]):
            return "formula"
        
        return "content"
    
    def process_pdf(self, pdf_path: str = None) -> Dict[str, Any]:
        """
        Main method to process PDF(s) and return chunks
        Can process single PDF or all PDFs in directory
        """
        start_time = time.time()
        
        try:
            if pdf_path:
                # Process single PDF file
                logger.info(f"Processing single PDF: {pdf_path}")
                pdf_files = [pdf_path]
            else:
                # Process all PDFs in directory
                logger.info("Processing all PDFs in directory")
                pdf_files = self.discover_pdf_files()
            
            if not pdf_files:
                raise ValueError("No PDF files found to process")
            
            all_sections = []
            
            # Process each PDF file
            for pdf_file in pdf_files:
                logger.info(f"Processing: {os.path.basename(pdf_file)}")
                try:
                    sections = self.extract_text_with_structure(pdf_file)
                    all_sections.extend(sections)
                except Exception as e:
                    logger.warning(f"Failed to process {pdf_file}: {str(e)}")
                    continue
            
            if not all_sections:
                raise ValueError("No text content extracted from any PDF")
            
            # Create chunks from all sections
            chunks = self.create_chunks(all_sections)
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "total_chunks": len(chunks),
                "total_files_processed": len(pdf_files),
                "chunks": chunks,
                "processing_time": processing_time,
                "message": f"Successfully processed {len(pdf_files)} PDF files into {len(chunks)} chunks"
            }
            
            logger.info(f"PDF processing completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"PDF processing failed: {str(e)}"
            
            rag_logger.log_error(
                operation="pdf_processing",
                error_message=error_msg,
                stack_trace=str(e)
            )
            
            return {
                "success": False,
                "total_chunks": 0,
                "total_files_processed": 0,
                "chunks": [],
                "processing_time": processing_time,
                "message": error_msg
            }

# Create global instance
pdf_processor = PDFProcessor() 