"""
Check inventory tool for automotive vehicles.

Provides comprehensive vehicle inventory search with filtering capabilities.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


async def check_inventory(
    category: Optional[str] = None,        # "sedan", "suv", "truck", "coupe"
    model_name: Optional[str] = None,      # Simple text search in brand+model
    min_price: Optional[int] = None,       # Price in dollars
    max_price: Optional[int] = None,       # Price in dollars
    features: Optional[List[str]] = None,  # Must have ALL these features
    status: str = "available"              # "available", "sold", "reserved", "all"
) -> Dict[str, Any]:
    """
    Search vehicle inventory with comprehensive filtering options.
    
    Args:
        category: Vehicle category filter
        model_name: Text search in brand and model fields
        min_price: Minimum price filter in dollars
        max_price: Maximum price filter in dollars
        features: List of required features (must have ALL)
        status: Inventory status filter
        
    Returns:
        Dict containing vehicles list, total count, and applied filters
        
    Raises:
        ValueError: For invalid parameters
        Exception: For database connection or query errors
    """
    from db import get_supabase_client, initialize_database
    
    # Input validation
    _validate_inputs(category, model_name, min_price, max_price, features, status)
    
    try:
        # Ensure database is initialized
        await initialize_database()
        
        # Get database client
        client = get_supabase_client()
        
        # Build query with filters
        query = _build_inventory_query(client, category, model_name, min_price, max_price, features, status)
        
        # Execute query
        response = query.execute()
        
        # Process and format results
        result = _format_inventory_response(response.data, category, model_name, min_price, max_price, features, status)
        
        logger.info(f"Found {result['total_count']} vehicles matching filters")
        return result
        
    except Exception as e:
        logger.error(f"Error searching inventory: {str(e)}")
        raise Exception(f"Inventory search failed: {str(e)}")


def _validate_inputs(category, model_name, min_price, max_price, features, status):
    """Validate input parameters."""
    valid_categories = ['sedan', 'suv', 'truck', 'coupe']
    valid_statuses = ['available', 'sold', 'reserved', 'all']
    
    if category and category not in valid_categories:
        raise ValueError(f"Invalid category '{category}'. Must be one of: {valid_categories}")
    
    if status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")
    
    if min_price is not None and min_price < 0:
        raise ValueError("Price cannot be negative")
    
    if max_price is not None and max_price < 0:
        raise ValueError("Price cannot be negative")
    
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ValueError("min_price cannot be greater than max_price")


def _build_inventory_query(client, category, model_name, min_price, max_price, features, status):
    """Build Supabase query with all filters applied."""
    
    # Base query joining inventory with vehicles
    query = client.table('inventory').select("""
        id,
        vehicle_id,
        vin,
        color,
        features,
        status,
        current_price,
        expected_delivery_date,
        vehicles!inner(
            id,
            brand,
            model,
            year,
            category,
            is_active
        )
    """)
    
    # Filter by vehicle status (only active vehicles unless specified)
    query = query.eq('vehicles.is_active', True)
    
    # Filter by inventory status
    if status != 'all':
        query = query.eq('status', status)
    
    # Filter by category
    if category:
        query = query.eq('vehicles.category', category)
    
    # Filter by model name (text search in brand or model)
    if model_name:
        query = query.or_(f'vehicles.brand.ilike.%{model_name}%,vehicles.model.ilike.%{model_name}%')
    
    # Filter by price range (convert dollars to cents)
    if min_price is not None:
        min_price_cents = int(min_price * 100)
        query = query.gte('current_price', min_price_cents)
    
    if max_price is not None:
        max_price_cents = int(max_price * 100)
        query = query.lte('current_price', max_price_cents)
    
    # Filter by features (must have ALL specified features)
    if features and len(features) > 0:
        for feature in features:
            query = query.contains('features', [feature])
    
    # Order by price (ascending)
    query = query.order('current_price')
    
    return query


def _format_inventory_response(data, category, model_name, min_price, max_price, features, status):
    """Format the response data into agent-friendly structure."""
    
    vehicles = []
    for item in data:
        vehicle_info = item['vehicles']
        
        vehicles.append({
            'inventory_id': item['id'],
            'vehicle_id': item['vehicle_id'],
            'brand': vehicle_info['brand'],
            'model': vehicle_info['model'],
            'category': vehicle_info['category'],
            'color': item['color'],
            'features': item['features'],
            'price': int(item['current_price'] / 100),  # Convert cents to dollars
            'status': item['status'],
            'delivery_date': item['expected_delivery_date']
        })
    
    # Build filters_applied object (only include non-None/non-default values)
    filters_applied = {}
    if category:
        filters_applied['category'] = category
    if model_name:
        filters_applied['model_name'] = model_name
    if min_price is not None:
        filters_applied['min_price'] = min_price
    if max_price is not None:
        filters_applied['max_price'] = max_price
    if features and len(features) > 0:
        filters_applied['features'] = features
    if status != 'available':  # Only include if not default
        filters_applied['status'] = status
    
    return {
        'vehicles': vehicles,
        'total_count': len(vehicles),
        'filters_applied': filters_applied
    }