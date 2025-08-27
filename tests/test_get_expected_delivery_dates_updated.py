"""
Updated tests for get_expected_delivery_dates tool with range-based functionality.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from inventory.get_expected_delivery_dates import get_expected_delivery_dates


class TestGetExpectedDeliveryDatesUpdated:
    """Updated test suite for range-based delivery date functionality."""

    @pytest.mark.asyncio
    async def test_get_delivery_dates_range_functionality(self):
        """Test that function returns delivery date ranges for multiple inventory records."""
        # Use Toyota Camry which has 4 inventory records (available, reserved, sold)
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Verify new response structure
        assert isinstance(result, dict)
        assert "vehicle_id" in result
        assert "vehicle" in result
        assert "delivery_range" in result
        assert "inventory_options" in result
        assert "total_inventory_records" in result
        
        # Verify vehicle info
        assert result["vehicle_id"] == vehicle_id
        assert result["vehicle"]["brand"] == "Toyota"
        assert result["vehicle"]["model"] == "Camry"
        
        # Verify delivery range structure
        delivery_range = result["delivery_range"]
        assert "status" in delivery_range
        assert "range_text" in delivery_range
        assert "earliest_date" in delivery_range
        assert "latest_date" in delivery_range
        assert "min_days" in delivery_range
        assert "max_days" in delivery_range
        assert "total_options" in delivery_range
        
        # Should have range of dates (not single date)
        assert delivery_range["min_days"] >= 1
        assert delivery_range["max_days"] >= delivery_range["min_days"]
        
        # Should have multiple inventory options
        assert result["total_inventory_records"] >= 3
        assert len(result["inventory_options"]) >= 3

    @pytest.mark.asyncio
    async def test_get_delivery_dates_handles_different_statuses(self):
        """Test that function handles available, reserved, and sold inventory records."""
        # Use Toyota Camry which has mixed statuses
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Check that we have different statuses in inventory options
        statuses = [option["status"] for option in result["inventory_options"]]
        
        # Should include multiple statuses
        assert "available" in statuses
        assert "reserved" in statuses or "sold" in statuses
        
        # Verify each inventory option has proper structure
        for option in result["inventory_options"]:
            assert "inventory_id" in option
            assert "vin" in option
            assert "color" in option
            assert "status" in option
            assert "location" in option
            assert "delivery_estimate" in option
            
            # Each delivery estimate should have proper structure
            delivery_est = option["delivery_estimate"]
            assert "status" in delivery_est
            assert "delivery_type" in delivery_est
            # Available/reserved have "reasoning", sold has "reason"
            assert "reasoning" in delivery_est or "reason" in delivery_est

    @pytest.mark.asyncio
    async def test_get_delivery_dates_excludes_sold_from_range(self):
        """Test that sold vehicles are excluded from delivery range calculation."""
        # Use Toyota Camry which has a sold record
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Should have sold inventory option
        statuses = [option["status"] for option in result["inventory_options"]]
        assert "sold" in statuses
        
        # But delivery range should still be available (other records exist)
        assert result["delivery_range"]["status"] == "available"
        
        # Sold option should be marked as unavailable
        sold_option = next(opt for opt in result["inventory_options"] if opt["status"] == "sold")
        assert sold_option["delivery_estimate"]["status"] == "unavailable"
        assert sold_option["delivery_estimate"]["estimated_delivery_date"] is None

    @pytest.mark.asyncio  
    async def test_get_delivery_dates_different_locations(self):
        """Test delivery date ranges for vehicles at different locations."""
        # Use Toyota RAV4 which has vehicles at main_dealership and service_center
        vehicle_id = "550e8400-e29b-41d4-a716-446655440004"
        result = await get_expected_delivery_dates(vehicle_id)
        
        # Should have multiple locations
        locations = [option["location"] for option in result["inventory_options"]]
        assert len(set(locations)) >= 2  # At least 2 different locations
        
        # Should show different delivery times for different locations
        main_dealership_options = [opt for opt in result["inventory_options"] 
                                 if opt["location"] == "main_dealership" and opt["status"] == "available"]
        other_location_options = [opt for opt in result["inventory_options"] 
                                if opt["location"] != "main_dealership" and opt["status"] == "available"]
        
        if main_dealership_options and other_location_options:
            main_days = main_dealership_options[0]["delivery_estimate"]["estimated_days"]
            other_days = other_location_options[0]["delivery_estimate"]["estimated_days"]
            # Transfer should take longer than immediate pickup
            assert other_days >= main_days

    @pytest.mark.asyncio
    async def test_get_delivery_dates_with_features(self):
        """Test delivery date calculation with additional features."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Premium Sound System", "Tinted Windows"]
        
        result = await get_expected_delivery_dates(vehicle_id, features=additional_features)
        
        # Should include feature information in delivery estimates
        for option in result["inventory_options"]:
            if option["status"] == "available":
                delivery_est = option["delivery_estimate"]
                assert "additional_features_requested" in delivery_est
                assert "feature_installation_delay_days" in delivery_est
                assert delivery_est["additional_features_requested"] == additional_features

    @pytest.mark.asyncio
    async def test_get_delivery_dates_range_text_formatting(self):
        """Test that range_text is properly formatted for human reading."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_expected_delivery_dates(vehicle_id)
        
        range_text = result["delivery_range"]["range_text"]
        
        # Should be a non-empty string
        assert isinstance(range_text, str)
        assert len(range_text) > 0
        
        # Should contain meaningful information
        assert any(word in range_text.lower() for word in 
                  ["available", "day", "days", "week", "weeks", "immediately"])

    @pytest.mark.asyncio
    async def test_get_delivery_dates_invalid_vehicle_id(self):
        """Test get_expected_delivery_dates with invalid vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_expected_delivery_dates("invalid-uuid-format")
        
        assert "Invalid vehicle_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_delivery_dates_nonexistent_vehicle_id(self):
        """Test get_expected_delivery_dates with valid but nonexistent vehicle ID."""
        nonexistent_uuid = "99999999-e29b-41d4-a716-446655440999"
        with pytest.raises(ValueError) as exc_info:
            await get_expected_delivery_dates(nonexistent_uuid)
        
        assert "not found" in str(exc_info.value)