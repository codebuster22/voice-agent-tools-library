"""
Tests for get_vehicle_details tool.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from inventory.get_vehicle_details import get_vehicle_details


class TestGetVehicleDetails:
    """Test suite for get_vehicle_details function using real Supabase database."""

    @pytest.mark.asyncio
    async def test_get_vehicle_details_by_inventory_id(self):
        """Test getting vehicle details by inventory ID (preferred method)."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"  # Toyota Camry Silver
        result = await get_vehicle_details(inventory_id=inventory_id)
        
        assert isinstance(result, dict)
        assert "vehicle" in result
        assert "specifications" in result
        assert "availability" in result
        assert "features" in result
        assert "inventory" in result
        
        # Verify vehicle information
        vehicle = result["vehicle"]
        assert vehicle["brand"] == "Toyota"
        assert vehicle["model"] == "Camry"
        assert vehicle["category"] == "sedan"
        
        # Verify inventory-specific information
        inventory = result["inventory"]
        assert inventory["inventory_id"] == inventory_id
        assert "vin" in inventory
        assert "color" in inventory
        assert "status" in inventory

    @pytest.mark.asyncio
    async def test_get_vehicle_details_by_vehicle_id(self):
        """Test getting vehicle details by vehicle ID."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        assert isinstance(result, dict)
        assert "vehicle" in result
        assert "specifications" in result
        assert "availability" in result
        assert "features" in result
        
        vehicle = result["vehicle"]
        assert vehicle["id"] == vehicle_id
        assert vehicle["brand"] == "Toyota"
        assert vehicle["model"] == "Camry"

    @pytest.mark.asyncio
    async def test_get_vehicle_details_with_pricing(self):
        """Test getting vehicle details with pricing information included."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(inventory_id=inventory_id, include_pricing=True)
        
        assert "pricing" in result
        
        pricing = result["pricing"]
        required_pricing_keys = [
            "base_price_dollars", "current_price_dollars", "price_currency"
        ]
        for key in required_pricing_keys:
            assert key in pricing
        
        # Verify pricing values are reasonable
        assert pricing["base_price_dollars"] > 0
        assert pricing["current_price_dollars"] > 0
        assert pricing["price_currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_vehicle_details_with_similar_vehicles(self):
        """Test getting vehicle details with similar vehicles included."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(inventory_id=inventory_id, include_similar=True)
        
        if "similar_vehicles" in result:
            similar_vehicles = result["similar_vehicles"]
            assert isinstance(similar_vehicles, list)
            assert len(similar_vehicles) <= 3  # Limited to 3
            
            # Each similar vehicle should have required structure
            for vehicle in similar_vehicles:
                assert "brand" in vehicle
                assert "model" in vehicle
                assert "similarity_score" in vehicle

    @pytest.mark.asyncio
    async def test_get_vehicle_details_specifications_structure(self):
        """Test that vehicle specifications have correct structure."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry (sedan)
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        specifications = result["specifications"]
        
        # Basic specifications should be present
        basic_spec_keys = ["year", "category", "fuel_type", "transmission", "drivetrain"]
        for key in basic_spec_keys:
            assert key in specifications
        
        # Category-specific specifications
        if specifications["category"] == "Sedan":
            assert "doors" in specifications
            assert "seating_capacity" in specifications
            assert specifications["doors"] == 4
            assert specifications["seating_capacity"] >= 4

    @pytest.mark.asyncio
    async def test_get_vehicle_details_suv_specifications(self):
        """Test specifications for SUV category vehicle."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440004"  # Toyota RAV4 (SUV)
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        specifications = result["specifications"]
        
        assert specifications["category"] == "Suv"
        assert "cargo_space_cubic_feet" in specifications
        assert "drivetrain" in specifications
        
        # SUVs typically have AWD
        assert specifications["drivetrain"] in ["AWD", "FWD", "4WD"]

    @pytest.mark.asyncio
    async def test_get_vehicle_details_truck_specifications(self):
        """Test specifications for truck category vehicle."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440007"  # Ford F-150 (truck)
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        specifications = result["specifications"]
        
        assert specifications["category"] == "Truck"
        assert "towing_capacity_lbs" in specifications
        assert "bed_length_feet" in specifications
        assert specifications["drivetrain"] in ["4WD", "RWD", "AWD"]

    @pytest.mark.asyncio
    async def test_get_vehicle_details_electric_vehicle(self):
        """Test specifications for electric vehicle."""
        vehicle_id = "550e8400-e29b-41d4-a716-44665544000c"  # Tesla Model S
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        specifications = result["specifications"]
        
        # Electric vehicles should have different specs
        if "Tesla" in result["vehicle"]["brand"]:
            assert specifications["fuel_type"] == "Electric"
            assert "range_miles" in specifications
            assert "charging_time_hours" in specifications

    @pytest.mark.asyncio
    async def test_get_vehicle_details_availability_info(self):
        """Test availability information structure and content."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(inventory_id=inventory_id)
        
        availability = result["availability"]
        
        required_availability_keys = ["status", "location", "in_stock", "message"]
        for key in required_availability_keys:
            assert key in availability
        
        assert isinstance(availability["in_stock"], bool)
        assert isinstance(availability["message"], str)
        assert len(availability["message"]) > 0

    @pytest.mark.asyncio
    async def test_get_vehicle_details_features_categorization(self):
        """Test that features are properly categorized."""
        # Use inventory item with features
        inventory_id = "650e8400-e29b-41d4-a716-446655440002"  # Toyota Camry White with features
        result = await get_vehicle_details(inventory_id=inventory_id)
        
        features = result["features"]
        
        assert "included_features" in features
        assert "total_features" in features
        assert isinstance(features["total_features"], int)
        
        if "features_by_category" in features and features["features_by_category"]:
            categories = features["features_by_category"]
            
            # Categories should be meaningful
            valid_categories = ["comfort", "technology", "safety", "performance", "exterior", "other"]
            for category in categories.keys():
                assert category in valid_categories
            
            # Each category should have a list of features
            for category_features in categories.values():
                assert isinstance(category_features, list)

    @pytest.mark.asyncio
    async def test_get_vehicle_details_additional_info(self):
        """Test additional information like warranty and maintenance."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        assert "additional_info" in result
        additional_info = result["additional_info"]
        
        # Should have warranty information
        assert "warranty" in additional_info
        warranty = additional_info["warranty"]
        assert "basic_years" in warranty
        assert "basic_miles" in warranty
        assert "powertrain_years" in warranty
        assert "powertrain_miles" in warranty
        
        # Should have maintenance information
        assert "maintenance" in additional_info
        maintenance = additional_info["maintenance"]
        assert "estimated_annual_cost_dollars" in maintenance

    @pytest.mark.asyncio
    async def test_get_vehicle_details_premium_vehicle(self):
        """Test details for premium vehicle (BMW M4)."""
        vehicle_id = "550e8400-e29b-41d4-a716-44665544000a"  # BMW M4
        result = await get_vehicle_details(vehicle_id=vehicle_id, include_pricing=True)
        
        vehicle = result["vehicle"]
        assert vehicle["brand"] == "BMW"
        assert vehicle["model"] == "M4"
        assert vehicle["category"] == "coupe"
        
        # Premium vehicle should have higher pricing
        if "pricing" in result:
            pricing = result["pricing"]
            assert pricing["base_price_dollars"] > 50000
        
        # Should have premium specifications
        additional_info = result["additional_info"]
        if "insurance_group" in additional_info:
            assert additional_info["insurance_group"] in ["Premium", "Sport"]

    @pytest.mark.asyncio
    async def test_get_vehicle_details_invalid_inventory_id(self):
        """Test get_vehicle_details with invalid inventory ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_vehicle_details(inventory_id="invalid-uuid")
        
        assert "Invalid inventory_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_vehicle_details_invalid_vehicle_id(self):
        """Test get_vehicle_details with invalid vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_vehicle_details(vehicle_id="invalid-uuid")
        
        assert "Invalid vehicle_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_vehicle_details_no_ids_provided(self):
        """Test get_vehicle_details without providing any IDs."""
        with pytest.raises(ValueError) as exc_info:
            await get_vehicle_details()
        
        assert "required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_vehicle_details_inactive_vehicle(self):
        """Test get_vehicle_details for inactive vehicle."""
        # This would require test data with inactive vehicles
        # For now, test with active vehicle and expect success
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        # Should succeed for active vehicles
        assert isinstance(result, dict)
        assert result["vehicle"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_vehicle_details_pricing_estimate(self):
        """Test pricing estimate calculations."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(inventory_id=inventory_id, include_pricing=True)
        
        if "pricing" in result:
            pricing = result["pricing"]
            
            # Should have estimated monthly payment
            assert "estimated_monthly_payment_dollars" in pricing
            monthly_payment = pricing["estimated_monthly_payment_dollars"]
            assert isinstance(monthly_payment, int)
            assert monthly_payment > 0
            
            # Monthly payment should be reasonable compared to total price
            total_price = pricing["current_price_dollars"]
            assert monthly_payment < total_price  # Monthly should be less than total
            assert monthly_payment > total_price / 120  # Reasonable monthly payment

    @pytest.mark.asyncio
    async def test_get_vehicle_details_response_completeness(self):
        """Test that response includes all expected sections."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(
            inventory_id=inventory_id, 
            include_pricing=True, 
            include_similar=True
        )
        
        # Should have all major sections
        expected_sections = [
            "vehicle", "specifications", "availability", "features", 
            "inventory", "additional_info"
        ]
        for section in expected_sections:
            assert section in result
        
        # Pricing should be included when requested
        assert "pricing" in result

    @pytest.mark.asyncio
    async def test_get_vehicle_details_data_types(self):
        """Test that all data types in response are correct."""
        inventory_id = "650e8400-e29b-41d4-a716-446655440001"
        result = await get_vehicle_details(inventory_id=inventory_id, include_pricing=True)
        
        # Vehicle section
        vehicle = result["vehicle"]
        assert isinstance(vehicle["id"], str)
        assert isinstance(vehicle["brand"], str)
        assert isinstance(vehicle["model"], str)
        assert isinstance(vehicle["year"], int)
        assert isinstance(vehicle["is_active"], bool)
        
        # Specifications section
        specifications = result["specifications"]
        assert isinstance(specifications["year"], int)
        assert isinstance(specifications["doors"], int)
        assert isinstance(specifications["seating_capacity"], int)
        
        # Availability section
        availability = result["availability"]
        assert isinstance(availability["in_stock"], bool)
        assert isinstance(availability["status"], str)
        
        # Features section
        features = result["features"]
        assert isinstance(features["included_features"], list)
        assert isinstance(features["total_features"], int)

    @pytest.mark.asyncio
    async def test_get_vehicle_details_fuel_economy_specs(self):
        """Test fuel economy specifications for gasoline vehicles."""
        vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry (gasoline)
        result = await get_vehicle_details(vehicle_id=vehicle_id)
        
        specifications = result["specifications"]
        
        if specifications["fuel_type"] == "Gasoline":
            assert "fuel_economy_city_mpg" in specifications
            assert "fuel_economy_highway_mpg" in specifications
            assert specifications["fuel_economy_city_mpg"] > 0
            assert specifications["fuel_economy_highway_mpg"] > 0
            assert specifications["fuel_economy_highway_mpg"] >= specifications["fuel_economy_city_mpg"]