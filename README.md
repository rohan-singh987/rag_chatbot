# 🎓 RAG Educational Chatbot

An AI-powered tutoring assistant for Class 9 Science students using Retrieval-Augmented Generation (RAG) with the official NCERT Science textbook as the knowledge base.

## 🏗️ Architecture Overview

```
├── backend/                      # FastAPI RAG Pipeline
│   ├── core/                     # Configuration & Logging
│   │   ├── config.py             # Environment-based settings
│   │   └── logging.py            # Structured logging for RAG pipeline
│   │
│   ├── models/                   # Pydantic Schemas
│   │   └── schemas.py            # Request/Response models
│   │
│   ├── services/                 # RAG Pipeline Services
│   │   ├── pdf_processor.py      # PDF ingestion & intelligent chunking
│   │   ├── embedding_service.py  # ChromaDB & vector embeddings
│   │   ├── llm_service.py        # OpenAI integration & personalization
│   │   └── rag_service.py        # Main pipeline orchestrator
│   │
│   ├── routers/                  # API Endpoints
│   │   └── chat.py               # Chat, initialization, demo endpoints
│   │
│   └── main.py                   # FastAPI application entry point
│
├── frontend/                     # Streamlit UI (NEW!)
│   ├── app.py                    # Interactive chat interface
│   └── README.md                 # Frontend documentation
│
├── data/                         # Storage (Root Level)
│   ├── chroma_db/               # ChromaDB vector storage
│   ├── iesc1an.pdf              # NCERT Annexure
│   ├── iesc1ps.pdf              # NCERT Preface
│   ├── iesc101.pdf              # Chapter 1: Matter in Our Surroundings
│   ├── iesc102.pdf              # Chapter 2: Is Matter Around Us Pure
│   ├── iesc103.pdf              # Chapter 3: Atoms and Molecules
│   ├── ...                      # Additional chapters (104-111)
│   └── iesc112.pdf              # Chapter 12: Improvement in Food Resources
│
├── logs/                         # Application logs
├── run_frontend.py               # Frontend launcher script
└── requirements.txt              # Python dependencies
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create conda environment
conda create -n rag_chatbot python=3.11
conda activate rag_chatbot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Application Settings
DEBUG=true
API_HOST=127.0.0.1
API_PORT=8000

# PDF Processing - Multiple Files Support
PDF_DIRECTORY=./data
PDF_PATTERN=iesc*.pdf
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# ChromaDB Configuration
CHROMA_DB_PATH=./data/chroma_db
COLLECTION_NAME=ncert_science_class9

# Retrieval Settings
RETRIEVAL_K=5
SIMILARITY_THRESHOLD=0.7
```

### 3. NCERT Textbook Setup

✅ **You Already Have This!** - Your `data/` folder contains all NCERT Class 9 Science chapters:
- `iesc1an.pdf` - Annexure
- `iesc1ps.pdf` - Preface  
- `iesc101.pdf` - Chapter 1: Matter in Our Surroundings
- `iesc102.pdf` - Chapter 2: Is Matter Around Us Pure
- `iesc103.pdf` - Chapter 3: Atoms and Molecules
- ... up to `iesc112.pdf` - Chapter 12: Improvement in Food Resources

### 4. Initialize Knowledge Base

```bash
# Start the backend
python backend/main.py

# Initialize knowledge base (processes ALL PDF files)
curl -X POST "http://localhost:8000/api/v1/initialize"
```

### 5. Start the Application

#### Option A: Manual Launch (Two Terminals)
```bash
# Terminal 1: Backend
python backend/main.py

# Terminal 2: Frontend  
streamlit run frontend/app.py
```

#### Option B: Using Frontend Launcher (Recommended)
```bash
# Start backend first
python backend/main.py

# Then in another terminal, use the launcher
python run_frontend.py
```

The frontend will open automatically at `http://localhost:8501`

## 🎨 Frontend Features

### 🖥️ **Modern Chat Interface**
- **Beautiful UI**: Gradient header with science theme 🔬
- **Chat Bubbles**: User messages (blue, right-aligned) vs Bot responses (gray, left-aligned)
- **Real-time Updates**: Live chat with message timestamps
- **Loading States**: Spinner indicators while processing queries

### 👤 **Student Personalization Panel**
- **Profile Selection**: Choose your learning level
  - General Student
  - Weak in Physics/Chemistry/Biology  
  - Strong in Physics/Chemistry/Biology
- **Subject Configuration**: Check boxes for weak subjects
- **Session Management**: Unique session tracking

### 📊 **Analytics Dashboard**
- **Live Metrics**: Message counts, processing times
- **Response Details**: Source chunk count, similarity scores
- **Personalization Status**: Shows if response was customized
- **Topic Detection**: Identified subjects and concepts

### 📚 **Source References**
- **Expandable Chunks**: View retrieved source content
- **Similarity Scores**: See how relevant each source is
- **Metadata Display**: Chapter info, page numbers
- **Real-time Updates**: Sources shown for each response

### 🛡️ **Health Monitoring**
- **Backend Status**: Real-time connection indicator
- **API Health Check**: Automatic backend monitoring
- **Error Handling**: Graceful error messages and recovery

