#!/usr/bin/env python3
"""
Script to seed the database with Gemini API keys from the environment variables
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, select
from backend.app.database import engine, init_db
from backend.app.models.api_key import GeminiApiKey
from datetime import datetime

# Load environment variables
project_root = Path(__file__).parent
os.chdir(project_root)
load_dotenv()

def seed_api_keys():
    """Seed the database with API keys from environment variables"""
    try:
        # Initialize database tables
        init_db()
        
        # Get API keys from environment
        gemini_api_keys_str = os.getenv('GEMINI_API_KEYS', '')
        if not gemini_api_keys_str:
            print("No GEMINI_API_KEYS found in environment variables")
            return
        
        # Split the keys
        api_keys = [key.strip() for key in gemini_api_keys_str.split(',') if key.strip()]
        
        if not api_keys:
            print("No valid API keys found")
            return
        
        # Create a session
        with Session(engine) as session:
            print(f"Found {len(api_keys)} API keys to seed")
            
            for i, api_key in enumerate(api_keys, 1):
                # Check if key already exists in the database
                existing_key = session.exec(
                    select(GeminiApiKey).where(GeminiApiKey.key == api_key)
                ).first()
                
                if existing_key:
                    print(f"API key #{i} already exists in database, skipping...")
                    continue
                
                # Create new API key object
                new_api_key = GeminiApiKey(
                    key=api_key,
                    description=f"Gemini API Key #{i} (Seeded)",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    usage_count=0
                )
                
                session.add(new_api_key)
                print(f"Added API key #{i} to database")
            
            session.commit()
            print(f"Successfully seeded {len(api_keys)} API keys to the database!")
    
    except Exception as e:
        print(f"Error seeding API keys: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_api_keys()