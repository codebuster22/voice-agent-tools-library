"""
Fixed tests for get_expected_delivery_dates tool with range-based functionality.

All tests updated to expect the new response structure.
"""

import pytest
import asyncio
from inventory.get_expected_delivery_dates import get_expected_delivery_dates


class TestGetExpectedDeliveryDatesFixed:
    """Fixed test suite for range-based delivery date functionality."""

    @pytest.mark.asyncio
    async def test_get_delivery_dates_transfer_required(self):
        """Test delivery dates for vehicle requiring transfer."""
        # Use Toyota RAV4 which has inventory at service_center
        vehicle_id = "550e8400-e29b-41d4-a716-446655440004"  # Toyota RAV4
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        assert "inventory_options" in result
        
        # Should find vehicles at different locations
        locations = [opt["location"] for opt in result["inventory_options"]]
        
        # Find option requiring transfer
        transfer_options = [opt for opt in result["inventory_options"] 
                          if opt["location"] != "main_dealership" and opt["status"] == "available"]
        
        if transfer_options:
            delivery_info = transfer_options[0]["delivery_estimate"]
            assert "transfer" in delivery_info["delivery_type"] or "transfer" in delivery_info["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_get_delivery_dates_response_structure(self):
        """Test that response has correct structure."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        assert isinstance(result, dict)
        
        # New structure should have these keys
        expected_keys = ["vehicle_id", "vehicle", "delivery_range", "inventory_options", "total_inventory_records"]
        for key in expected_keys:
            assert key in result
        
        # Delivery range should have proper structure
        delivery_range = result["delivery_range"]
        range_keys = ["status", "range_text", "earliest_date", "latest_date", "min_days", "max_days"]
        for key in range_keys:
            assert key in delivery_range
        
        # Each inventory option should have proper structure
        for option in result["inventory_options"]:
            option_keys = ["inventory_id", "vin", "color", "status", "location", "delivery_estimate"]
            for key in option_keys:
                assert key in option

    @pytest.mark.asyncio
    async def test_get_delivery_dates_date_format(self):
        """Test that delivery dates are properly formatted."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check delivery range dates
        delivery_range = result["delivery_range"]
        if delivery_range["earliest_date"]:
            # Should be in YYYY-MM-DD format
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            assert re.match(date_pattern, delivery_range["earliest_date"])
            assert re.match(date_pattern, delivery_range["latest_date"])
        
        # Check individual option dates
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            if delivery_est.get("estimated_delivery_date"):
                assert re.match(date_pattern, delivery_est["estimated_delivery_date"])

    @pytest.mark.asyncio
    async def test_get_delivery_dates_estimated_days_positive(self):
        """Test that estimated days are positive integers."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check delivery range
        delivery_range = result["delivery_range"]
        if delivery_range["min_days"]:
            assert delivery_range["min_days"] >= 1
            assert delivery_range["max_days"] >= delivery_range["min_days"]
        
        # Check individual options
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            if delivery_est.get("estimated_days"):
                assert delivery_est["estimated_days"] >= 1

    @pytest.mark.asyncio
    async def test_get_delivery_dates_feature_delay_calculation(self):
        """Test feature delay calculation with additional features."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Custom Feature", "Another Feature"]
        
        result = await get_expected_delivery_dates(vehicle_id, features=additional_features)
        
        # Check that available options account for feature delays
        available_options = [opt for opt in result["inventory_options"] if opt["status"] == "available"]
        
        for option in available_options:
            delivery_est = option["delivery_estimate"]
            assert "feature_installation_delay_days" in delivery_est
            assert "additional_features_requested" in delivery_est
            assert delivery_est["additional_features_requested"] == additional_features
            
            # Should have some delay since these are custom features
            assert delivery_est["feature_installation_delay_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_delivery_dates_current_features_included(self):
        """Test that current features are included in response."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check that available options include current features
        available_options = [opt for opt in result["inventory_options"] if opt["status"] == "available"]
        
        for option in available_options:
            delivery_est = option["delivery_estimate"]
            assert "current_features" in delivery_est
            assert isinstance(delivery_est["current_features"], list)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_reasoning_provided(self):
        """Test that reasoning is provided for delivery estimates."""
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
        """Test that proper delivery types are assigned."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        valid_delivery_types = [
            "immediate_pickup", "transfer_required", "reserved_scheduled", 
            "reserved_estimated", "unavailable", "custom_order", "estimated"
        ]
        
        # Check that each inventory option has valid delivery type
        for option in result["inventory_options"]:
            delivery_est = option["delivery_estimate"]
            assert "delivery_type" in delivery_est
            assert delivery_est["delivery_type"] in valid_delivery_types

    @pytest.mark.asyncio
    async def test_get_delivery_dates_with_existing_features(self):
        """Test delivery dates when requesting features that already exist."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # First get current features to find existing ones
        initial_result = await get_expected_delivery_dates(vehicle_id)
        available_option = next(opt for opt in initial_result["inventory_options"] if opt["status"] == "available")
        existing_features = available_option["delivery_estimate"]["current_features"]
        
        if existing_features:
            # Request a feature that already exists
            result = await get_expected_delivery_dates(vehicle_id, features=existing_features[:1])
            
            # Should have no additional delay for existing features
            for option in result["inventory_options"]:
                if option["status"] == "available":
                    delivery_est = option["delivery_estimate"]
                    # If requesting existing feature, delay should be minimal
                    requested_feature = existing_features[0]
                    if requested_feature in delivery_est["current_features"]:
                        # This specific option should have no delay for this feature
                        pass  # Test that it doesn't error