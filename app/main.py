"""
Main application entry point.
"""
import os
from app.api import start_api
from dotenv import load_dotenv

def main():
    """Application entry point"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Start the API
    start_api()

if __name__ == "__main__":
    main() 