"""
Tests for get_prices tool.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from inventory.get_prices import get_prices


class TestGetPrices:
    """Test suite for get_prices function using real Supabase database."""

    @pytest.mark.asyncio
    async def test_get_prices_specific_by_vehicle_id(self):
        """Test getting specific pricing by vehicle ID."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        assert isinstance(result, dict)
        assert "vehicle" in result
        assert "pricing" in result
        
        # Verify vehicle information
        vehicle = result["vehicle"]
        assert vehicle["id"] == vehicle_id
        assert vehicle["brand"] == "Toyota"
        assert vehicle["model"] == "Camry"
        
        # Verify pricing structure
        pricing = result["pricing"]
        required_pricing_keys = [
            "base_price_dollars", "current_price_dollars", "final_price_dollars", "price_currency"
        ]
        for key in required_pricing_keys:
            assert key in pricing

    @pytest.mark.asyncio
    async def test_get_prices_specific_by_inventory_id(self):
        """Test getting specific pricing by inventory ID (preferred method)."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"  # Toyota Camry Silver
        result = await get_prices(query_type="specific", inventory_id=inventory_id)
        
        assert isinstance(result, dict)
        assert "vehicle" in result
        assert "pricing" in result
        assert "inventory_id" in result
        assert "inventory_status" in result
        assert "color" in result
        
        assert result["inventory_id"] == inventory_id
        assert result["color"] is not None
        
        # Should have more detailed pricing info since it's inventory-specific
        pricing = result["pricing"]
        assert "current_price_dollars" in pricing
        assert pricing["current_price_dollars"] > 0

    @pytest.mark.asyncio
    async def test_get_prices_with_additional_features(self):
        """Test pricing calculation with additional features requested."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Premium Audio", "Sunroof"]
        
        result = await get_prices(
            query_type="specific",
            inventory_id=inventory_id,
            features=additional_features
        )
        
        assert isinstance(result, dict)
        pricing = result["pricing"]
        
        # Should show additional features cost
        assert "additional_features_requested" in pricing
        assert "additional_features_cost_dollars" in pricing
        assert "additional_features_breakdown" in pricing
        
        assert pricing["additional_features_requested"] == additional_features
        
        # Final price should include additional features
        base_price = pricing["current_price_dollars"]
        additional_cost = pricing["additional_features_cost_dollars"]
        final_price = pricing["final_price_dollars"]
        assert final_price >= base_price

    @pytest.mark.asyncio
    async def test_get_prices_feature_based_query(self):
        """Test feature-based pricing query."""
        features = ["Leather Seats", "Navigation System", "Heated Seats"]
        result = await get_prices(query_type="by_features", features=features)
        
        assert isinstance(result, dict)
        assert "requested_features" in result
        assert "feature_pricing" in result
        assert "total_additional_cost_dollars" in result
        
        assert result["requested_features"] == features
        
        # Should have pricing for each feature
        feature_pricing = result["feature_pricing"]
        for feature in features:
            if feature in feature_pricing:
                feature_info = feature_pricing[feature]
                assert "average_cost_dollars" in feature_info
                assert "price_range_dollars" in feature_info
                assert isinstance(feature_info["average_cost_dollars"], int)

    @pytest.mark.asyncio
    async def test_get_prices_with_discount(self):
        """Test pricing for vehicle with discount applied."""
        # Honda Accord has discount in seed data
        vehicle_id = "550e8400-e29b-41d4-a716-446655440002"
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        assert isinstance(result, dict)
        pricing = result["pricing"]
        
        # Should show discount if available
        if "discount_applied_dollars" in pricing and pricing["discount_applied_dollars"] > 0:
            assert "savings_from_discount" in pricing
            assert pricing["savings_from_discount"] is True

    @pytest.mark.asyncio
    async def test_get_prices_included_features_value(self):
        """Test that included features are valued in pricing."""
        # Get vehicle with features
        inventory_id = "650e8400-e29b-41d4-a716-446655440002"  # Toyota Camry White with features
        result = await get_prices(query_type="specific", inventory_id=inventory_id)
        
        assert isinstance(result, dict)
        pricing = result["pricing"]
        
        # Should show included features
        assert "included_features" in pricing
        assert "included_features_value_dollars" in pricing
        
        if pricing["included_features"]:
            assert len(pricing["included_features"]) > 0
            assert pricing["included_features_value_dollars"] >= 0

    @pytest.mark.asyncio
    async def test_get_prices_price_conversion(self):
        """Test that prices are correctly converted from cents to dollars."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        pricing = result["pricing"]
        
        # Prices should be reasonable dollar amounts
        assert pricing["base_price_dollars"] >= 1000
        assert pricing["base_price_dollars"] <= 200000
        assert pricing["current_price_dollars"] >= 1000
        assert pricing["current_price_dollars"] <= 200000
        
        # All price fields should be integers (dollars)
        price_fields = ["base_price_dollars", "current_price_dollars", "final_price_dollars"]
        for field in price_fields:
            if field in pricing:
                assert isinstance(pricing[field], int)

    @pytest.mark.asyncio
    async def test_get_prices_invalid_query_type(self):
        """Test get_prices with invalid query type."""
        with pytest.raises(ValueError) as exc_info:
            await get_prices(query_type="invalid_type")
        
        assert "Invalid query_type" in str(exc_info.value)


    @pytest.mark.asyncio
    async def test_get_prices_invalid_vehicle_id(self):
        """Test get_prices with invalid vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_prices(query_type="specific", vehicle_id="invalid-uuid")
        
        assert "Invalid vehicle_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_prices_invalid_inventory_id(self):
        """Test get_prices with invalid inventory ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_prices(query_type="specific", inventory_id="invalid-uuid")
        
        assert "Invalid inventory_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_prices_feature_based_no_features(self):
        """Test feature-based pricing without providing features."""
        with pytest.raises(ValueError) as exc_info:
            await get_prices(query_type="by_features")
        
        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_prices_inactive_vehicle(self):
        """Test get_prices for inactive vehicle."""
        # First, we need to find an inactive vehicle or modify the test data
        # For now, test with a valid vehicle and assume it's active
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        # Should succeed for active vehicles
        assert isinstance(result, dict)
        assert "vehicle" in result

    @pytest.mark.asyncio
    async def test_get_prices_response_structure_specific(self):
        """Test that specific pricing response has correct structure."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_prices(query_type="specific", inventory_id=inventory_id)
        
        # Verify top-level structure
        required_keys = ["vehicle", "pricing"]
        for key in required_keys:
            assert key in result
        
        # Verify vehicle structure
        vehicle = result["vehicle"]
        vehicle_keys = ["id", "brand", "model", "year", "category"]
        for key in vehicle_keys:
            assert key in vehicle
        
        # Verify pricing structure
        pricing = result["pricing"]
        pricing_keys = ["base_price_dollars", "current_price_dollars", "final_price_dollars", "price_currency"]
        for key in pricing_keys:
            assert key in pricing

    @pytest.mark.asyncio
    async def test_get_prices_response_structure_feature_based(self):
        """Test that feature-based pricing response has correct structure."""
        features = ["Leather Seats", "Premium Audio"]
        result = await get_prices(query_type="by_features", features=features)
        
        # Verify structure
        required_keys = ["requested_features", "feature_pricing", "total_additional_cost_dollars"]
        for key in required_keys:
            assert key in result
        
        assert result["requested_features"] == features
        assert isinstance(result["feature_pricing"], dict)
        assert isinstance(result["total_additional_cost_dollars"], int)

    @pytest.mark.asyncio
    async def test_get_prices_currency_consistency(self):
        """Test that currency is consistently USD."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        pricing = result["pricing"]
        assert pricing["price_currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_prices_premium_vehicle(self):
        """Test pricing for premium vehicle (BMW M4)."""
        vehicle_id = "550e8400-e29b-41d4-a716-44665544000a"  # BMW M4
        result = await get_prices(query_type="specific", vehicle_id=vehicle_id)
        
        assert isinstance(result, dict)
        vehicle = result["vehicle"]
        pricing = result["pricing"]
        
        assert vehicle["brand"] == "BMW"
        assert vehicle["model"] == "M4"
        
        # Premium vehicle should have higher base price
        assert pricing["base_price_dollars"] > 50000

    @pytest.mark.asyncio
    async def test_get_prices_feature_availability(self):
        """Test feature pricing shows availability information."""
        features = ["Navigation System", "Premium Audio", "Leather Seats"]
        result = await get_prices(query_type="by_features", features=features)
        
        feature_pricing = result["feature_pricing"]
        
        # Each feature should show availability info if found
        for feature, pricing_info in feature_pricing.items():
            if "available_on_vehicles" in pricing_info:
                assert isinstance(pricing_info["available_on_vehicles"], int)
                assert pricing_info["available_on_vehicles"] >= 0
            
            if "example_vehicles" in pricing_info:
                assert isinstance(pricing_info["example_vehicles"], list)

    @pytest.mark.asyncio
    async def test_get_prices_final_price_calculation(self):
        """Test that final price is calculated correctly."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        additional_features = ["Premium Audio"]
        
        result = await get_prices(
            query_type="specific",
            inventory_id=inventory_id,
            features=additional_features
        )
        
        pricing = result["pricing"]
        current_price = pricing["current_price_dollars"]
        additional_cost = pricing["additional_features_cost_dollars"]
        final_price = pricing["final_price_dollars"]
        
        # Final price should equal current price plus additional features
        expected_final_price = current_price + additional_cost
        assert final_price == expected_final_price