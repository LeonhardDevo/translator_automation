#!/usr/bin/env python3
"""
Development script to run the AI Translation Service server
"""
import os
import sys
from pathlib import Path

# Change to the project root directory to ensure proper module resolution
project_root = Path(__file__).parent.parent  # Go up from backend/start_server.py to project root
os.chdir(project_root)  # Change working directory to project root
sys.path.insert(0, str(project_root))  # Also add to Python path

# Set environment variables to use the .env file
from dotenv import load_dotenv
load_dotenv()

import uvicorn

def main():
    print("="*60)
    print("  AI TRANSLATION SERVICE - DEVELOPMENT MODE")
    print("  Secure translation service with proper safety measures")
    print("="*60)
    # Get configuration from environment or use defaults
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '8002'))  # Use port 8002 to avoid conflicts
    env = os.getenv('ENVIRONMENT', 'development').lower()

    
    print(f"[INFO] Starting server on {host}:{port}")
    print(f"[INFO] Environment: {env}")
    # Run the server with development settings
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()