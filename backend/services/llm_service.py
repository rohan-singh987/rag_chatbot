"""
LLM Service for the RAG Chatbot
Generates personalized, grounded responses using retrieved context
Handles different student types and weak subject personalization
"""

from openai import OpenAI
from typing import List, Dict, Any
import time
from backend.core.config import settings
from backend.core.logging import rag_logger, logger
from backend.models.schemas import RetrievedChunk, StudentType, LLMPrompt

class LLMService:
    """
    Handles LLM interactions for generating contextual responses
    Implements personalization based on student profiles
    """
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.max_tokens
        
        # Initialize OpenAI client
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not provided. LLM service will not work.")
            self.client = None
    
    def _create_system_prompt(self, user_type: StudentType, weak_subjects: List[str]) -> str:
        """
        Create personalized system prompt based on student profile
        This is crucial for adapting response style and complexity
        """
        base_prompt = """You are an AI tutoring assistant specialized in Class 9 NCERT Science. 
Your role is to help students understand scientific concepts clearly and accurately.

IMPORTANT GUIDELINES:
1. Base your answers ONLY on the provided context from the NCERT textbook
2. If the context doesn't contain enough information, clearly state this limitation
3. Never make up facts or provide information not found in the context
4. Always cite the chapter/page when possible
5. Use simple, clear language appropriate for Class 9 students"""

        # Personalization based on student type
        personalization = ""
        
        if user_type == StudentType.WEAK_PHYSICS:
            personalization = """
PERSONALIZATION FOR PHYSICS-WEAK STUDENT:
- Use simple analogies and real-world examples for physics concepts
- Break down complex physics problems into smaller steps
- Avoid heavy mathematical derivations unless specifically asked
- Focus on conceptual understanding over calculations
- Use everyday examples to explain abstract physics concepts"""
            
        elif user_type == StudentType.WEAK_CHEMISTRY:
            personalization = """
PERSONALIZATION FOR CHEMISTRY-WEAK STUDENT:
- Use visual descriptions for chemical processes
- Relate chemistry concepts to daily life examples
- Avoid complex chemical equations unless necessary
- Focus on understanding 'why' reactions happen
- Use simple language for chemical terminology"""
            
        elif user_type == StudentType.WEAK_BIOLOGY:
            personalization = """
PERSONALIZATION FOR BIOLOGY-WEAK STUDENT:
- Use relatable examples from human body and nature
- Break down biological processes into simple steps
- Avoid complex biological terminology without explanation
- Focus on how biological processes affect everyday life
- Use analogies to explain biological functions"""
            
        elif user_type in [StudentType.STRONG_PHYSICS, StudentType.STRONG_CHEMISTRY, StudentType.STRONG_BIOLOGY]:
            personalization = """
PERSONALIZATION FOR ADVANCED STUDENT:
- You can use more technical terminology
- Include detailed explanations and mechanisms
- Make connections between different concepts
- Encourage deeper thinking with follow-up questions
- Provide additional context when relevant"""
        
        # Add weak subject considerations
        if weak_subjects:
            weak_subject_text = ", ".join(weak_subjects)
            personalization += f"""

ADDITIONAL CONSIDERATION:
The student has indicated weakness in: {weak_subject_text}
When topics relate to these subjects, provide extra clarity and simpler explanations."""

        return base_prompt + personalization
    
    def _create_user_prompt(self, query: str, context: str) -> str:
        """Create the user prompt with query and retrieved context"""
        return f"""Based on the following context from the NCERT Class 9 Science textbook, please answer the student's question.

CONTEXT:
{context}

STUDENT'S QUESTION:
{query}

Please provide a clear, accurate answer based on the context above. If the context doesn't fully address the question, mention what information is missing."""
    
    def _extract_context_from_chunks(self, chunks: List[RetrievedChunk]) -> str:
        """Extract and format context from retrieved chunks"""
        if not chunks:
            return "No relevant context found in the textbook."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            chapter = chunk.metadata.get('chapter', 'Unknown Chapter')
            page = chunk.metadata.get('page_number', 'Unknown Page')
            
            context_part = f"""[Source {i}: {chapter}, Page {page}]
{chunk.content}
---"""
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _identify_matched_topics(self, query: str, chunks: List[RetrievedChunk]) -> List[str]:
        """Identify topics covered in the query and retrieved chunks"""
        topics = set()
        
        # Common science topics for Class 9
        topic_keywords = {
            "matter": ["matter", "solid", "liquid", "gas", "state", "particle"],
            "motion": ["motion", "speed", "velocity", "acceleration", "distance"],
            "force": ["force", "newton", "pressure", "thrust"],
            "gravity": ["gravity", "gravitation", "weight", "mass"],
            "work_energy": ["work", "energy", "power", "kinetic", "potential"],
            "sound": ["sound", "wave", "frequency", "amplitude", "noise"],
            "atoms": ["atom", "molecule", "element", "compound", "ion"],
            "cell": ["cell", "tissue", "organ", "organism"],
            "diversity": ["classification", "species", "kingdom", "taxonomy"],
            "health": ["disease", "health", "immunity", "vaccine"]
        }
        
        # Check query and chunk content for topic keywords
        text_to_check = query.lower() + " " + " ".join([chunk.content.lower() for chunk in chunks])
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                topics.add(topic)
        
        return list(topics)
    
    def generate_response(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        user_type: StudentType = StudentType.GENERAL,
        weak_subjects: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized response using LLM
        Main interface for the LLM service
        """
        start_time = time.time()
        
        try:
            if not self.client:
                return {
                    "success": False,
                    "answer": "LLM service is not available. Please configure OpenAI API key.",
                    "matched_topics": [],
                    "personalization_applied": False,
                    "processing_time": 0,
                    "tokens_used": 0
                }
            
            weak_subjects = weak_subjects or []
            
            # Extract context from chunks
            context = self._extract_context_from_chunks(retrieved_chunks)
            
            # Identify matched topics
            matched_topics = self._identify_matched_topics(query, retrieved_chunks)
            
            # Create prompts
            system_prompt = self._create_system_prompt(user_type, weak_subjects)
            user_prompt = self._create_user_prompt(query, context)
            
            # Log personalization decision
            personalization_applied = user_type != StudentType.GENERAL or bool(weak_subjects)
            rag_logger.log_personalization(
                user_type=user_type.value,
                weak_subjects=weak_subjects,
                matched_topics=matched_topics,
                personalization_applied=personalization_applied
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract response
            answer = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            processing_time = time.time() - start_time
            
            # Log LLM response
            rag_logger.log_llm_response(
                query=query,
                retrieved_context=context,
                llm_response=answer,
                user_type=user_type.value,
                processing_time=processing_time,
                tokens_used=tokens_used
            )
            
            return {
                "success": True,
                "answer": answer,
                "matched_topics": matched_topics,
                "personalization_applied": personalization_applied,
                "processing_time": processing_time,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"LLM response generation failed: {str(e)}"
            
            rag_logger.log_error(
                operation="llm_response_generation",
                error_message=error_msg,
                query=query
            )
            
            return {
                "success": False,
                "answer": f"I apologize, but I encountered an error while generating the response: {error_msg}",
                "matched_topics": [],
                "personalization_applied": False,
                "processing_time": processing_time,
                "tokens_used": 0
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection"""
        try:
            if not self.client:
                return {"status": "error", "message": "OpenAI client not initialized"}
            
            # Make a simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say 'API connection successful'"}],
                max_tokens=10
            )
            
            return {
                "status": "success",
                "message": "OpenAI API connection successful",
                "model": self.model
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API connection failed: {str(e)}"
            }

# Create global instance
llm_service = LLMService() 