"""
Tests for get_expected_delivery_dates tool.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from inventory.get_expected_delivery_dates import get_expected_delivery_dates


class TestGetExpectedDeliveryDates:
    """Test suite for get_expected_delivery_dates function using real Supabase database."""

    @pytest.mark.asyncio
    async def test_get_delivery_dates_available_main_dealership(self):
        """Test delivery date ranges for vehicle with multiple inventory records."""
        # Use Toyota Camry vehicle ID from seed data (has multiple inventory records)
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert "vehicle_id" in result
        assert "vehicle" in result
        assert "delivery_range" in result
        assert "inventory_options" in result
        assert "total_inventory_records" in result
        
        assert result["vehicle_id"] == vehicle_id
        assert result["vehicle"]["brand"] == "Toyota"
        assert result["vehicle"]["model"] == "Camry"
        
        # Should have delivery range information
        delivery_range = result["delivery_range"]
        assert "range_text" in delivery_range
        assert "earliest_date" in delivery_range
        assert "latest_date" in delivery_range
        assert "min_days" in delivery_range
        assert "max_days" in delivery_range
        assert "status" in delivery_range
        
        # Should have multiple inventory options
        assert result["total_inventory_records"] >= 2
        assert len(result["inventory_options"]) >= 2
        
        # Each inventory option should have proper structure
        for option in result["inventory_options"]:
            assert "inventory_id" in option
            assert "color" in option
            assert "status" in option
            assert "location" in option
            assert "delivery_estimate" in option

    @pytest.mark.asyncio
    async def test_get_delivery_dates_with_additional_features(self):
        """Test delivery dates with additional features requested."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Premium Audio", "Heated Seats"]
        
        result = await get_expected_delivery_dates(vehicle_id, features=additional_features)
        
        assert isinstance(result, dict)
        assert "inventory_options" in result
        
        # Check that available inventory options account for additional features
        available_options = [opt for opt in result["inventory_options"] if opt["status"] == "available"]
        assert len(available_options) > 0
        
        for option in available_options:
            delivery_info = option["delivery_estimate"]
            assert "additional_features_requested" in delivery_info
            assert "feature_installation_delay_days" in delivery_info
            assert delivery_info["additional_features_requested"] == additional_features
            
            # Should have some delay for additional features not already included
            current_features = delivery_info.get("current_features", [])
            missing_features = [f for f in additional_features if f not in current_features]
            if missing_features:
                assert delivery_info["feature_installation_delay_days"] > 0
                assert "Additional" in delivery_info["reasoning"]

    @pytest.mark.asyncio
    async def test_get_delivery_dates_reserved_vehicle(self):
        """Test delivery dates for reserved vehicle."""
        # Find a reserved vehicle from seed data
        from db.connection import get_supabase_client
        client = get_supabase_client()
        
        response = client.table('inventory').select('vehicle_id').eq('status', 'reserved').limit(1).execute()
        if not response.data:
            pytest.skip("No reserved vehicles in test data")
        
        vehicle_id = response.data[0]['vehicle_id']
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert result["current_status"] == "reserved"
        
        delivery_info = result["delivery_estimation"]
        assert "reserved" in delivery_info["delivery_type"]

    @pytest.mark.asyncio
    async def test_get_delivery_dates_sold_vehicle(self):
        """Test delivery dates for vehicle with sold inventory records."""
        # Use Toyota Camry which has a sold inventory record
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert "inventory_options" in result
        
        # Should find sold inventory records
        statuses = [opt["status"] for opt in result["inventory_options"]]
        assert "sold" in statuses
        
        # Find sold option and verify it's marked as unavailable
        sold_option = next(opt for opt in result["inventory_options"] if opt["status"] == "sold")
        delivery_info = sold_option["delivery_estimate"]
        assert delivery_info["status"] == "unavailable"
        assert "sold" in delivery_info["reason"].lower()

    @pytest.mark.asyncio
    async def test_get_delivery_dates_transfer_required(self):
        """Test delivery dates for vehicle requiring transfer."""
        # Use Toyota RAV4 which has inventory at service_center
        vehicle_id = "550e8400-e29b-41d4-a716-446655440004"  # Toyota RAV4
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert "inventory_options" in result
        
        # Find option requiring transfer
        transfer_options = [opt for opt in result["inventory_options"] 
                          if opt["location"] != "main_dealership" and opt["status"] == "available"]
        
        if transfer_options:
            delivery_info = transfer_options[0]["delivery_estimate"]
            assert "transfer" in delivery_info["delivery_type"] or "transfer" in delivery_info["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_get_delivery_dates_invalid_vehicle_id(self):
        """Test delivery dates with invalid vehicle ID."""
        invalid_vehicle_id = "invalid-uuid-format"
        
        with pytest.raises(ValueError) as exc_info:
            await get_expected_delivery_dates(invalid_vehicle_id)
        
        assert "not found" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_delivery_dates_empty_vehicle_id(self):
        """Test delivery dates with empty vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_expected_delivery_dates("")
        
        assert "required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_none_vehicle_id(self):
        """Test delivery dates with None vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_expected_delivery_dates(None)
        
        assert "required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_response_structure(self):
        """Test that delivery dates response has correct structure."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Verify top-level structure
        required_keys = ["vehicle_id", "vehicle", "current_status", "location", "delivery_estimation"]
        for key in required_keys:
            assert key in result
        
        # Verify vehicle structure
        vehicle = result["vehicle"]
        vehicle_keys = ["brand", "model", "year", "category", "color"]
        for key in vehicle_keys:
            assert key in vehicle
        
        # Verify delivery estimation structure
        delivery_info = result["delivery_estimation"]
        delivery_keys = ["status", "estimated_delivery_date", "estimated_days", "delivery_type", "reasoning"]
        for key in delivery_keys:
            assert key in delivery_info

    @pytest.mark.asyncio
    async def test_get_delivery_dates_date_format(self):
        """Test that delivery dates are returned in correct format."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_info = result["delivery_estimation"]
        if delivery_info["status"] != "unavailable":
            delivery_date = delivery_info["estimated_delivery_date"]
            
            # Should be in YYYY-MM-DD format
            assert isinstance(delivery_date, str)
            datetime.strptime(delivery_date, '%Y-%m-%d')  # Should not raise exception
            
            # Should be a future date or today
            delivery_datetime = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            today = datetime.now().date()
            assert delivery_datetime >= today

    @pytest.mark.asyncio
    async def test_get_delivery_dates_estimated_days_positive(self):
        """Test that estimated days is always positive for available vehicles."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_info = result["delivery_estimation"]
        if delivery_info["status"] != "unavailable":
            assert delivery_info["estimated_days"] >= 1

    @pytest.mark.asyncio
    async def test_get_delivery_dates_feature_delay_calculation(self):
        """Test feature installation delay calculation."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # Test with features that might not be included
        additional_features = ["Premium Sound System", "Ceramic Coating", "Extended Warranty"]
        result = await get_expected_delivery_dates(vehicle_id, features=additional_features)
        
        delivery_info = result["delivery_estimation"]
        assert "feature_installation_delay_days" in delivery_info
        assert isinstance(delivery_info["feature_installation_delay_days"], int)
        assert delivery_info["feature_installation_delay_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_delivery_dates_current_features_included(self):
        """Test that current vehicle features are included in response."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_info = result["delivery_estimation"]
        assert "current_features" in delivery_info
        assert isinstance(delivery_info["current_features"], list)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_reasoning_provided(self):
        """Test that reasoning is always provided for delivery estimation."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_info = result["delivery_estimation"]
        assert "reasoning" in delivery_info
        assert isinstance(delivery_info["reasoning"], str)
        assert len(delivery_info["reasoning"]) > 0

    @pytest.mark.asyncio
    async def test_get_delivery_dates_delivery_types(self):
        """Test that appropriate delivery types are assigned."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_info = result["delivery_estimation"]
        delivery_type = delivery_info["delivery_type"]
        
        valid_delivery_types = [
            "immediate_pickup", "transfer_required", "reserved_scheduled", 
            "reserved_estimated", "custom_order", "estimated", "unavailable"
        ]
        assert delivery_type in valid_delivery_types

    @pytest.mark.asyncio
    async def test_get_delivery_dates_with_existing_features(self):
        """Test delivery dates when requesting features already included."""
        # Get a vehicle with features
        from db.connection import get_supabase_client
        client = get_supabase_client()
        
        response = client.table('inventory').select('vehicle_id, features').neq('features', '[]').limit(1).execute()
        if not response.data:
            pytest.skip("No vehicles with features in test data")
        
        vehicle_data = response.data[0]
        vehicle_id = vehicle_data['vehicle_id']
        existing_features = vehicle_data['features'][:1]  # Request one existing feature
        
        result = await get_expected_delivery_dates(vehicle_id, features=existing_features)
        
        delivery_info = result["delivery_estimation"]
        # Should not add delay for features already included
        # or should be minimal delay
        assert delivery_info["feature_installation_delay_days"] == 0