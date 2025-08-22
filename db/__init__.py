"""
Database module for Supabase integration.
"""

from .connection import get_supabase_client, test_connection, close_connection
from .schema import create_tables, check_tables_exist, initialize_database

__all__ = [
    'get_supabase_client', 
    'test_connection', 
    'close_connection',
    'create_tables',
    'check_tables_exist', 
    'initialize_database'
]