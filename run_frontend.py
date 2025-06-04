#!/usr/bin/env python
"""
Frontend Launcher for RAG Science Chatbot
Run this script to start the Streamlit frontend
"""

import subprocess
import sys
import os
from pathlib import Path

def check_backend_running():
    """Check if the backend is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔬 Starting RAG Science Chatbot Frontend...")
    print("=" * 50)
    
    # Check if backend is running
    if check_backend_running():
        print("✅ Backend is running on http://localhost:8000")
    else:
        print("⚠️  Backend not detected on http://localhost:8000")
        print("   Make sure to start the backend first:")
        print("   python backend/main.py")
        print()
    
    # Get the path to the frontend app
    frontend_path = Path(__file__).parent / "frontend" / "app.py"
    
    if not frontend_path.exists():
        print("❌ Frontend app not found at:", frontend_path)
        sys.exit(1)
    
    print("🚀 Starting Streamlit frontend...")
    print("   Opening in your browser at: http://localhost:8501")
    print("   Press Ctrl+C to stop")
    print()
    
    # Start Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(frontend_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 