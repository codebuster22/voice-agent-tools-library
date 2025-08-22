"""
Direct SQL execution using Supabase Management API.
"""

import httpx
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


async def execute_sql_direct(sql_statements: List[str]) -> Dict[str, Any]:
    """
    Execute SQL statements directly using Supabase's database connection.
    
    This uses the Management API to execute raw SQL.
    
    Args:
        sql_statements: List of SQL statements to execute
        
    Returns:
        Dict containing execution results
        
    Raises:
        Exception: If SQL execution fails
    """
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not service_key:
        service_key = os.getenv('SUPABASE_KEY')
        logger.warning("Using regular API key instead of service key")
    
    if not supabase_url or not service_key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    
    # Extract project ref from URL
    project_ref = supabase_url.replace('https://', '').split('.')[0]
    
    results = {
        'executed': [],
        'failed': [],
        'errors': []
    }
    
    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Use the database API endpoint for direct SQL execution
    sql_endpoint = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, sql in enumerate(sql_statements):
            try:
                response = await client.post(
                    sql_endpoint,
                    headers=headers,
                    json={'query': sql}
                )
                
                if response.status_code in [200, 201]:
                    results['executed'].append(f"statement_{i+1}")
                    logger.info(f"SQL statement {i+1} executed successfully")
                else:
                    error_msg = f"SQL statement {i+1} failed: HTTP {response.status_code} - {response.text}"
                    results['failed'].append(f"statement_{i+1}")
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"SQL statement {i+1} failed: {str(e)}"
                results['failed'].append(f"statement_{i+1}")
                results['errors'].append(error_msg)
                logger.error(error_msg)
    
    return results


async def execute_sql_via_psycopg(sql_statements: List[str]) -> Dict[str, Any]:
    """
    Alternative: Execute SQL using direct PostgreSQL connection.
    
    This requires the database connection string and psycopg2.
    """
    try:
        import asyncpg
    except ImportError:
        raise Exception("asyncpg package required for direct PostgreSQL connection. Install with: pip install asyncpg")
    
    # Get connection string from environment
    db_url = os.getenv('DATABASE_URL')  # Full PostgreSQL connection string
    
    if not db_url:
        raise Exception("DATABASE_URL environment variable required for direct PostgreSQL connection")
    
    results = {
        'executed': [],
        'failed': [],
        'errors': []
    }
    
    try:
        # Connect to PostgreSQL directly
        conn = await asyncpg.connect(db_url)
        
        for i, sql in enumerate(sql_statements):
            try:
                await conn.execute(sql)
                results['executed'].append(f"statement_{i+1}")
                logger.info(f"SQL statement {i+1} executed successfully")
                
            except Exception as e:
                error_msg = f"SQL statement {i+1} failed: {str(e)}"
                results['failed'].append(f"statement_{i+1}")
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        await conn.close()
        
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")
    
    return results