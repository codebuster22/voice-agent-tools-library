"""
Get vehicle details tool for automotive inventory.

Provides comprehensive information about specific vehicles.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


async def get_vehicle_details(
    vehicle_id: Optional[str] = None,      # Vehicle ID to get details for
    inventory_id: Optional[str] = None,    # Specific inventory item ID
    include_pricing: bool = True,          # Include detailed pricing information
    include_similar: bool = False          # Include similar vehicle suggestions
) -> Dict[str, Any]:
    """
    Get comprehensive details about a specific vehicle or inventory item.
    
    Args:
        vehicle_id: UUID of the vehicle to get details for
        inventory_id: UUID of specific inventory item (preferred)
        include_pricing: Whether to include detailed pricing breakdown
        include_similar: Whether to include similar vehicle suggestions
        
    Returns:
        Dict containing comprehensive vehicle information
        
    Raises:
        ValueError: For invalid parameters
        Exception: For database connection or query errors
    """
    from db.connection import get_supabase_client
    
    try:
        client = get_supabase_client()
        
        # Input validation - if no specific vehicle requested, return all vehicle details
        if not vehicle_id and not inventory_id:
            return await _get_all_vehicle_details(client, include_pricing, include_similar)
        
        # Get vehicle and inventory information
        if inventory_id:
            vehicle_data, inventory_data = await _get_inventory_details(client, inventory_id)
        else:
            vehicle_data, inventory_data = await _get_vehicle_details(client, vehicle_id)
        
        # Get pricing information if requested
        pricing_data = None
        if include_pricing:
            pricing_data = await _get_pricing_details(client, vehicle_data['id'])
        
        # Get similar vehicles if requested
        similar_vehicles = []
        if include_similar and inventory_data:
            try:
                from .get_similar_vehicles import get_similar_vehicles
                similar_response = await get_similar_vehicles(
                    reference_vehicle_id=vehicle_data['id'],
                    max_results=3,
                    include_unavailable=False
                )
                similar_vehicles = similar_response.get('alternatives', [])
            except Exception as e:
                logger.warning(f"Could not get similar vehicles: {str(e)}")
        
        # Format comprehensive response
        result = _format_vehicle_details_response(
            vehicle_data, 
            inventory_data, 
            pricing_data, 
            similar_vehicles
        )
        
        logger.info(f"Vehicle details retrieved for {vehicle_data['brand']} {vehicle_data['model']}")
        return result
        
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "invalid input syntax for type uuid" in error_msg:
            if inventory_id:
                raise ValueError(f"Invalid inventory_id format: {inventory_id}")
            elif vehicle_id:
                raise ValueError(f"Invalid vehicle_id format: {vehicle_id}")
        logger.error(f"Error getting vehicle details: {error_msg}")
        raise Exception(f"Vehicle details query failed: {error_msg}")


async def _get_inventory_details(client, inventory_id: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Get vehicle details via inventory ID."""
    
    response = client.table('inventory').select("""
        id,
        vehicle_id,
        vin,
        color,
        features,
        status,
        current_price,
        expected_delivery_date,
        location,
        created_at,
        vehicles!inner(
            id,
            brand,
            model,
            year,
            category,
            base_price,
            image_url,
            is_active,
            created_at,
            updated_at
        )
    """).eq('id', inventory_id).execute()
    
    if not response.data:
        raise ValueError(f"Inventory item '{inventory_id}' not found")
    
    inventory_item = response.data[0]
    vehicle_data = inventory_item['vehicles']
    
    if not vehicle_data['is_active']:
        raise ValueError("Vehicle is no longer active")
    
    return vehicle_data, inventory_item


async def _get_vehicle_details(client, vehicle_id: str) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Get vehicle details via vehicle ID."""
    
    # Get vehicle information
    vehicle_response = client.table('vehicles').select("""
        id,
        brand,
        model,
        year,
        category,
        base_price,
        image_url,
        is_active,
        created_at,
        updated_at
    """).eq('id', vehicle_id).execute()
    
    if not vehicle_response.data:
        raise ValueError(f"Vehicle '{vehicle_id}' not found")
    
    vehicle_data = vehicle_response.data[0]
    
    if not vehicle_data['is_active']:
        raise ValueError("Vehicle is no longer active")
    
    # Get sample inventory item (prefer available ones)
    inventory_response = client.table('inventory').select("""
        id,
        vehicle_id,
        vin,
        color,
        features,
        status,
        current_price,
        expected_delivery_date,
        location,
        created_at
    """).eq('vehicle_id', vehicle_id).order('status').execute()  # This will put 'available' first alphabetically
    
    inventory_data = inventory_response.data[0] if inventory_response.data else None
    
    return vehicle_data, inventory_data


async def _get_pricing_details(client, vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive pricing information."""
    
    response = client.table('pricing').select("""
        id,
        base_price,
        feature_prices,
        discount_amount,
        is_current,
        effective_date,
        created_at
    """).eq('vehicle_id', vehicle_id).order('is_current', desc=True).order('effective_date', desc=True).execute()
    
    return response.data[0] if response.data else None


