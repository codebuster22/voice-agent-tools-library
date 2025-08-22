"""
Supabase database connection and configuration.
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global client instance (singleton pattern for connection reuse)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create a Supabase client instance.
    
    Returns:
        Client: Authenticated Supabase client
        
    Raises:
        ValueError: If required environment variables are missing
        Exception: If connection fails
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing required environment variables: SUPABASE_URL and SUPABASE_KEY must be set"
        )
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
        
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise Exception(f"Database connection failed: {str(e)}")


async def test_connection() -> dict:
    """
    Test the Supabase database connection.
    
    Returns:
        dict: Connection status and basic info
        
    Raises:
        Exception: If connection test fails
    """
    try:
        client = get_supabase_client()
        
        # Simple query to test connection
        response = client.table('vehicles').select('count', count='exact').limit(0).execute()
        
        return {
            'status': 'connected',
            'url': os.getenv('SUPABASE_URL', '').split('@')[1] if '@' in os.getenv('SUPABASE_URL', '') else 'unknown',
            'message': 'Database connection successful'
        }
        
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Database connection failed'
        }


def close_connection():
    """
    Close the Supabase client connection (cleanup).
    """
    global _supabase_client
    if _supabase_client is not None:
        _supabase_client = None
        logger.info("Supabase client connection closed")