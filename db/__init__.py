"""
Database module for Supabase integration.
"""

from .connection import get_supabase_client, close_connection

__all__ = [
    'get_supabase_client', 
    'close_connection'
]