"""
Database connection utilities for Supabase and PostgreSQL.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    
    Returns:
        Client: Supabase client
    """
    supabase_url = os.getenv('SUPABASE_URL', 'https://vcoshhbfaymqyqjsytcw.supabase.co')
    supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjb3NoaGJmYXltcXlxanN5dGN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE5MTE2NTMsImV4cCI6MjA2NzQ4NzY1M30.PUqs39Cfd2hh2_Yu4-ReX5pI9em2jYlE3TrTlV_7IA0')
    
    return create_client(supabase_url, supabase_key)

def get_db_engine():
    """
    Create and return a SQLAlchemy engine for connecting to Supabase PostgreSQL.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    # Database connection parameters
    db_host = os.getenv('DB_HOST', 'db.vcoshhbfaymqyqjsytcw.supabase.co')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'boolmind')  # Replace with your actual DB password
    
    # Create connection string
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Create engine
    return create_engine(connection_string)

def test_connection():
    """
    Test database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        # Test Supabase connection
        supabase = get_supabase_client()
        response = supabase.table('_dummy').select('*').limit(1).execute()
        print("Supabase connection successful")
        
        # Test PostgreSQL connection
        engine = get_db_engine()
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("PostgreSQL connection successful")
        
        return True
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
