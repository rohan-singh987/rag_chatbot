# 🔬 RAG Science Chatbot Frontend

This is the Streamlit frontend for the Class 9 NCERT Science RAG Chatbot.

## Features

### 🎨 Beautiful UI
- Modern chat interface with bubble-style messages
- Gradient header with science theme
- Responsive layout with sidebar configuration
- Real-time backend health monitoring

### 💬 Chat Interface
- Interactive chat with the RAG chatbot
- Message timestamps
- Chat history persistence during session
- Loading indicators while processing

### 👤 Student Personalization
- Select student learning profile:
  - General Student
  - Weak in Physics
  - Weak in Chemistry  
  - Weak in Biology
  - Strong in Physics
  - Strong in Chemistry
  - Strong in Biology
- Configure weak subjects for personalized responses

### 📊 Analytics Dashboard
- Real-time chat statistics
- Response processing time metrics
- Source chunk information
- Topic identification display
- Personalization status

### 📚 Source References
- View retrieved source chunks
- Similarity scores for each reference
- Expandable content preview
- Chapter and page metadata

## Running the Frontend

### Prerequisites
1. Make sure the FastAPI backend is running on `http://localhost:8000`
2. Install required dependencies (already in `requirements.txt`)

### Start the Streamlit App
```bash
# From the project root directory
streamlit run frontend/app.py
```

The app will open in your browser at `http://localhost:8501`

### Usage Instructions

1. **Start Backend First**: Ensure your FastAPI server is running
2. **Select Profile**: Choose your student learning profile in the sidebar
3. **Configure Subjects**: If you're weak in specific subjects, check the relevant boxes
4. **Ask Questions**: Type your science questions in the input field
5. **View Responses**: See personalized answers with source references
6. **Explore Sources**: Check the sidebar for detailed source information

### Example Questions

Try these sample questions to test the chatbot:

- "Why does a ball thrown upwards come back down?"
- "What is the difference between an atom and a molecule?"
- "How do cells divide and grow?"
- "What is photosynthesis?"
- "Why do we fall ill?"

### Features Showcase

#### Chat Interface
- Clean, modern design with chat bubbles
- User messages appear on the right (blue)
- Bot responses appear on the left (gray)
- Timestamps for each message

#### Sidebar Configuration
- Backend health status indicator
- Student profile selection
- Subject weakness configuration
- Session management
- Source reference display

#### Analytics Panel
- Message count metrics
- Processing time tracking
- Source usage statistics
- Personalization indicators

## Configuration

### API Endpoint
The frontend connects to the backend at `http://localhost:8000/api/v1`

To change this, modify the `API_BASE_URL` variable in `app.py`:

```python
API_BASE_URL = "http://your-backend-url/api/v1"
```

### Student Types
The app supports various student profiles that affect response personalization:

- `general`: Standard responses
- `weak_physics`: Simplified physics explanations
- `weak_chemistry`: Simplified chemistry explanations  
- `weak_biology`: Simplified biology explanations
- `strong_*`: Advanced explanations for strong students

## Troubleshooting

### Backend Connection Issues
- **Error**: "Cannot connect to the backend API"
- **Solution**: Make sure FastAPI server is running on port 8000

### Slow Responses
- Check backend logs for processing delays
- Ensure ChromaDB is properly initialized
- Verify OpenAI API keys are configured

### Missing Responses
- Check backend health endpoint: `http://localhost:8000/api/v1/health`
- Verify knowledge base is initialized
- Check logs for any errors

## Development

### Customizing the UI
- Modify the CSS in the `st.markdown()` section
- Adjust colors, spacing, and layout as needed
- Add new components using Streamlit widgets

### Adding Features
- Add new student profile types in `STUDENT_TYPES`
- Implement additional metrics in the analytics panel
- Add export functionality for chat history

### API Integration
- All API calls are handled in `call_chat_api()`
- Response processing in `process_query()`
- Health checks in `check_backend_health()` 