def _format_vehicle_details_response(
    vehicle_data: Dict[str, Any], 
    inventory_data: Optional[Dict[str, Any]], 
    pricing_data: Optional[Dict[str, Any]], 
    similar_vehicles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Format comprehensive vehicle details response."""
    
    # Basic vehicle information
    result = {
        'vehicle': {
            'id': vehicle_data['id'],
            'brand': vehicle_data['brand'],
            'model': vehicle_data['model'],
            'year': vehicle_data['year'],
            'category': vehicle_data['category'],
            'image_url': vehicle_data.get('image_url'),
            'is_active': vehicle_data['is_active']
        },
        'specifications': _get_vehicle_specifications(vehicle_data),
        'availability': _get_availability_info(inventory_data),
        'features': _get_features_info(inventory_data, pricing_data)
    }
    
    # Add pricing information if available
    if pricing_data or inventory_data:
        result['pricing'] = _get_pricing_info(vehicle_data, inventory_data, pricing_data)
    
    # Add inventory-specific information if available
    if inventory_data:
        result['inventory'] = {
            'inventory_id': inventory_data['id'],
            'vin': inventory_data['vin'],
            'color': inventory_data['color'],
            'status': inventory_data['status'],
            'location': inventory_data['location'],
            'expected_delivery_date': inventory_data.get('expected_delivery_date')
        }
    
    # Add similar vehicles if requested
    if similar_vehicles:
        result['similar_vehicles'] = similar_vehicles[:3]  # Limit to 3
    
    # Add warranty and additional information
    result['additional_info'] = _get_additional_info(vehicle_data)
    
    return result


def _get_vehicle_specifications(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate vehicle specifications based on category and brand."""
    
    category = vehicle_data['category']
    brand = vehicle_data['brand'].lower()
    year = vehicle_data['year']
    
    # Basic specs that apply to all vehicles
    specs = {
        'year': year,
        'category': category.title(),
        'fuel_type': 'Gasoline',  # Default
        'transmission': 'Automatic',
        'drivetrain': 'FWD'  # Default
    }
    
    # Category-specific specifications
    if category == 'sedan':
        specs.update({
            'doors': 4,
            'seating_capacity': 5,
            'cargo_space_cubic_feet': 15,
            'fuel_economy_city_mpg': 28,
            'fuel_economy_highway_mpg': 36
        })
    elif category == 'suv':
        specs.update({
            'doors': 4,
            'seating_capacity': 7,
            'cargo_space_cubic_feet': 25,
            'fuel_economy_city_mpg': 22,
            'fuel_economy_highway_mpg': 30,
            'drivetrain': 'AWD'
        })
    elif category == 'truck':
        specs.update({
            'doors': 4,
            'seating_capacity': 5,
            'bed_length_feet': 6.5,
            'towing_capacity_lbs': 8000,
            'fuel_economy_city_mpg': 18,
            'fuel_economy_highway_mpg': 24,
            'drivetrain': '4WD'
        })
    elif category == 'coupe':
        specs.update({
            'doors': 2,
            'seating_capacity': 4,
            'cargo_space_cubic_feet': 12,
            'fuel_economy_city_mpg': 24,
            'fuel_economy_highway_mpg': 32
        })
    
    # Brand-specific adjustments
    if 'tesla' in brand:
        specs.update({
            'fuel_type': 'Electric',
            'range_miles': 300,
            'charging_time_hours': 8
        })
        specs.pop('fuel_economy_city_mpg', None)
        specs.pop('fuel_economy_highway_mpg', None)
    elif 'bmw' in brand or 'mercedes' in brand or 'audi' in brand:
        specs['transmission'] = 'Automatic (Premium)'
        if category in ['sedan', 'coupe']:
            specs['drivetrain'] = 'RWD'
    
    return specs


def _get_availability_info(inventory_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get availability information."""
    
    if not inventory_data:
        return {
            'status': 'unknown',
            'message': 'No inventory information available',
            'in_stock': False
        }
    
    status = inventory_data['status']
    location = inventory_data['location']
    delivery_date = inventory_data.get('expected_delivery_date')
    
    availability = {
        'status': status,
        'location': location,
        'in_stock': status == 'available',
        'delivery_date': delivery_date
    }
    
    # Add user-friendly message
    if status == 'available':
        if location == 'main_dealership':
            availability['message'] = 'Available for immediate viewing and purchase'
        else:
            availability['message'] = f'Available at {location}, can be transferred to main dealership'
    elif status == 'reserved':
        availability['message'] = 'Currently reserved by another customer'
    elif status == 'sold':
        availability['message'] = 'This vehicle has been sold'
    else:
        availability['message'] = f'Vehicle status: {status}'
    
    return availability


def _get_features_info(inventory_data: Optional[Dict[str, Any]], pricing_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get features and options information."""
    
    included_features = inventory_data.get('features', []) if inventory_data else []
    feature_prices = pricing_data.get('feature_prices', {}) if pricing_data else {}
    
    # Organize features by category
    feature_categories = {
        'comfort': [],
        'technology': [],
        'safety': [],
        'performance': [],
        'exterior': [],
        'other': []
    }
    
    # Categorize features
    for feature in included_features:
        feature_lower = feature.lower()
        if any(word in feature_lower for word in ['leather', 'heated', 'cooled', 'climate', 'seat', 'comfort']):
            feature_categories['comfort'].append(feature)
        elif any(word in feature_lower for word in ['nav', 'bluetooth', 'usb', 'display', 'audio', 'tech', 'camera', 'screen']):
            feature_categories['technology'].append(feature)
        elif any(word in feature_lower for word in ['safety', 'brake', 'warning', 'assist', 'blind', 'collision', 'airbag']):
            feature_categories['safety'].append(feature)
        elif any(word in feature_lower for word in ['engine', 'turbo', 'sport', 'performance', 'suspension']):
            feature_categories['performance'].append(feature)
        elif any(word in feature_lower for word in ['wheel', 'paint', 'roof', 'exterior', 'trim', 'light']):
            feature_categories['exterior'].append(feature)
        else:
            feature_categories['other'].append(feature)
    
    # Remove empty categories
    feature_categories = {k: v for k, v in feature_categories.items() if v}
    
    return {
        'included_features': included_features,
        'features_by_category': feature_categories,
        'total_features': len(included_features),
        'feature_pricing_available': len(feature_prices) > 0
    }


def _get_pricing_info(vehicle_data: Dict[str, Any], inventory_data: Optional[Dict[str, Any]], pricing_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get comprehensive pricing information."""
    
    base_price = vehicle_data['base_price']
    current_price = inventory_data['current_price'] if inventory_data else base_price
    
    pricing_info = {
        'base_price_dollars': base_price // 100,
        'current_price_dollars': current_price // 100,
        'price_currency': 'USD'
    }
    
    if pricing_data:
        discount = pricing_data.get('discount_amount', 0)
        if discount > 0:
            pricing_info['discount_applied_dollars'] = discount // 100
            pricing_info['savings'] = discount // 100
        
        feature_prices = pricing_data.get('feature_prices', {})
        if feature_prices:
            pricing_info['available_options'] = {}
            for feature, price in feature_prices.items():
                pricing_info['available_options'][feature] = price // 100
    
    # Calculate financing estimate (rough)
    monthly_payment = _estimate_monthly_payment(current_price // 100)
    pricing_info['estimated_monthly_payment_dollars'] = monthly_payment
    
    return pricing_info


def _get_additional_info(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get additional vehicle information."""
    
    year = vehicle_data['year']
    brand = vehicle_data['brand']
    
    return {
        'warranty': {
            'basic_years': 3,
            'basic_miles': 36000,
            'powertrain_years': 5,
            'powertrain_miles': 60000
        },
        'expected_depreciation': {
            'year_1_percent': 15,
            'year_3_percent': 35,
            'year_5_percent': 55
        },
        'insurance_group': _estimate_insurance_group(vehicle_data),
        'maintenance': {
            'first_service_miles': 7500,
            'service_interval_miles': 7500,
            'estimated_annual_cost_dollars': _estimate_maintenance_cost(vehicle_data)
        }
    }


def _estimate_insurance_group(vehicle_data: Dict[str, Any]) -> str:
    """Estimate insurance group based on vehicle characteristics."""
    
    category = vehicle_data['category']
    year = vehicle_data['year']
    brand = vehicle_data['brand'].lower()
    
    if 'bmw' in brand or 'mercedes' in brand or 'audi' in brand:
        return 'Premium'
    elif category == 'truck':
        return 'Standard'
    elif category == 'coupe':
        return 'Sport'
    else:
        return 'Standard'


def _estimate_maintenance_cost(vehicle_data: Dict[str, Any]) -> int:
    """Estimate annual maintenance cost."""
    
    category = vehicle_data['category']
    brand = vehicle_data['brand'].lower()
    
    base_cost = 800  # Base maintenance cost
    
    if 'bmw' in brand or 'mercedes' in brand or 'audi' in brand:
        base_cost *= 1.5
    elif 'toyota' in brand or 'honda' in brand:
        base_cost *= 0.8
    
    if category == 'truck':
        base_cost *= 1.2
    elif category == 'coupe':
        base_cost *= 1.1
    
    return int(base_cost)


def _estimate_monthly_payment(price_dollars: int, down_payment_percent: float = 10, interest_rate: float = 6.5, term_years: int = 5) -> int:
    """Estimate monthly payment for financing."""
    
    down_payment = price_dollars * (down_payment_percent / 100)
    loan_amount = price_dollars - down_payment
    monthly_rate = (interest_rate / 100) / 12
    num_payments = term_years * 12
    
    if monthly_rate == 0:
        monthly_payment = loan_amount / num_payments
    else:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return int(monthly_payment)


async def _get_all_vehicle_details(client, include_pricing: bool, include_similar: bool) -> Dict[str, Any]:
    """Get details for all available vehicles when no specific vehicle requested."""
    
    # Query all available vehicles with basic information
    response = client.table('vehicles').select("""
        id,
        brand,
        model,
        year,
        category,
        base_price,
        is_active,
        inventory!inner(
            id,
            vin,
            color,
            features,
            current_price,
            status
        )
    """).eq('is_active', True).eq('inventory.status', 'available').execute()
    
    if not response.data:
        return {
            'message': 'No vehicles available in inventory',
            'vehicles': []
        }
    
    vehicles_summary = []
    categories = {}
    
    for vehicle_record in response.data:
        vehicle_data = vehicle_record
        inventory_items = vehicle_record.get('inventory', [])
        
        for inventory_item in inventory_items:
            # Basic vehicle info
            vehicle_info = {
                'vehicle_id': vehicle_data['id'],
                'inventory_id': inventory_item['id'],
                'brand': vehicle_data['brand'],
                'model': vehicle_data['model'],
                'year': vehicle_data['year'],
                'category': vehicle_data['category'],
                'color': inventory_item['color'],
                'vin': inventory_item['vin'],
                'features': inventory_item.get('features', []),
                'current_price_dollars': inventory_item['current_price'] // 100,
                'status': inventory_item['status']
            }
            
            # Add pricing if requested
            if include_pricing:
                vehicle_info['financing_estimate'] = {
                    'estimated_monthly_payment_dollars': _estimate_monthly_payment(inventory_item['current_price'] // 100)
                }
            
            vehicles_summary.append(vehicle_info)
            
            # Category statistics
            category = vehicle_data['category']
            if category not in categories:
                categories[category] = {'count': 0, 'price_range': {'min': None, 'max': None}}
            
            categories[category]['count'] += 1
            price = inventory_item['current_price'] // 100
            
            if categories[category]['price_range']['min'] is None or price < categories[category]['price_range']['min']:
                categories[category]['price_range']['min'] = price
            if categories[category]['price_range']['max'] is None or price > categories[category]['price_range']['max']:
                categories[category]['price_range']['max'] = price
    
    return {
        'message': f'Found {len(vehicles_summary)} vehicles available in inventory',
        'total_vehicles': len(vehicles_summary),
        'vehicles': vehicles_summary,
        'inventory_summary': {
            'by_category': categories,
            'helpful_hint': 'Ask for details about specific vehicles using their vehicle_id or inventory_id'
        }
    }