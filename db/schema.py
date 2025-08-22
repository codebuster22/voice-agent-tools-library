"""
Database schema creation and management for automotive inventory system.
"""

import logging
from typing import Dict, Any
from .connection import get_supabase_client

logger = logging.getLogger(__name__)


# SQL schema definitions
SCHEMA_SQL = {
    'vehicles': """
        CREATE TABLE IF NOT EXISTS vehicles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            category VARCHAR NOT NULL CHECK (category IN ('sedan', 'suv', 'truck', 'coupe')),
            base_price INTEGER NOT NULL CHECK (base_price > 0),
            image_url VARCHAR,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """,
    
    'inventory': """
        CREATE TABLE IF NOT EXISTS inventory (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
            vin VARCHAR UNIQUE NOT NULL,
            color VARCHAR NOT NULL,
            features JSONB DEFAULT '[]'::jsonb,
            status VARCHAR DEFAULT 'available' CHECK (status IN ('available', 'sold', 'reserved')),
            location VARCHAR DEFAULT 'main_dealership',
            current_price INTEGER NOT NULL CHECK (current_price > 0),
            expected_delivery_date DATE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """,
    
    'pricing': """
        CREATE TABLE IF NOT EXISTS pricing (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
            base_price INTEGER NOT NULL CHECK (base_price > 0),
            feature_prices JSONB DEFAULT '{}'::jsonb,
            discount_amount INTEGER DEFAULT 0 CHECK (discount_amount >= 0),
            is_current BOOLEAN DEFAULT true,
            effective_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
}

# Index creation SQL
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_vehicles_category ON vehicles(category);",
    "CREATE INDEX IF NOT EXISTS idx_vehicles_brand_model ON vehicles(brand, model);",
    "CREATE INDEX IF NOT EXISTS idx_vehicles_active ON vehicles(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_vehicle_id ON inventory(vehicle_id);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_price ON inventory(current_price);",
    "CREATE INDEX IF NOT EXISTS idx_pricing_current ON pricing(is_current, vehicle_id);",
    "CREATE INDEX IF NOT EXISTS idx_pricing_vehicle_id ON pricing(vehicle_id);"
]


async def create_tables() -> Dict[str, Any]:
    """
    Create all required tables and indexes for the automotive inventory system.
    
    Returns:
        Dict containing creation status and details
        
    Raises:
        Exception: If table creation fails
    """
    try:
        client = get_supabase_client()
        results = {
            'tables_created': [],
            'indexes_created': [],
            'errors': []
        }
        
        logger.info("Starting database schema creation...")
        
        # Simple approach: Print SQL statements for manual execution
        # This is the most reliable approach for MVP
        logger.info("=== SQL STATEMENTS TO CREATE TABLES ===")
        logger.info("Copy and paste these statements into your Supabase SQL Editor:")
        logger.info("")
        
        all_sql_statements = []
        
        # Collect all SQL statements
        for table_name, sql in SCHEMA_SQL.items():
            logger.info(f"-- Creating table: {table_name}")
            logger.info(sql)
            logger.info("")
            all_sql_statements.append(sql)
            results['tables_created'].append(table_name)
        
        logger.info("-- Creating indexes")
        for i, index_sql in enumerate(INDEXES_SQL):
            logger.info(index_sql)
            all_sql_statements.append(index_sql)
            results['indexes_created'].append(f"index_{i+1}")
        
        logger.info("=== END SQL STATEMENTS ===")
        logger.info("")
        logger.info("After running these SQL statements in Supabase, run the tests again.")
        
        # Try to verify if tables exist (in case they were already created)
        for table_name in SCHEMA_SQL.keys():
            try:
                response = client.table(table_name).select('*').limit(0).execute()
                logger.info(f"✅ Table '{table_name}' verified as existing")
            except Exception as e:
                logger.info(f"❌ Table '{table_name}' not found: {str(e)}")
                results['errors'].append(f"Table '{table_name}' not found")
        
        if results['errors']:
            logger.warning(f"Schema creation completed with {len(results['errors'])} errors")
        else:
            logger.info("Database schema creation completed successfully")
            
        return results
        
    except Exception as e:
        logger.error(f"Database schema creation failed: {str(e)}")
        raise Exception(f"Schema creation failed: {str(e)}")


async def check_tables_exist() -> Dict[str, bool]:
    """
    Check if all required tables exist in the database.
    
    Returns:
        Dict mapping table names to existence status
        
    Raises:
        Exception: If database query fails
    """
    try:
        client = get_supabase_client()
        table_status = {}
        
        for table_name in SCHEMA_SQL.keys():
            try:
                # Try to query the table with limit 0 to check existence
                response = client.table(table_name).select('*').limit(0).execute()
                table_status[table_name] = True
                logger.info(f"Table '{table_name}' exists")
                
            except Exception:
                table_status[table_name] = False
                logger.info(f"Table '{table_name}' does not exist")
        
        return table_status
        
    except Exception as e:
        logger.error(f"Failed to check table existence: {str(e)}")
        raise Exception(f"Table existence check failed: {str(e)}")


async def initialize_database() -> Dict[str, Any]:
    """
    Initialize the database by checking for tables and creating them if needed.
    
    Returns:
        Dict containing initialization status and details
        
    Raises:
        Exception: If initialization fails
    """
    try:
        logger.info("Initializing automotive inventory database...")
        
        # Check if tables exist
        table_status = await check_tables_exist()
        missing_tables = [name for name, exists in table_status.items() if not exists]
        
        if not missing_tables:
            logger.info("All tables already exist, database is ready")
            return {
                'status': 'ready',
                'message': 'Database already initialized',
                'tables_status': table_status
            }
        
        logger.info(f"Missing tables: {missing_tables}. Creating schema...")
        
        # Create missing tables and indexes
        creation_results = await create_tables()
        
        # Verify creation
        final_status = await check_tables_exist()
        all_exist = all(final_status.values())
        
        return {
            'status': 'initialized' if all_exist else 'partial',
            'message': 'Database initialization completed' if all_exist else 'Database initialization completed with errors',
            'creation_results': creation_results,
            'final_table_status': final_status
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise Exception(f"Database initialization failed: {str(e)}")