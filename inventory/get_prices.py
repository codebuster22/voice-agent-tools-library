"""
Get prices tool for automotive vehicles.

Provides pricing information with feature-based calculations.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


async def get_prices(
    query_type: str = "specific",          # "specific", "by_features"  
    vehicle_id: Optional[str] = None,      # For specific vehicle pricing
    inventory_id: Optional[str] = None,    # For specific inventory item pricing
    features: Optional[List[str]] = None   # Features to include in pricing
) -> Dict[str, Any]:
    """
    Get pricing information for vehicles with feature calculations.
    
    Args:
        query_type: Type of pricing query ("specific", "by_features")
        vehicle_id: UUID for vehicle base pricing
        inventory_id: UUID for specific inventory item pricing (preferred)
        features: List of features to include in pricing calculation
        
    Returns:
        Dict containing pricing details with breakdown
        
    Raises:
        ValueError: For invalid parameters or query_type
        Exception: For database connection or query errors
    """
    from db.connection import get_supabase_client
    
    # Input validation
    valid_query_types = ["specific", "by_features"]
    if query_type not in valid_query_types:
        raise ValueError(f"Invalid query_type '{query_type}'. Must be one of: {valid_query_types}")
    
    if query_type == "specific" and not vehicle_id and not inventory_id:
        raise ValueError("Either vehicle_id or inventory_id is required for specific pricing")
    
    try:
        client = get_supabase_client()
        
        if query_type == "specific":
            return await _get_specific_pricing(client, vehicle_id, inventory_id, features)
        elif query_type == "by_features":
            return await _get_feature_based_pricing(client, features)
            
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "invalid input syntax for type uuid" in error_msg:
            if vehicle_id:
                raise ValueError(f"Invalid vehicle_id format: {vehicle_id}")
            elif inventory_id:
                raise ValueError(f"Invalid inventory_id format: {inventory_id}")
        logger.error(f"Error getting prices: {error_msg}")
        raise Exception(f"Pricing query failed: {error_msg}")


async def _get_specific_pricing(client, vehicle_id: Optional[str], inventory_id: Optional[str], features: Optional[List[str]]) -> Dict[str, Any]:
    """Get pricing for a specific vehicle or inventory item."""
    
    if inventory_id:
        # Get pricing via inventory item (preferred - includes current price)
        response = client.table('inventory').select("""
            id,
            vehicle_id,
            vin,
            color,
            features,
            current_price,
            status,
            vehicles!inner(
                id,
                brand,
                model,
                year,
                category,
                base_price,
                is_active
            )
        """).eq('id', inventory_id).execute()
        
        if not response.data:
            raise ValueError(f"Inventory item '{inventory_id}' not found")
            
        inventory_data = response.data[0]
        vehicle_data = inventory_data['vehicles']
        
        # Get current pricing information
        pricing_response = client.table('pricing').select("""
            base_price,
            feature_prices,
            discount_amount,
            effective_date,
            is_current
        """).eq('vehicle_id', vehicle_data['id']).eq('is_current', True).execute()
        
    else:
        # Get pricing via vehicle_id only
        vehicle_response = client.table('vehicles').select("""
            id,
            brand,
            model,
            year,
            category,
            base_price,
            is_active
        """).eq('id', vehicle_id).execute()
        
        if not vehicle_response.data:
            raise ValueError(f"Vehicle '{vehicle_id}' not found")
            
        vehicle_data = vehicle_response.data[0]
        
        # Get a sample inventory item for this vehicle
        inventory_response = client.table('inventory').select("""
            id,
            current_price,
            features,
            status
        """).eq('vehicle_id', vehicle_id).eq('status', 'available').limit(1).execute()
        
        inventory_data = inventory_response.data[0] if inventory_response.data else None
        
        # Get current pricing information  
        pricing_response = client.table('pricing').select("""
            base_price,
            feature_prices,
            discount_amount,
            effective_date,
            is_current
        """).eq('vehicle_id', vehicle_id).eq('is_current', True).execute()
    
    # Check if vehicle is active
    if not vehicle_data['is_active']:
        raise ValueError("Vehicle is no longer available")
    
    # Get pricing data
    pricing_data = pricing_response.data[0] if pricing_response.data else None
    
    # Calculate final pricing
    price_breakdown = _calculate_price_breakdown(
        vehicle_data, 
        inventory_data if inventory_id else None,
        pricing_data, 
        features
    )
    
    # Format response
    result = {
        'vehicle': {
            'id': vehicle_data['id'],
            'brand': vehicle_data['brand'],
            'model': vehicle_data['model'],
            'year': vehicle_data['year'],
            'category': vehicle_data['category']
        },
        'pricing': price_breakdown
    }
    
    if inventory_id:
        result['inventory_id'] = inventory_id
        result['inventory_status'] = inventory_data['status']
        result['color'] = inventory_data['color']
    
    logger.info(f"Pricing calculated for vehicle {vehicle_data['brand']} {vehicle_data['model']}")
    return result


async def _get_feature_based_pricing(client, features: Optional[List[str]]) -> Dict[str, Any]:
    """Get feature-based pricing information."""
    
    if not features:
        raise ValueError("Features list is required for feature-based pricing")
    
    # Get feature pricing from all current pricing records
    response = client.table('pricing').select("""
        vehicle_id,
        feature_prices,
        vehicles!inner(
            brand,
            model,
            category
        )
    """).eq('is_current', True).execute()
    
    if not response.data:
        raise ValueError("No current pricing data available")
    
    # Aggregate feature pricing across all vehicles
    feature_costs = {}
    vehicle_examples = {}
    
    for pricing_record in response.data:
        feature_prices = pricing_record.get('feature_prices', {})
        vehicle_info = pricing_record['vehicles']
        
        for feature in features:
            if feature in feature_prices:
                cost = feature_prices[feature]
                if feature not in feature_costs:
                    feature_costs[feature] = []
                feature_costs[feature].append(cost)
                
                # Store example vehicle
                if feature not in vehicle_examples:
                    vehicle_examples[feature] = []
                vehicle_examples[feature].append(f"{vehicle_info['brand']} {vehicle_info['model']}")
    
    # Calculate average pricing for each feature
    feature_pricing = {}
    for feature, costs in feature_costs.items():
        avg_cost = sum(costs) // len(costs)  # Average in cents
        feature_pricing[feature] = {
            'average_cost_dollars': avg_cost // 100,
            'price_range_dollars': {
                'min': min(costs) // 100,
                'max': max(costs) // 100
            },
            'available_on_vehicles': len(set(vehicle_examples[feature])),
            'example_vehicles': list(set(vehicle_examples[feature][:3]))  # First 3 unique
        }
    
    # Calculate total if all features selected
    total_avg_cost = sum(pricing['average_cost_dollars'] for pricing in feature_pricing.values())
    
    result = {
        'requested_features': features,
        'feature_pricing': feature_pricing,
        'total_additional_cost_dollars': total_avg_cost,
        'notes': 'Prices may vary by vehicle model and availability'
    }
    
    logger.info(f"Feature-based pricing calculated for {len(features)} features")
    return result


def _calculate_price_breakdown(vehicle_data: Dict, inventory_data: Optional[Dict], pricing_data: Optional[Dict], additional_features: Optional[List[str]]) -> Dict[str, Any]:
    """Calculate detailed price breakdown."""
    
    # Base price (from pricing table if available, otherwise from vehicle)
    if pricing_data:
        base_price_cents = pricing_data['base_price']
        feature_prices = pricing_data.get('feature_prices', {})
        discount_amount = pricing_data.get('discount_amount', 0)
    else:
        base_price_cents = vehicle_data['base_price']
        feature_prices = {}
        discount_amount = 0
    
    # Current market price (from inventory if available)
    if inventory_data:
        current_price_cents = inventory_data['current_price']
        included_features = inventory_data.get('features', [])
    else:
        current_price_cents = base_price_cents
        included_features = []
    
    # Calculate feature costs
    included_feature_cost = 0
    for feature in included_features:
        if feature in feature_prices:
            included_feature_cost += feature_prices[feature]
    
    # Additional features cost
    additional_feature_cost = 0
    additional_feature_breakdown = {}
    if additional_features:
        for feature in additional_features:
            if feature not in included_features and feature in feature_prices:
                cost = feature_prices[feature]
                additional_feature_cost += cost
                additional_feature_breakdown[feature] = cost // 100  # Convert to dollars
    
    # Final calculations
    base_price_dollars = base_price_cents // 100
    current_price_dollars = current_price_cents // 100
    discount_dollars = discount_amount // 100
    included_features_value = included_feature_cost // 100
    additional_features_cost = additional_feature_cost // 100
    
    final_price_dollars = current_price_dollars + additional_features_cost
    
    return {
        'base_price_dollars': base_price_dollars,
        'current_price_dollars': current_price_dollars,
        'discount_applied_dollars': discount_dollars,
        'included_features': included_features,
        'included_features_value_dollars': included_features_value,
        'additional_features_requested': additional_features or [],
        'additional_features_cost_dollars': additional_features_cost,
        'additional_features_breakdown': additional_feature_breakdown,
        'final_price_dollars': final_price_dollars,
        'savings_from_discount': discount_dollars > 0,
        'price_currency': 'USD'
    }