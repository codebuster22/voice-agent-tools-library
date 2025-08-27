"""
Tests for check_inventory tool.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from inventory.check_inventory import check_inventory


class TestCheckInventory:
    """Test suite for check_inventory function using real Supabase database."""

    @pytest.mark.asyncio
    async def test_check_inventory_no_filters(self):
        """Test inventory search with no filters (should return available vehicles)."""
        result = await check_inventory()
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert "total_count" in result
        assert "filters_applied" in result
        assert isinstance(result["vehicles"], list)
        assert result["total_count"] >= 0
        
        # Should have vehicles with available status by default
        if result["vehicles"]:
            for vehicle in result["vehicles"]:
                assert vehicle["status"] == "available"

    @pytest.mark.asyncio
    async def test_check_inventory_by_category(self):
        """Test inventory search filtered by category."""
        result = await check_inventory(category="sedan")
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["filters_applied"]["category"] == "sedan"
        
        # All returned vehicles should be sedans
        for vehicle in result["vehicles"]:
            assert vehicle["category"] == "sedan"

    @pytest.mark.asyncio
    async def test_check_inventory_by_model_name(self):
        """Test inventory search by model name (text search)."""
        result = await check_inventory(model_name="Toyota")
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["filters_applied"]["model_name"] == "Toyota"
        
        # All returned vehicles should contain "Toyota" in brand or model
        for vehicle in result["vehicles"]:
            vehicle_text = f"{vehicle['brand']} {vehicle['model']}".lower()
            assert "toyota" in vehicle_text

    @pytest.mark.asyncio
    async def test_check_inventory_by_price_range(self):
        """Test inventory search with price range filters."""
        min_price = 20000
        max_price = 40000
        result = await check_inventory(min_price=min_price, max_price=max_price)
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["filters_applied"]["min_price"] == min_price
        assert result["filters_applied"]["max_price"] == max_price
        
        # All returned vehicles should be within price range
        for vehicle in result["vehicles"]:
            assert min_price <= vehicle["price"] <= max_price

    @pytest.mark.asyncio
    async def test_check_inventory_with_features(self):
        """Test inventory search requiring specific features."""
        required_features = ["Leather Seats", "Navigation System"]
        result = await check_inventory(features=required_features)
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["filters_applied"]["features"] == required_features
        
        # All returned vehicles should have ALL required features
        for vehicle in result["vehicles"]:
            vehicle_features = vehicle["features"]
            for required_feature in required_features:
                assert required_feature in vehicle_features

    @pytest.mark.asyncio
    async def test_check_inventory_all_statuses(self):
        """Test inventory search including all vehicle statuses."""
        result = await check_inventory(status="all")
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        
        # Should include vehicles with different statuses
        if result["vehicles"]:
            statuses = set(vehicle["status"] for vehicle in result["vehicles"])
            assert len(statuses) >= 1  # At least one status type

    @pytest.mark.asyncio
    async def test_check_inventory_reserved_status(self):
        """Test inventory search for reserved vehicles only."""
        result = await check_inventory(status="reserved")
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["filters_applied"]["status"] == "reserved"
        
        # All returned vehicles should be reserved
        for vehicle in result["vehicles"]:
            assert vehicle["status"] == "reserved"

    @pytest.mark.asyncio
    async def test_check_inventory_combined_filters(self):
        """Test inventory search with multiple filters combined."""
        result = await check_inventory(
            category="suv",
            min_price=25000,
            max_price=50000,
            features=["All-Wheel Drive"],
            status="available"
        )
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        
        # Verify all filters are applied correctly
        filters = result["filters_applied"]
        assert filters["category"] == "suv"
        assert filters["min_price"] == 25000
        assert filters["max_price"] == 50000
        assert filters["features"] == ["All-Wheel Drive"]
        assert filters["status"] == "available"
        
        # Verify all vehicles match all criteria
        for vehicle in result["vehicles"]:
            assert vehicle["category"] == "suv"
            assert 25000 <= vehicle["price"] <= 50000
            assert "All-Wheel Drive" in vehicle["features"]
            assert vehicle["status"] == "available"

    @pytest.mark.asyncio
    async def test_check_inventory_no_results(self):
        """Test inventory search with filters that yield no results."""
        result = await check_inventory(
            category="sedan",
            min_price=100000,  # Very high price for sedans
            max_price=200000
        )
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        assert result["total_count"] == 0
        assert len(result["vehicles"]) == 0

    @pytest.mark.asyncio
    async def test_check_inventory_invalid_category(self):
        """Test inventory search with invalid category."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(category="invalid_category")
        
        assert "Invalid category" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_inventory_invalid_status(self):
        """Test inventory search with invalid status."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(status="invalid_status")
        
        assert "Invalid status" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_inventory_negative_price(self):
        """Test inventory search with negative price values."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=-1000)
        
        assert "Price cannot be negative" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_inventory_invalid_price_range(self):
        """Test inventory search with min_price greater than max_price."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=50000, max_price=30000)
        
        assert "min_price cannot be greater than max_price" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_inventory_response_structure(self):
        """Test that inventory response has correct structure and data types."""
        result = await check_inventory(category="sedan")
        
        # Verify top-level structure
        assert isinstance(result, dict)
        required_keys = ["vehicles", "total_count", "filters_applied"]
        for key in required_keys:
            assert key in result
        
        # Verify vehicles structure
        assert isinstance(result["vehicles"], list)
        assert isinstance(result["total_count"], int)
        assert isinstance(result["filters_applied"], dict)
        
        if result["vehicles"]:
            vehicle = result["vehicles"][0]
            expected_vehicle_keys = [
                "inventory_id", "vehicle_id", "brand", "model", "category",
                "color", "features", "price", "status", "delivery_date"
            ]
            for key in expected_vehicle_keys:
                assert key in vehicle
            
            # Verify data types
            assert isinstance(vehicle["inventory_id"], str)
            assert isinstance(vehicle["vehicle_id"], str)
            assert isinstance(vehicle["brand"], str)
            assert isinstance(vehicle["model"], str)
            assert isinstance(vehicle["category"], str)
            assert isinstance(vehicle["color"], str)
            assert isinstance(vehicle["features"], list)
            assert isinstance(vehicle["price"], int)
            assert isinstance(vehicle["status"], str)

    @pytest.mark.asyncio
    async def test_check_inventory_price_conversion(self):
        """Test that prices are correctly converted from cents to dollars."""
        result = await check_inventory(category="sedan")
        
        if result["vehicles"]:
            vehicle = result["vehicles"][0]
            # Price should be a reasonable dollar amount (not in cents)
            assert vehicle["price"] >= 1000  # At least $1,000
            assert vehicle["price"] <= 200000  # At most $200,000
            assert isinstance(vehicle["price"], int)

    @pytest.mark.asyncio
    async def test_check_inventory_empty_features_list(self):
        """Test inventory search with empty features list."""
        result = await check_inventory(features=[])
        
        assert isinstance(result, dict)
        assert "vehicles" in result
        # Empty features list should not be included in filters_applied
        assert "features" not in result["filters_applied"]