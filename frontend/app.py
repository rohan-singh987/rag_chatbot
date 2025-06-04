import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import time
import base64

# Configure Streamlit page
st.set_page_config(
    page_title="RAG Science Chatbot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .bot-message {
        background-color: #e9ecef;
        color: #333;
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        margin-right: 20%;
        position: relative;
    }
    
    .speaker-icon {
        position: absolute;
        top: 10px;
        right: 15px;
        cursor: pointer;
        font-size: 16px;
        color: #666;
        transition: color 0.3s ease;
    }
    
    .speaker-icon:hover {
        color: #007bff;
    }
    
    .message-content {
        margin-right: 30px;
    }
    
    .timestamp {
        font-size: 0.8em;
        color: #666;
        margin-top: 5px;
    }
    
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .source-chunk {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .tts-controls {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
STUDENT_TYPES = {
    "General Student": "general",
    "Weak in Physics": "weak_physics", 
    "Weak in Chemistry": "weak_chemistry",
    "Weak in Biology": "weak_biology",
    "Strong in Physics": "strong_physics",
    "Strong in Chemistry": "strong_chemistry", 
    "Strong in Biology": "strong_biology"
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"streamlit_{int(time.time())}"
if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True

def text_to_speech_html(text: str, message_id: str) -> str:
    """Generate HTML for text-to-speech functionality"""
    # Clean the text for TTS (remove markdown, special characters)
    clean_text = text.replace('"', "'").replace('\n', ' ').replace('*', '')
    
    return f"""
    <script>
    function speakText_{message_id}() {{
        if ('speechSynthesis' in window) {{
            // Stop any ongoing speech
            window.speechSynthesis.cancel();
            
            const text = `{clean_text}`;
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Configure voice settings
            utterance.rate = 0.9;  // Slightly slower for better comprehension
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            // Try to use a more natural voice
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('English') || 
                voice.lang.includes('en')
            );
            if (preferredVoice) {{
                utterance.voice = preferredVoice;
            }}
            
            // Visual feedback
            const icon = document.getElementById('speaker_{message_id}');
            if (icon) {{
                icon.style.color = '#007bff';
                icon.innerHTML = '🔊';
            }}
            
            utterance.onend = function() {{
                if (icon) {{
                    icon.style.color = '#666';
                    icon.innerHTML = '🔈';
                }}
            }};
            
            utterance.onerror = function() {{
                if (icon) {{
                    icon.style.color = '#dc3545';
                    icon.innerHTML = '❌';
                    setTimeout(() => {{
                        icon.style.color = '#666';
                        icon.innerHTML = '🔈';
                    }}, 2000);
                }}
            }};
            
            window.speechSynthesis.speak(utterance);
        }} else {{
            alert('Text-to-speech is not supported in your browser');
        }}
    }}
    </script>
    """

def call_chat_api(query: str, user_type: str, weak_subjects: List[str]) -> Dict[str, Any]:
    """Call the FastAPI chat endpoint"""
    try:
        payload = {
            "query": query,
            "user_type": user_type,
            "weak_subjects": weak_subjects,
            "session_id": st.session_state.session_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend API. Please make sure the FastAPI server is running on http://localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def check_backend_health():
    """Check if the backend is healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """Display a chat message with styling"""
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong> {message['content']}
            <div class="timestamp">{message['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Generate unique ID for this message
        message_id = f"msg_{hash(message['content'])}_{message['timestamp'].replace(':', '')}"
        
        # Bot message with speaker icon
        st.markdown(f"""
        <div class="bot-message">
            <div class="speaker-icon" id="speaker_{message_id}" onclick="speakText_{message_id}()" title="Click to hear this response">
                🔈
            </div>
            <div class="message-content">
                <strong>🤖 Science Bot:</strong> {message['content']}
                <div class="timestamp">{message['timestamp']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add the TTS JavaScript
        if st.session_state.tts_enabled:
            st.markdown(text_to_speech_html(message['content'], message_id), unsafe_allow_html=True)

def display_source_chunks(chunks: List[Dict[str, Any]]):
    """Display retrieved source chunks"""
    if chunks:
        st.subheader("📚 Source References")
        for i, chunk in enumerate(chunks, 1):
            with st.expander(f"Reference {i} (Similarity: {chunk['similarity_score']:.2f})"):
                st.markdown(f"""
                <div class="source-chunk">
                    <strong>Content:</strong> {chunk['content'][:200]}...
                    <br><strong>Metadata:</strong> {chunk['metadata']}
                </div>
                """, unsafe_allow_html=True)

# Main App Layout
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Class 9 Science RAG Chatbot</h1>
        <p>Ask me anything about NCERT Class 9 Science!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Backend health check
        backend_healthy = check_backend_health()
        if backend_healthy:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Disconnected")
            st.info("Please start the FastAPI server:\n`python backend/main.py`")
        
        st.markdown("---")
        
        # # Text-to-Speech Settings
        # st.subheader("🔊 Audio Settings")
        # st.session_state.tts_enabled = st.checkbox(
        #     "Enable Text-to-Speech", 
        #     value=st.session_state.tts_enabled,
        #     help="Click the speaker icon on bot responses to hear them aloud"
        # )
        
        # if st.session_state.tts_enabled:
        #     st.markdown("""
        #     <div class="tts-controls">
        #         <strong>🎙️ Voice Controls:</strong><br>
        #         • Click 🔈 icon on any bot response<br>
        #         • 🔊 = Currently speaking<br>
        #         • ❌ = Speech error<br>
        #         <small><em>Uses your browser's built-in voices</em></small>
        #     </div>
        #     """, unsafe_allow_html=True)
        
        # st.markdown("---")
        
        # Student profile selection
        st.subheader("👤 Student Profile")
        selected_type = st.selectbox(
            "Select your learning profile:",
            list(STUDENT_TYPES.keys()),
            index=0
        )
        
        # Weak subjects (for weak student types)
        weak_subjects = []
        if "Weak" in selected_type:
            st.subheader("📚 Subjects You Need Help With")
            physics_weak = st.checkbox("Physics", value="Physics" in selected_type)
            chemistry_weak = st.checkbox("Chemistry", value="Chemistry" in selected_type)
            biology_weak = st.checkbox("Biology", value="Biology" in selected_type)
            
            if physics_weak:
                weak_subjects.append("physics")
            if chemistry_weak:
                weak_subjects.append("chemistry")
            if biology_weak:
                weak_subjects.append("biology")
        
        st.markdown("---")
        
        # Session info
        st.subheader("🔗 Session Info")
        st.info(f"Session ID: {st.session_state.session_id}")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # TTS Info banner
        if st.session_state.tts_enabled:
            st.info("🔈 Text-to-Speech enabled! Click the speaker icon on bot responses to hear them.")
        
        # Chat history display
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(message, message["role"] == "user")
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            query = st.text_input(
                "Ask your science question:",
                placeholder="e.g., Why does a ball thrown upwards come back down?",
                key="query_input"
            )
            
            col_send, col_example = st.columns([1, 1])
            with col_send:
                submit_button = st.form_submit_button("🚀 Send", use_container_width=True)
            
            with col_example:
                if st.form_submit_button("💡 Example Questions", use_container_width=True):
                    examples = [
                        "Why does a ball thrown upwards come back down?",
                        "What is the difference between an atom and a molecule?",
                        "How do cells divide and grow?",
                        "What is photosynthesis?",
                        "Why do we fall ill?"
                    ]
                    st.session_state.example_queries = examples
        
        # Show example queries if requested
        if hasattr(st.session_state, 'example_queries'):
            st.subheader("💡 Example Questions")
            for example in st.session_state.example_queries:
                if st.button(example, key=f"example_{hash(example)}"):
                    # Process the example query
                    process_query(example, STUDENT_TYPES[selected_type], weak_subjects)
    
    with col2:
        st.subheader("📊 Chat Statistics")
        
        # Chat metrics
        total_messages = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        bot_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        st.metric("Total Messages", total_messages)
        st.metric("Your Questions", user_messages)
        st.metric("Bot Responses", bot_messages)
        
        # Audio feature info
        if st.session_state.tts_enabled and bot_messages > 0:
            st.metric("🔊 Audio Responses", f"{bot_messages} available")
        
        # Last response details
        if st.session_state.messages:
            last_message = st.session_state.messages[-1]
            if last_message["role"] == "assistant" and "details" in last_message:
                st.subheader("🔍 Last Response Details")
                details = last_message["details"]
                
                st.metric("Processing Time", f"{details.get('processing_time', 0):.2f}s")
                st.metric("Sources Used", len(details.get('retrieved_chunks', [])))
                
                if details.get('matched_topics'):
                    st.write("**Topics Identified:**")
                    for topic in details['matched_topics']:
                        st.write(f"• {topic}")
                
                if details.get('personalization_applied'):
                    st.success("✅ Personalized Response")
                else:
                    st.info("ℹ️ General Response")
    
    # Process query submission
    if submit_button and query:
        process_query(query, STUDENT_TYPES[selected_type], weak_subjects)

def process_query(query: str, user_type: str, weak_subjects: List[str]):
    """Process a user query and display the response"""
    # Add user message to chat
    user_message = {
        "role": "user",
        "content": query,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    st.session_state.messages.append(user_message)
    
    # Show loading spinner
    with st.spinner("🤔 Thinking..."):
        # Call the API
        response = call_chat_api(query, user_type, weak_subjects)
        
        if response:
            # Add bot response to chat
            bot_message = {
                "role": "assistant", 
                "content": response["answer"],
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "details": response
            }
            st.session_state.messages.append(bot_message)
            
            # Show source chunks in sidebar
            if response.get("retrieved_chunks"):
                with st.sidebar:
                    st.markdown("---")
                    display_source_chunks(response["retrieved_chunks"])
        else:
            # Add error message
            error_message = {
                "role": "assistant",
                "content": "Sorry, I couldn't process your question right now. Please try again later.",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.messages.append(error_message)
    
    # Refresh the page to show new messages
    st.rerun()

if __name__ == "__main__":
    main()
