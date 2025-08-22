"""
Database initialization script for automotive inventory system.

Run this script to set up the database schema and verify connection.
"""

import asyncio
import logging
from typing import Dict, Any
from .connection import test_connection
from .schema import initialize_database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main() -> Dict[str, Any]:
    """
    Main initialization function.
    
    Returns:
        Dict containing initialization results
    """
    try:
        logger.info("=== Automotive Inventory Database Initialization ===")
        
        # Test database connection
        logger.info("Step 1: Testing database connection...")
        connection_result = await test_connection()
        
        if connection_result['status'] != 'connected':
            logger.error("Database connection failed!")
            return {
                'success': False,
                'error': 'Database connection failed',
                'details': connection_result
            }
        
        logger.info(f"✅ Connection successful: {connection_result['message']}")
        
        # Initialize database schema
        logger.info("Step 2: Initializing database schema...")
        init_result = await initialize_database()
        
        logger.info(f"✅ Database initialization: {init_result['message']}")
        
        # Final status
        final_result = {
            'success': True,
            'connection': connection_result,
            'initialization': init_result
        }
        
        logger.info("=== Database initialization completed successfully ===")
        return final_result
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Run the initialization
    result = asyncio.run(main())
    
    if result['success']:
        print("\n🎉 Database is ready for automotive inventory tools!")
    else:
        print(f"\n❌ Database initialization failed: {result.get('error', 'Unknown error')}")
        exit(1)