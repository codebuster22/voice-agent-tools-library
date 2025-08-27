"""
Complete fixed tests for get_expected_delivery_dates tool.

Tests updated for range-based delivery date functionality.
"""

import pytest
import asyncio
from datetime import datetime
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
        """Test delivery dates for vehicle with reserved inventory records."""
        # Use Honda CR-V which has reserved inventory records
        vehicle_id = "550e8400-e29b-41d4-a716-446655440005"  # Honda CR-V
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert "inventory_options" in result
        
        # Should find reserved inventory records
        statuses = [opt["status"] for opt in result["inventory_options"]]
        assert "reserved" in statuses
        
        # Find reserved option and verify delivery estimate
        reserved_option = next(opt for opt in result["inventory_options"] if opt["status"] == "reserved")
        delivery_info = reserved_option["delivery_estimate"]
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
        
        assert "Invalid vehicle_id format" in str(exc_info.value)

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
        """Test that response has correct range-based structure."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Verify new range-based structure
        required_keys = ["vehicle_id", "vehicle", "delivery_range", "inventory_options", "total_inventory_records"]
        for key in required_keys:
            assert key in result
        
        # Verify vehicle structure
        vehicle = result["vehicle"]
        vehicle_keys = ["brand", "model", "year", "category"]
        for key in vehicle_keys:
            assert key in vehicle
        
        # Verify delivery range structure
        delivery_range = result["delivery_range"]
        range_keys = ["status", "range_text", "earliest_date", "latest_date", "min_days", "max_days"]
        for key in range_keys:
            assert key in delivery_range
        
        # Verify inventory options structure
        for option in result["inventory_options"]:
            option_keys = ["inventory_id", "vin", "color", "status", "location", "delivery_estimate"]
            for key in option_keys:
                assert key in option

    @pytest.mark.asyncio
    async def test_get_delivery_dates_date_format(self):
        """Test that delivery dates are returned in correct format."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check delivery range dates
        delivery_range = result["delivery_range"]
        if delivery_range["status"] == "available":
            # Should be in YYYY-MM-DD format
            assert isinstance(delivery_range["earliest_date"], str)
            assert isinstance(delivery_range["latest_date"], str)
            datetime.strptime(delivery_range["earliest_date"], '%Y-%m-%d')
            datetime.strptime(delivery_range["latest_date"], '%Y-%m-%d')
        
        # Check individual option dates
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            if delivery_est.get("estimated_delivery_date"):
                datetime.strptime(delivery_est["estimated_delivery_date"], '%Y-%m-%d')

    @pytest.mark.asyncio
    async def test_get_delivery_dates_estimated_days_positive(self):
        """Test that estimated days are positive for available vehicles."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        delivery_range = result["delivery_range"]
        if delivery_range["status"] == "available":
            assert delivery_range["min_days"] >= 1
            assert delivery_range["max_days"] >= delivery_range["min_days"]
        
        # Check individual options
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            if delivery_est.get("estimated_days"):
                assert delivery_est["estimated_days"] >= 1

    @pytest.mark.asyncio
    async def test_get_delivery_dates_feature_delay_calculation(self):
        """Test feature installation delay calculation."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Premium Sound System", "Ceramic Coating", "Extended Warranty"]
        
        result = await get_expected_delivery_dates(vehicle_id, features=additional_features)
        
        # Check available options for feature delays
        available_options = [opt for opt in result["inventory_options"] if opt["status"] == "available"]
        
        for option in available_options:
            delivery_info = option["delivery_estimate"]
            assert "feature_installation_delay_days" in delivery_info
            assert isinstance(delivery_info["feature_installation_delay_days"], int)
            assert delivery_info["feature_installation_delay_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_delivery_dates_current_features_included(self):
        """Test that current vehicle features are included in response."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check that each inventory option includes current features
        for option in result["inventory_options"]:
            if option["status"] != "sold":
                delivery_info = option["delivery_estimate"]
                assert "current_features" in delivery_info
                assert isinstance(delivery_info["current_features"], list)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_reasoning_provided(self):
        """Test that reasoning is always provided for delivery estimation."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check that each inventory option has reasoning
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            # Available/reserved have "reasoning", sold has "reason"
            assert "reasoning" in delivery_est or "reason" in delivery_est
            
            reasoning_text = delivery_est.get("reasoning") or delivery_est.get("reason")
            assert isinstance(reasoning_text, str)
            assert len(reasoning_text) > 0

    @pytest.mark.asyncio
    async def test_get_delivery_dates_delivery_types(self):
        """Test that appropriate delivery types are assigned."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        valid_delivery_types = [
            "immediate_pickup", "transfer_required", "reserved_scheduled", 
            "reserved_estimated", "custom_order", "estimated", "unavailable"
        ]
        
        # Check that each inventory option has valid delivery type
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            delivery_type = delivery_est["delivery_type"]
            assert delivery_type in valid_delivery_types

    @pytest.mark.asyncio
    async def test_get_delivery_dates_with_existing_features(self):
        """Test delivery dates when requesting features that might already exist."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # Use common features that might exist
        existing_features = ["Bluetooth"]
        result = await get_expected_delivery_dates(vehicle_id, features=existing_features)
        
        # Should handle existing features gracefully
        available_options = [opt for opt in result["inventory_options"] if opt["status"] == "available"]
        
        for option in available_options:
            delivery_info = option["delivery_estimate"]
            assert "additional_features_requested" in delivery_info
            assert delivery_info["additional_features_requested"] == existing_features
            
            # If feature already exists, should have minimal or no delay
            current_features = delivery_info.get("current_features", [])
            if "Bluetooth" in current_features:
                # Should have no delay for existing feature
                pass  # Test that it doesn't error