### 💡 **Example Questions**
Built-in sample queries for different student types:
- "Why does a ball thrown upwards come back down?" (Physics)
- "What is the difference between an atom and a molecule?" (Chemistry)
- "How do cells divide and grow?" (Biology)
- "What is photosynthesis?" (Biology)
- "Why do we fall ill?" (Biology)

## 🔧 Core Features

### 📖 **Multi-PDF Processing**
- **Automatic Discovery**: Finds all `iesc*.pdf` files in data directory
- **Chapter Recognition**: Extracts chapter info from filenames and content
- **Smart Chunking**: Preserves document structure across multiple files
- **Metadata Enrichment**: Tracks source file, chapter, page numbers, content types

### 🧠 **ChromaDB Vector Storage**
- **Semantic Embeddings**: Using `all-MiniLM-L6-v2` model
- **Persistent Storage**: ChromaDB for fast similarity search
- **Metadata Filtering**: Chapter-wise and topic-wise retrieval

### 🎯 **Student Personalization**
- **Proficiency Levels**: Weak/Strong in Physics, Chemistry, Biology
- **Adaptive Responses**: Simplified explanations for weak subjects
- **Context Awareness**: Real-world examples and analogies

### 📊 **Comprehensive Logging**
- **Query Tracking**: User queries → Retrieved chunks → LLM responses
- **Performance Metrics**: Processing times, similarity scores
- **Personalization Logs**: Applied adaptations and topic matching

## 🌟 API Endpoints

### Chat Endpoint
```bash
POST /api/v1/chat
{
  "query": "Why does a ball thrown upwards come back down?",
  "user_type": "weak_physics",
  "weak_subjects": ["physics"],
  "session_id": "user123"
}
```

### Demo Queries
```bash
POST /api/v1/demo
# Runs 3 sample queries with different student types
```

### Health Check
```bash
GET /api/v1/health
# Returns system status and component health
```

## 🎨 Sample Queries & Responses

### **Physics Question (Weak Student)**
**Query**: "Why does a ball thrown upwards come back down?"
**Response**: Simple analogy-driven explanation focusing on gravity with everyday examples

### **Chemistry Question (Weak Student)**  
**Query**: "What is the difference between an atom and a molecule?"
**Response**: Visual descriptions using building blocks analogy

### **Biology Question (Strong Student)**
**Query**: "How do cells divide and grow?"
**Response**: Detailed explanation with technical terminology and mechanisms

## 🔍 Technical Implementation

### **RAG Pipeline Flow**
1. **Query Processing**: User query with personalization metadata
2. **Semantic Retrieval**: ChromaDB similarity search (top-5 chunks)
3. **Context Assembly**: Relevant chunks with source citations
4. **LLM Generation**: Personalized response using OpenAI GPT
5. **Response Logging**: Complete pipeline metrics

### **Personalization Strategy**
- **System Prompts**: Dynamic based on student proficiency
- **Response Adaptation**: Complexity, terminology, examples
- **Weak Subject Handling**: Extra clarity for identified weaknesses

### **Performance Optimizations**
- **Chunk Caching**: Embeddings stored persistently
- **Batch Processing**: Efficient embedding generation
- **Async Operations**: Non-blocking API responses

### **Frontend Architecture**
- **Streamlit Framework**: Rapid prototyping with Python
- **Session State Management**: Persistent chat history
- **API Integration**: RESTful communication with FastAPI backend
- **Responsive Design**: CSS styling for modern appearance
- **Error Boundaries**: Graceful handling of API failures

## 📈 Logging & Monitoring

The system provides comprehensive logging for analysis:

```json
{
  "event": "user_query",
  "timestamp": "2024-01-15T10:30:45",
  "user_query": "Why does a ball come down?",
  "user_type": "weak_physics",
  "weak_subjects": ["physics"]
}

{
  "event": "chunk_retrieval",
  "query": "Why does a ball come down?",
  "num_retrieved": 3,
  "avg_similarity_score": 0.87,
  "retrieved_sources": ["Chapter 10: Gravitation"]
}

{
  "event": "llm_response",
  "processing_time_seconds": 2.34,
  "tokens_used": 156,
  "personalization_applied": true
}
```

## 🛡️ Limitations & Future Improvements

### **Current Limitations**
- Multiple PDF support (Currently: NCERT Class 9 Science - 14 chapters)
- English language support only
- Requires OpenAI API key (commercial dependency)

### **Planned Enhancements**
- Multiple textbook support
- Voice input/output integration
- Conversation memory and context
- Advanced analytics dashboard
- Mobile-responsive UI
- Chat history export
- Multi-language support

## 🚀 Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: Streamlit (NEW!)
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: OpenAI gpt-4o-mini
- **PDF Processing**: PyMuPDF, LangChain
- **Logging**: Loguru
- **Validation**: Pydantic

## 📝 Development Notes

- **Modular Architecture**: Each service is independently testable
- **Async Support**: FastAPI for high-performance API serving
- **Type Safety**: Comprehensive Pydantic models
- **Error Handling**: Graceful fallbacks and detailed error logging
- **Configuration**: Environment-based settings management
- **Frontend Integration**: Seamless API communication with error boundaries
