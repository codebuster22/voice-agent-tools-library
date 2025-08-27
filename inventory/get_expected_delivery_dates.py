"""
Get expected delivery dates tool for automotive vehicles.

Provides delivery date estimation based on vehicle and feature selection.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def get_expected_delivery_dates(
    vehicle_id: str,                       # UUID from check_inventory
    features: Optional[List[str]] = None   # Additional features affecting delivery
) -> Dict[str, Any]:
    """
    Get expected delivery date ranges for all inventory records of a specific vehicle.
    
    Args:
        vehicle_id: UUID of the vehicle from inventory
        features: Additional features that may affect delivery time
        
    Returns:
        Dict containing delivery date ranges, individual inventory options, and summary
        
    Raises:
        ValueError: For invalid vehicle_id or parameters
        Exception: For database connection or query errors
    """
    from db.connection import get_supabase_client
    
    # Input validation
    if not vehicle_id or not vehicle_id.strip():
        raise ValueError("vehicle_id is required")
    
    try:
        client = get_supabase_client()
        
        # Get ALL inventory records for this vehicle
        response = client.table('inventory').select("""
            id,
            vehicle_id,
            vin,
            color,
            features,
            status,
            expected_delivery_date,
            location,
            vehicles!inner(
                brand,
                model,
                year,
                category,
                is_active
            )
        """).eq('vehicle_id', vehicle_id).execute()
        
        if not response.data:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found")
        
        all_inventory_records = response.data
        vehicle_info = all_inventory_records[0]['vehicles']
        
        # Check if vehicle is active
        if not vehicle_info['is_active']:
            raise ValueError("Vehicle is no longer available")
        
        # Calculate delivery estimates for all inventory records
        inventory_options = []
        all_delivery_dates = []
        
        for inventory_record in all_inventory_records:
            delivery_info = _calculate_delivery_estimate(inventory_record, features)
            
            # Skip sold/unavailable options for range calculation
            if delivery_info['status'] != 'unavailable':
                all_delivery_dates.append({
                    'date': delivery_info['estimated_delivery_date'],
                    'days': delivery_info['estimated_days']
                })
            
            inventory_options.append({
                'inventory_id': inventory_record['id'],
                'vin': inventory_record['vin'],
                'color': inventory_record['color'],
                'status': inventory_record['status'],
                'location': inventory_record['location'],
                'delivery_estimate': delivery_info
            })
        
        # Calculate delivery date range
        delivery_range = _calculate_delivery_range(all_delivery_dates, features)
        
        # Format response
        result = {
            'vehicle_id': vehicle_id,
            'vehicle': {
                'brand': vehicle_info['brand'],
                'model': vehicle_info['model'],
                'year': vehicle_info['year'],
                'category': vehicle_info['category']
            },
            'delivery_range': delivery_range,
            'inventory_options': inventory_options,
            'total_inventory_records': len(all_inventory_records)
        }
        
        logger.info(f"Delivery range generated for vehicle {vehicle_id}: {delivery_range['range_text']}")
        return result
        
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "invalid input syntax for type uuid" in error_msg:
            raise ValueError(f"Invalid vehicle_id format: {vehicle_id}")
        logger.error(f"Error getting delivery dates: {error_msg}")
        raise Exception(f"Delivery date query failed: {error_msg}")


def _calculate_delivery_range(all_delivery_dates: List[Dict[str, Any]], additional_features: Optional[List[str]]) -> Dict[str, Any]:
    """Calculate overall delivery date range from all available inventory options."""
    
    if not all_delivery_dates:
        return {
            'status': 'unavailable',
            'range_text': 'No vehicles available',
            'earliest_date': None,
            'latest_date': None,
            'min_days': None,
            'max_days': None
        }
    
    # Find earliest and latest delivery dates
    min_days = min(option['days'] for option in all_delivery_dates)
    max_days = max(option['days'] for option in all_delivery_dates)
    
    earliest_date = min(option['date'] for option in all_delivery_dates)
    latest_date = max(option['date'] for option in all_delivery_dates)
    
    # Generate human-readable range text
    if min_days == max_days:
        if min_days <= 1:
            range_text = "Available immediately"
        elif min_days <= 7:
            range_text = f"Available in {min_days} day{'s' if min_days > 1 else ''}"
        else:
            weeks = min_days // 7
            range_text = f"Available in {weeks} week{'s' if weeks > 1 else ''}"
    else:
        if max_days <= 7:
            range_text = f"{min_days}-{max_days} days"
        elif min_days <= 7 and max_days > 7:
            max_weeks = max_days // 7
            range_text = f"{min_days} days to {max_weeks} week{'s' if max_weeks > 1 else ''}"
        else:
            min_weeks = min_days // 7
            max_weeks = max_days // 7
            range_text = f"{min_weeks}-{max_weeks} week{'s' if max_weeks > 1 else ''}"
    
    return {
        'status': 'available',
        'range_text': range_text,
        'earliest_date': earliest_date,
        'latest_date': latest_date,
        'min_days': min_days,
        'max_days': max_days,
        'total_options': len(all_delivery_dates)
    }


def _calculate_delivery_estimate(vehicle_data: Dict[str, Any], additional_features: Optional[List[str]]) -> Dict[str, Any]:
    """Calculate delivery estimate for a single inventory record."""
    
    status = vehicle_data['status']
    existing_delivery_date = vehicle_data['expected_delivery_date']
    current_features = vehicle_data.get('features', [])
    location = vehicle_data['location']
    
    # Base delivery estimation
    today = datetime.now().date()
    
    if status == 'available':
        if location == 'main_dealership':
            # Vehicle ready for immediate pickup
            delivery_date = today + timedelta(days=1)
            estimated_days = 1
            reasoning = "Vehicle is available at main dealership for immediate pickup"
            delivery_type = "immediate_pickup"
        else:
            # Vehicle needs to be transferred
            delivery_date = today + timedelta(days=3)
            estimated_days = 3
            reasoning = f"Vehicle needs to be transferred from {location} to main dealership"
            delivery_type = "transfer_required"
    
    elif status == 'reserved':
        # Check if there's a specific delivery date
        if existing_delivery_date:
            delivery_date = datetime.strptime(existing_delivery_date, '%Y-%m-%d').date()
            estimated_days = (delivery_date - today).days
            reasoning = "Vehicle is reserved with scheduled delivery date"
            delivery_type = "reserved_scheduled"
        else:
            # Reserved but no specific date - estimate based on typical processing
            delivery_date = today + timedelta(days=7)
            estimated_days = 7
            reasoning = "Vehicle is reserved, estimated delivery based on typical processing time"
            delivery_type = "reserved_estimated"
    
    elif status == 'sold':
        return {
            'status': 'unavailable',
            'reason': 'Vehicle has been sold',
            'estimated_delivery_date': None,
            'estimated_days': None,
            'delivery_type': 'unavailable'
        }
    
    else:
        # Custom order or other status
        if existing_delivery_date:
            delivery_date = datetime.strptime(existing_delivery_date, '%Y-%m-%d').date()
            estimated_days = (delivery_date - today).days
            reasoning = f"Vehicle status: {status}, delivery as scheduled"
            delivery_type = "custom_order"
        else:
            # Default estimate for unknown status
            delivery_date = today + timedelta(days=14)
            estimated_days = 14
            reasoning = f"Vehicle status: {status}, estimated delivery time"
            delivery_type = "estimated"
    
    # Adjust for additional features
    feature_delay = 0
    if additional_features:
        # Check if additional features need to be installed
        missing_features = [f for f in additional_features if f not in current_features]
        if missing_features:
            feature_delay = len(missing_features) * 2  # 2 days per additional feature
            delivery_date += timedelta(days=feature_delay)
            estimated_days += feature_delay
            reasoning += f". Additional {feature_delay} days for installing features: {', '.join(missing_features)}"
    
    # Ensure delivery date is not in the past
    if delivery_date <= today:
        delivery_date = today + timedelta(days=1)
        estimated_days = 1
    
    return {
        'status': 'available' if status != 'sold' else 'unavailable',
        'estimated_delivery_date': delivery_date.strftime('%Y-%m-%d') if status != 'sold' else None,
        'estimated_days': max(1, estimated_days) if status != 'sold' else None,
        'delivery_type': delivery_type,
        'reasoning': reasoning,
        'current_features': current_features,
        'additional_features_requested': additional_features or [],
        'feature_installation_delay_days': feature_delay
    }