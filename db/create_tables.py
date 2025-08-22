"""
Script to create Supabase tables programmatically using SQL execution.

This script uses multiple approaches to create tables in Supabase.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from .connection import get_supabase_client
from .schema import SCHEMA_SQL, INDEXES_SQL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables_via_rpc() -> Dict[str, Any]:
    """
    Create tables using Supabase RPC function.
    
    Note: This requires the exec_sql RPC function to be created first in Supabase.
    """
    try:
        client = get_supabase_client()
        results = {'success': [], 'failed': [], 'errors': []}
        
        # First, try to create the exec_sql RPC function
        exec_sql_function = """
        CREATE OR REPLACE FUNCTION exec_sql(sql text)
        RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            EXECUTE sql;
            RETURN 'OK';
        EXCEPTION
            WHEN OTHERS THEN
                RETURN SQLERRM;
        END;
        $$;
        """
        
        try:
            # Try to create the exec_sql function first
            response = client.rpc('exec_sql', {'sql': exec_sql_function}).execute()
            logger.info("exec_sql function created/verified")
        except Exception as e:
            logger.warning(f"Could not create exec_sql function: {e}")
        
        # Create tables
        for table_name, sql in SCHEMA_SQL.items():
            try:
                response = client.rpc('exec_sql', {'sql': sql}).execute()
                if response.data == 'OK':
                    results['success'].append(table_name)
                    logger.info(f"✅ Table '{table_name}' created successfully")
                else:
                    results['failed'].append(table_name)
                    results['errors'].append(f"Table '{table_name}': {response.data}")
                    logger.error(f"❌ Table '{table_name}' failed: {response.data}")
                    
            except Exception as e:
                results['failed'].append(table_name)
                results['errors'].append(f"Table '{table_name}': {str(e)}")
                logger.error(f"❌ Table '{table_name}' failed: {str(e)}")
        
        # Create indexes
        for i, index_sql in enumerate(INDEXES_SQL):
            try:
                response = client.rpc('exec_sql', {'sql': index_sql}).execute()
                if response.data == 'OK':
                    results['success'].append(f"index_{i+1}")
                    logger.info(f"✅ Index {i+1} created successfully")
                else:
                    results['failed'].append(f"index_{i+1}")
                    results['errors'].append(f"Index {i+1}: {response.data}")
                    logger.error(f"❌ Index {i+1} failed: {response.data}")
                    
            except Exception as e:
                results['failed'].append(f"index_{i+1}")
                results['errors'].append(f"Index {i+1}: {str(e)}")
                logger.error(f"❌ Index {i+1} failed: {str(e)}")
        
        return results
        
    except Exception as e:
        logger.error(f"RPC table creation failed: {str(e)}")
        raise


def print_sql_statements():
    """Print all SQL statements for manual execution."""
    print("=" * 60)
    print("SQL STATEMENTS FOR SUPABASE TABLE CREATION")
    print("=" * 60)
    print()
    print("Copy and paste these into your Supabase SQL Editor:")
    print()
    
    # Print table creation statements
    for table_name, sql in SCHEMA_SQL.items():
        print(f"-- Creating table: {table_name}")
        print(sql)
        print()
    
    # Print index creation statements
    print("-- Creating indexes")
    for index_sql in INDEXES_SQL:
        print(index_sql)
        print()
    
    print("=" * 60)
    print("END OF SQL STATEMENTS")
    print("=" * 60)


async def verify_tables_exist() -> Dict[str, bool]:
    """Verify that all required tables exist."""
    try:
        client = get_supabase_client()
        table_status = {}
        
        logger.info("Verifying table existence...")
        
        for table_name in SCHEMA_SQL.keys():
            try:
                response = client.table(table_name).select('*').limit(0).execute()
                table_status[table_name] = True
                logger.info(f"✅ Table '{table_name}' exists")
            except Exception as e:
                table_status[table_name] = False
                logger.info(f"❌ Table '{table_name}' not found: {str(e)}")
        
        return table_status
        
    except Exception as e:
        logger.error(f"Table verification failed: {str(e)}")
        raise


async def main():
    """Main function to create tables."""
    logger.info("=== Supabase Table Creation Script ===")
    
    try:
        # First, verify current state
        logger.info("Step 1: Checking current table state...")
        table_status = await verify_tables_exist()
        
        missing_tables = [name for name, exists in table_status.items() if not exists]
        
        if not missing_tables:
            logger.info("🎉 All tables already exist!")
            return
        
        logger.info(f"Missing tables: {missing_tables}")
        
        # Print SQL statements for manual creation
        logger.info("Step 2: Printing SQL statements for manual creation...")
        print_sql_statements()
        
        # Try RPC creation
        logger.info("Step 3: Attempting automatic creation via RPC...")
        try:
            results = await create_tables_via_rpc()
            
            if results['failed']:
                logger.warning(f"Some operations failed: {results['failed']}")
                logger.info("You may need to run the SQL statements manually.")
            else:
                logger.info("🎉 All tables created successfully!")
                
        except Exception as e:
            logger.error(f"Automatic creation failed: {str(e)}")
            logger.info("Please run the SQL statements manually in Supabase SQL Editor.")
        
        # Final verification
        logger.info("Step 4: Final verification...")
        final_status = await verify_tables_exist()
        
        all_exist = all(final_status.values())
        if all_exist:
            logger.info("🎉 Database is ready for inventory tools!")
        else:
            missing = [name for name, exists in final_status.items() if not exists]
            logger.warning(f"Still missing tables: {missing}")
            
    except Exception as e:
        logger.error(f"Table creation script failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())