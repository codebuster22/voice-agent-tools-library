"""
Get similar vehicles tool for automotive inventory.

Finds alternative vehicles when the preferred option is unavailable.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


async def get_similar_vehicles(
    reference_vehicle_id: str,                    # Vehicle to find alternatives for
    max_results: int = 5,                        # Maximum number of alternatives
    price_tolerance_percent: int = 20,           # Price range tolerance
    include_unavailable: bool = False            # Include sold/reserved vehicles
) -> Dict[str, Any]:
    """
    Find similar vehicles based on category, price range, and features.
    
    Args:
        reference_vehicle_id: UUID of the reference vehicle
        max_results: Maximum number of similar vehicles to return
        price_tolerance_percent: Price tolerance as percentage (e.g., 20 = ±20%)
        include_unavailable: Whether to include sold/reserved vehicles
        
    Returns:
        Dict containing similar vehicles ranked by similarity
        
    Raises:
        ValueError: For invalid parameters
        Exception: For database connection or query errors
    """
    from db.connection import get_supabase_client
    
    # Input validation
    if not reference_vehicle_id or not reference_vehicle_id.strip():
        raise ValueError("reference_vehicle_id is required")
    
    if max_results < 1 or max_results > 20:
        raise ValueError("max_results must be between 1 and 20")
    
    if price_tolerance_percent < 0 or price_tolerance_percent > 100:
        raise ValueError("price_tolerance_percent must be between 0 and 100")
    
    try:
        client = get_supabase_client()
        
        # Get reference vehicle information
        reference_vehicle = await _get_reference_vehicle(client, reference_vehicle_id)
        
        # Find similar vehicles
        similar_vehicles = await _find_similar_vehicles(
            client, 
            reference_vehicle, 
            max_results, 
            price_tolerance_percent, 
            include_unavailable
        )
        
        # Rank and format results
        result = _format_similarity_response(reference_vehicle, similar_vehicles, max_results)
        
        logger.info(f"Found {len(similar_vehicles)} similar vehicles for {reference_vehicle['brand']} {reference_vehicle['model']}")
        return result
        
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "invalid input syntax for type uuid" in error_msg:
            raise ValueError(f"Invalid reference_vehicle_id format: {reference_vehicle_id}")
        logger.error(f"Error finding similar vehicles: {error_msg}")
        raise Exception(f"Similar vehicles search failed: {error_msg}")


async def _get_reference_vehicle(client, vehicle_id: str) -> Dict[str, Any]:
    """Get detailed information about the reference vehicle."""
    
    response = client.table('vehicles').select("""
        id,
        brand,
        model,
        year,
        category,
        base_price,
        is_active
    """).eq('id', vehicle_id).execute()
    
    if not response.data:
        raise ValueError(f"Reference vehicle '{vehicle_id}' not found")
    
    vehicle_data = response.data[0]
    
    if not vehicle_data['is_active']:
        raise ValueError("Reference vehicle is no longer active")
    
    # Get sample inventory and pricing info
    inventory_response = client.table('inventory').select("""
        current_price,
        features,
        status
    """).eq('vehicle_id', vehicle_id).limit(1).execute()
    
    pricing_response = client.table('pricing').select("""
        base_price,
        feature_prices
    """).eq('vehicle_id', vehicle_id).eq('is_current', True).execute()
    
    # Add additional context
    vehicle_data['sample_current_price'] = None
    vehicle_data['sample_features'] = []
    vehicle_data['feature_prices'] = {}
    
    if inventory_response.data:
        inventory_item = inventory_response.data[0]
        vehicle_data['sample_current_price'] = inventory_item['current_price']
        vehicle_data['sample_features'] = inventory_item.get('features', [])
    
    if pricing_response.data:
        pricing_item = pricing_response.data[0]
        vehicle_data['feature_prices'] = pricing_item.get('feature_prices', {})
    
    return vehicle_data


async def _find_similar_vehicles(client, reference_vehicle: Dict, max_results: int, price_tolerance: int, include_unavailable: bool) -> List[Dict[str, Any]]:
    """Find vehicles similar to the reference vehicle."""
    
    reference_price = reference_vehicle['sample_current_price'] or reference_vehicle['base_price']
    price_min = reference_price * (100 - price_tolerance) // 100
    price_max = reference_price * (100 + price_tolerance) // 100
    
    # Build query to find similar vehicles
    query = client.table('inventory').select("""
        id,
        vehicle_id,
        vin,
        color,
        features,
        current_price,
        status,
        expected_delivery_date,
        location,
        vehicles!inner(
            id,
            brand,
            model,
            year,
            category,
            base_price,
            is_active
        )
    """)
    
    # Filter by active vehicles
    query = query.eq('vehicles.is_active', True)
    
    # Exclude the reference vehicle
    query = query.neq('vehicle_id', reference_vehicle['id'])
    
    # Filter by category (same category)
    query = query.eq('vehicles.category', reference_vehicle['category'])
    
    # Filter by price range
    query = query.gte('current_price', price_min)
    query = query.lte('current_price', price_max)
    
    # Filter by availability status
    if not include_unavailable:
        query = query.eq('status', 'available')
    
    # Execute query
    response = query.execute()
    
    if not response.data:
        # If no exact category matches, try broader search (remove category filter)
        query = client.table('inventory').select("""
            id,
            vehicle_id,
            vin,
            color,
            features,
            current_price,
            status,
            expected_delivery_date,
            location,
            vehicles!inner(
                id,
                brand,
                model,
                year,
                category,
                base_price,
                is_active
            )
        """)
        query = query.eq('vehicles.is_active', True)
        query = query.neq('vehicle_id', reference_vehicle['id'])
        query = query.gte('current_price', price_min)
        query = query.lte('current_price', price_max)
        
        if not include_unavailable:
            query = query.eq('status', 'available')
        
        response = query.execute()
    
    # Calculate similarity scores and rank results
    vehicles_with_scores = []
    for item in response.data:
        vehicle_info = item['vehicles']
        similarity_score = _calculate_similarity_score(reference_vehicle, vehicle_info, item)
        
        vehicles_with_scores.append({
            'inventory_data': item,
            'vehicle_data': vehicle_info,
            'similarity_score': similarity_score
        })
    
    # Sort by similarity score (descending) and limit results
    vehicles_with_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
    return vehicles_with_scores[:max_results]


def _calculate_similarity_score(reference_vehicle: Dict, vehicle_info: Dict, inventory_item: Dict) -> float:
    """Calculate similarity score between reference and candidate vehicle."""
    
    score = 0.0
    max_score = 0.0
    
    # Category match (40% weight)
    category_weight = 40
    max_score += category_weight
    if vehicle_info['category'] == reference_vehicle['category']:
        score += category_weight
    
    # Brand match (25% weight)
    brand_weight = 25
    max_score += brand_weight
    if vehicle_info['brand'].lower() == reference_vehicle['brand'].lower():
        score += brand_weight
    
    # Year proximity (15% weight)
    year_weight = 15
    max_score += year_weight
    year_diff = abs(vehicle_info['year'] - reference_vehicle['year'])
    if year_diff == 0:
        score += year_weight
    elif year_diff == 1:
        score += year_weight * 0.7
    elif year_diff == 2:
        score += year_weight * 0.4
    elif year_diff <= 3:
        score += year_weight * 0.2
    
    # Feature similarity (20% weight)
    feature_weight = 20
    max_score += feature_weight
    reference_features = set(reference_vehicle.get('sample_features', []))
    candidate_features = set(inventory_item.get('features', []))
    
    if reference_features or candidate_features:
        if reference_features:
            # Calculate overlap percentage
            overlap = len(reference_features.intersection(candidate_features))
            overlap_ratio = overlap / len(reference_features)
            score += feature_weight * overlap_ratio
        else:
            # If reference has no features, give some score for any features
            score += feature_weight * 0.5
    else:
        # Both have no features - perfect match for this aspect
        score += feature_weight
    
    # Normalize score to percentage
    return (score / max_score) * 100 if max_score > 0 else 0


def _format_similarity_response(reference_vehicle: Dict, similar_vehicles: List[Dict], max_results: int) -> Dict[str, Any]:
    """Format the similarity search response."""
    
    alternatives = []
    for vehicle_data in similar_vehicles:
        inventory_item = vehicle_data['inventory_data']
        vehicle_info = vehicle_data['vehicle_data']
        similarity_score = vehicle_data['similarity_score']
        
        alternatives.append({
            'inventory_id': inventory_item['id'],
            'vehicle_id': vehicle_info['id'],
            'brand': vehicle_info['brand'],
            'model': vehicle_info['model'],
            'year': vehicle_info['year'],
            'category': vehicle_info['category'],
            'color': inventory_item['color'],
            'features': inventory_item['features'],
            'price_dollars': inventory_item['current_price'] // 100,
            'status': inventory_item['status'],
            'location': inventory_item['location'],
            'delivery_date': inventory_item['expected_delivery_date'],
            'similarity_score': round(similarity_score, 1),
            'similarity_reasons': _get_similarity_reasons(reference_vehicle, vehicle_info, inventory_item, similarity_score)
        })
    
    return {
        'reference_vehicle': {
            'id': reference_vehicle['id'],
            'brand': reference_vehicle['brand'],
            'model': reference_vehicle['model'],
            'year': reference_vehicle['year'],
            'category': reference_vehicle['category']
        },
        'alternatives': alternatives,
        'total_found': len(alternatives),
        'max_requested': max_results,
        'search_criteria': {
            'same_category': reference_vehicle['category'],
            'price_range_tolerance': 'within configured range',
            'availability_filter': 'available vehicles only' if len([v for v in alternatives if v['status'] == 'available']) == len(alternatives) else 'includes all statuses'
        }
    }


def _get_similarity_reasons(reference_vehicle: Dict, vehicle_info: Dict, inventory_item: Dict, similarity_score: float) -> List[str]:
    """Generate human-readable reasons for similarity."""
    
    reasons = []
    
    # Category match
    if vehicle_info['category'] == reference_vehicle['category']:
        reasons.append(f"Same category ({vehicle_info['category']})")
    
    # Brand match
    if vehicle_info['brand'].lower() == reference_vehicle['brand'].lower():
        reasons.append(f"Same brand ({vehicle_info['brand']})")
    
    # Year proximity
    year_diff = abs(vehicle_info['year'] - reference_vehicle['year'])
    if year_diff == 0:
        reasons.append(f"Same year ({vehicle_info['year']})")
    elif year_diff <= 2:
        reasons.append(f"Similar year ({vehicle_info['year']} vs {reference_vehicle['year']})")
    
    # Feature overlap
    reference_features = set(reference_vehicle.get('sample_features', []))
    candidate_features = set(inventory_item.get('features', []))
    
    if reference_features and candidate_features:
        overlap = reference_features.intersection(candidate_features)
        if overlap:
            reasons.append(f"Shared features: {', '.join(list(overlap)[:3])}")  # Show first 3
    
    # Price comparison
    ref_price = reference_vehicle.get('sample_current_price', reference_vehicle['base_price'])
    candidate_price = inventory_item['current_price']
    price_diff_percent = abs(candidate_price - ref_price) / ref_price * 100
    
    if price_diff_percent < 10:
        reasons.append("Similar price range")
    
    # Overall similarity
    if similarity_score >= 80:
        reasons.append("Excellent match")
    elif similarity_score >= 60:
        reasons.append("Good alternative")
    elif similarity_score >= 40:
        reasons.append("Reasonable option")
    
    return reasons[:4]  # Limit to 4 most relevant reasons