"""
Comprehensive tests for inventory tools using real Supabase database.

Following TDD methodology with real database integration (no mocks).
"""

import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from uuid import uuid4

# Import our modules
from db import get_supabase_client
from inventory.check_inventory import check_inventory


class TestCheckInventory:
    """Comprehensive tests for check_inventory function using real Supabase database."""
    
    @pytest_asyncio.fixture(scope="class")
    async def database_setup(self):
        """Setup test data using existing Supabase database."""
        # Create test data
        await self._create_test_data()
        
        yield
        
        # Cleanup test data
        await self._cleanup_test_data()
    
    async def _create_test_data(self):
        """Create comprehensive test data for inventory testing."""
        client = get_supabase_client()
        
        # Test vehicles data with proper UUIDs
        vehicles_data = [
            {
                'id': 'aaaaaaaa-bbbb-cccc-dddd-111111111111',
                'brand': 'Tesla',
                'model': 'Model 3',
                'year': 2024,
                'category': 'sedan',
                'base_price': 3999000,  # $39,990 in cents
                'is_active': True
            },
            {
                'id': 'aaaaaaaa-bbbb-cccc-dddd-222222222222', 
                'brand': 'Tesla',
                'model': 'Model Y',
                'year': 2024,
                'category': 'suv',
                'base_price': 4799000,  # $47,990 in cents
                'is_active': True
            },
            {
                'id': 'aaaaaaaa-bbbb-cccc-dddd-333333333333',
                'brand': 'Ford',
                'model': 'F-150',
                'year': 2024,
                'category': 'truck',
                'base_price': 3495000,  # $34,950 in cents
                'is_active': True
            },
            {
                'id': 'aaaaaaaa-bbbb-cccc-dddd-444444444444',
                'brand': 'BMW',
                'model': '330i',
                'year': 2024,
                'category': 'sedan',
                'base_price': 4595000,  # $45,950 in cents
                'is_active': False  # Inactive vehicle
            }
        ]
        
        # Insert vehicles
        for vehicle in vehicles_data:
            try:
                client.table('vehicles').upsert(vehicle).execute()
            except Exception as e:
                print(f"Warning: Could not insert vehicle {vehicle['id']}: {e}")
        
        # Test inventory data with proper UUIDs
        inventory_data = [
            {
                'id': 'bbbbbbbb-cccc-dddd-eeee-111111111111',
                'vehicle_id': 'aaaaaaaa-bbbb-cccc-dddd-111111111111',
                'vin': 'TEST1VIN123456789',
                'color': 'Pearl White',
                'features': ['autopilot', 'premium_interior'],
                'status': 'available',
                'current_price': 4299000,  # $42,990 in cents
                'expected_delivery_date': str(date.today() + timedelta(days=30))
            },
            {
                'id': 'bbbbbbbb-cccc-dddd-eeee-222222222222',
                'vehicle_id': 'aaaaaaaa-bbbb-cccc-dddd-111111111111',
                'vin': 'TEST2VIN123456789',
                'color': 'Midnight Silver',
                'features': ['autopilot', 'fsd'],
                'status': 'available',
                'current_price': 4799000,  # $47,990 in cents
                'expected_delivery_date': str(date.today() + timedelta(days=45))
            },
            {
                'id': 'bbbbbbbb-cccc-dddd-eeee-333333333333',
                'vehicle_id': 'aaaaaaaa-bbbb-cccc-dddd-222222222222',
                'vin': 'TEST3VIN123456789',
                'color': 'Deep Blue',
                'features': ['autopilot', 'tow_hitch'],
                'status': 'available',
                'current_price': 5199000,  # $51,990 in cents
                'expected_delivery_date': str(date.today() + timedelta(days=60))
            },
            {
                'id': 'bbbbbbbb-cccc-dddd-eeee-444444444444',
                'vehicle_id': 'aaaaaaaa-bbbb-cccc-dddd-333333333333',
                'vin': 'TEST4VIN123456789',
                'color': 'Lightning Blue',
                'features': ['4x4', 'tow_package'],
                'status': 'sold',  # Not available
                'current_price': 3895000,  # $38,950 in cents
                'expected_delivery_date': str(date.today() + timedelta(days=90))
            },
            {
                'id': 'bbbbbbbb-cccc-dddd-eeee-555555555555',
                'vehicle_id': 'aaaaaaaa-bbbb-cccc-dddd-333333333333',
                'vin': 'TEST5VIN123456789',
                'color': 'Agate Black',
                'features': ['4x4', 'tow_package', 'pro_trailer_backup'],
                'status': 'available',
                'current_price': 4195000,  # $41,950 in cents
                'expected_delivery_date': str(date.today() + timedelta(days=75))
            }
        ]
        
        # Insert inventory
        for inventory in inventory_data:
            try:
                client.table('inventory').upsert(inventory).execute()
            except Exception as e:
                print(f"Warning: Could not insert inventory {inventory['id']}: {e}")
    
    async def _cleanup_test_data(self):
        """Clean up test data from database."""
        client = get_supabase_client()
        
        try:
            # Delete test inventory first (due to foreign key constraints)
            inventory_ids = [
                'bbbbbbbb-cccc-dddd-eeee-111111111111',
                'bbbbbbbb-cccc-dddd-eeee-222222222222', 
                'bbbbbbbb-cccc-dddd-eeee-333333333333',
                'bbbbbbbb-cccc-dddd-eeee-444444444444',
                'bbbbbbbb-cccc-dddd-eeee-555555555555'
            ]
            client.table('inventory').delete().in_('id', inventory_ids).execute()
            
            # Delete test vehicles
            vehicle_ids = [
                'aaaaaaaa-bbbb-cccc-dddd-111111111111',
                'aaaaaaaa-bbbb-cccc-dddd-222222222222',
                'aaaaaaaa-bbbb-cccc-dddd-333333333333', 
                'aaaaaaaa-bbbb-cccc-dddd-444444444444'
            ]
            client.table('vehicles').delete().in_('id', vehicle_ids).execute()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")
    
    @pytest.mark.asyncio
    async def test_check_inventory_all_available(self, database_setup):
        """Test retrieving all available inventory."""
        result = await check_inventory()
        
        assert isinstance(result, dict)
        assert 'vehicles' in result
        assert 'total_count' in result
        assert 'filters_applied' in result
        
        # Should have available vehicles (excluding sold ones)
        assert result['total_count'] >= 3
        assert len(result['vehicles']) >= 3
        
        # Verify structure of returned vehicles
        for vehicle in result['vehicles']:
            assert 'inventory_id' in vehicle
            assert 'vehicle_id' in vehicle
            assert 'brand' in vehicle
            assert 'model' in vehicle
            assert 'category' in vehicle
            assert 'color' in vehicle
            assert 'features' in vehicle
            assert 'price' in vehicle
            assert 'status' in vehicle
            assert 'delivery_date' in vehicle
            assert vehicle['status'] == 'available'  # Default filter
    
    @pytest.mark.asyncio
    async def test_check_inventory_filter_by_category(self, database_setup):
        """Test filtering inventory by vehicle category."""
        result = await check_inventory(category='sedan')
        
        assert result['total_count'] >= 1
        assert all(vehicle['category'] == 'sedan' for vehicle in result['vehicles'])
        assert result['filters_applied']['category'] == 'sedan'
        
        # Test SUV category
        result_suv = await check_inventory(category='suv')
        assert result_suv['total_count'] >= 1
        assert all(vehicle['category'] == 'suv' for vehicle in result_suv['vehicles'])
    
    @pytest.mark.asyncio
    async def test_check_inventory_filter_by_model_name(self, database_setup):
        """Test filtering inventory by model name (text search)."""
        result = await check_inventory(model_name='Model 3')
        
        assert result['total_count'] >= 1
        assert all('Model 3' in vehicle['model'] for vehicle in result['vehicles'])
        assert result['filters_applied']['model_name'] == 'Model 3'
        
        # Test another model search
        result_f150 = await check_inventory(model_name='F-150')
        assert result_f150['total_count'] >= 1
        assert all('F-150' in vehicle['model'] for vehicle in result_f150['vehicles'])
    
    @pytest.mark.asyncio
    async def test_check_inventory_filter_by_price_range(self, database_setup):
        """Test filtering inventory by price range."""
        # Filter for vehicles under $45,000
        result = await check_inventory(max_price=45000)
        
        assert result['total_count'] >= 1
        assert all(vehicle['price'] <= 45000 for vehicle in result['vehicles'])
        assert result['filters_applied']['max_price'] == 45000
        
        # Filter for vehicles between $40,000 and $50,000
        result_range = await check_inventory(min_price=40000, max_price=50000)
        assert all(40000 <= vehicle['price'] <= 50000 for vehicle in result_range['vehicles'])
    
    @pytest.mark.asyncio
    async def test_check_inventory_filter_by_features(self, database_setup):
        """Test filtering inventory by required features."""
        result = await check_inventory(features=['autopilot'])
        
        assert result['total_count'] >= 2
        assert all('autopilot' in vehicle['features'] for vehicle in result['vehicles'])
        assert result['filters_applied']['features'] == ['autopilot']
        
        # Test multiple features (must have ALL)
        result_multi = await check_inventory(features=['4x4', 'tow_package'])
        # Should find the F-150 with both features
        assert any(vehicle['category'] == 'truck' for vehicle in result_multi['vehicles'])
    
    @pytest.mark.asyncio
    async def test_check_inventory_filter_by_status(self, database_setup):
        """Test filtering inventory by status."""
        # Test sold vehicles
        result_sold = await check_inventory(status='sold')
        assert all(vehicle['status'] == 'sold' for vehicle in result_sold['vehicles'])
        
        # Test all statuses
        result_all = await check_inventory(status='all')
        assert result_all['total_count'] >= 4  # Should include sold vehicles
    
    @pytest.mark.asyncio
    async def test_check_inventory_combined_filters(self, database_setup):
        """Test combining multiple filters."""
        result = await check_inventory(
            category='sedan',
            max_price=50000,
            features=['autopilot']
        )
        
        # Should find Tesla sedans with autopilot under $50k
        for vehicle in result['vehicles']:
            assert vehicle['category'] == 'sedan'
            assert vehicle['price'] <= 50000
            assert 'autopilot' in vehicle['features']
        
        # Verify filters were applied
        filters = result['filters_applied']
        assert filters['category'] == 'sedan'
        assert filters['max_price'] == 50000
        assert filters['features'] == ['autopilot']
    
    @pytest.mark.asyncio
    async def test_check_inventory_no_results(self, database_setup):
        """Test query with no matching results."""
        result = await check_inventory(
            category='coupe',  # No coupes in test data
            min_price=100000   # Very high price
        )
        
        assert result['total_count'] == 0
        assert result['vehicles'] == []
        assert 'filters_applied' in result
    
    @pytest.mark.asyncio
    async def test_check_inventory_invalid_category(self, database_setup):
        """Test error handling for invalid category."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(category='invalid_category')
        
        assert 'invalid category' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_inventory_invalid_price_range(self, database_setup):
        """Test error handling for invalid price range."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=50000, max_price=30000)
        
        assert 'min_price cannot be greater than max_price' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_inventory_invalid_status(self, database_setup):
        """Test error handling for invalid status."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(status='invalid_status')
        
        assert 'invalid status' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_inventory_negative_price(self, database_setup):
        """Test error handling for negative prices."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=-1000)
        
        assert 'price cannot be negative' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_inventory_empty_features(self, database_setup):
        """Test handling of empty features list."""
        result = await check_inventory(features=[])
        
        # Empty features should return all vehicles (no feature filtering)
        assert result['total_count'] >= 3
        assert 'features' not in result['filters_applied']
    
    @pytest.mark.asyncio
    async def test_check_inventory_response_structure(self, database_setup):
        """Test complete response structure validation."""
        result = await check_inventory(category='sedan')
        
        # Validate top-level structure
        required_keys = ['vehicles', 'total_count', 'filters_applied']
        assert all(key in result for key in required_keys)
        
        # Validate vehicle structure
        if result['vehicles']:
            vehicle = result['vehicles'][0]
            vehicle_keys = [
                'inventory_id', 'vehicle_id', 'brand', 'model', 'category',
                'color', 'features', 'price', 'status', 'delivery_date'
            ]
            assert all(key in vehicle for key in vehicle_keys)
            
            # Validate data types
            assert isinstance(vehicle['inventory_id'], str)
            assert isinstance(vehicle['vehicle_id'], str)
            assert isinstance(vehicle['brand'], str)
            assert isinstance(vehicle['model'], str)
            assert isinstance(vehicle['price'], (int, float))
            assert isinstance(vehicle['features'], list)
    
    @pytest.mark.asyncio
    async def test_check_inventory_database_connection_error(self):
        """Test handling of database connection errors."""
        # This test would typically use dependency injection or mocking
        # For now, we'll test with a malformed query that should fail gracefully
        
        # Test will be implemented when we add connection error simulation
        pass