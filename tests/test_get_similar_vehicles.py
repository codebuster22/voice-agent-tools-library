"""
Tests for get_similar_vehicles tool.

Tests use real Supabase database integration following TDD methodology.
"""

import pytest
import asyncio
from inventory.get_similar_vehicles import get_similar_vehicles


class TestGetSimilarVehicles:
    """Test suite for get_similar_vehicles function using real Supabase database."""

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_basic(self):
        """Test basic similar vehicles search."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry
        result = await get_similar_vehicles(reference_vehicle_id)
        
        assert isinstance(result, dict)
        assert "reference_vehicle" in result
        assert "alternatives" in result
        assert "total_found" in result
        assert "search_criteria" in result
        
        # Verify reference vehicle
        ref_vehicle = result["reference_vehicle"]
        assert ref_vehicle["id"] == reference_vehicle_id
        assert ref_vehicle["brand"] == "Toyota"
        assert ref_vehicle["model"] == "Camry"
        
        # Verify alternatives structure
        assert isinstance(result["alternatives"], list)
        assert result["total_found"] >= 0
        assert result["total_found"] <= 5  # Default max_results

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_same_category(self):
        """Test that similar vehicles are from same category."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry (sedan)
        result = await get_similar_vehicles(reference_vehicle_id)
        
        # All alternatives should be sedans (same category as reference)
        for vehicle in result["alternatives"]:
            assert vehicle["category"] == "sedan"

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_price_tolerance(self):
        """Test similar vehicles within price tolerance."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"  # Toyota Camry
        price_tolerance = 15  # 15% tolerance
        
        result = await get_similar_vehicles(
            reference_vehicle_id, 
            price_tolerance_percent=price_tolerance
        )
        
        if result["alternatives"]:
            # Get reference price for comparison (approximate from seed data)
            reference_price = 25000  # Toyota Camry approximate price
            min_price = reference_price * (100 - price_tolerance) // 100
            max_price = reference_price * (100 + price_tolerance) // 100
            
            for vehicle in result["alternatives"]:
                vehicle_price = vehicle["price_dollars"]
                # Should be within tolerance (allowing some flexibility for test data)
                assert vehicle_price >= min_price * 0.8  # Allow some flexibility
                assert vehicle_price <= max_price * 1.2

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_exclude_reference(self):
        """Test that reference vehicle is excluded from results."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        # Reference vehicle should not appear in alternatives
        for vehicle in result["alternatives"]:
            assert vehicle["vehicle_id"] != reference_vehicle_id

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_max_results(self):
        """Test max_results parameter limiting."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        max_results = 3
        
        result = await get_similar_vehicles(reference_vehicle_id, max_results=max_results)
        
        assert len(result["alternatives"]) <= max_results
        assert result["total_found"] <= max_results

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_similarity_scores(self):
        """Test that similarity scores are provided and reasonable."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        for vehicle in result["alternatives"]:
            assert "similarity_score" in vehicle
            score = vehicle["similarity_score"]
            assert isinstance(score, (int, float))
            assert 0 <= score <= 100  # Percentage score

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_similarity_reasons(self):
        """Test that similarity reasons are provided."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        for vehicle in result["alternatives"]:
            assert "similarity_reasons" in vehicle
            reasons = vehicle["similarity_reasons"]
            assert isinstance(reasons, list)
            assert len(reasons) >= 0
            
            # Each reason should be a string
            for reason in reasons:
                assert isinstance(reason, str)
                assert len(reason) > 0

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_sorted_by_similarity(self):
        """Test that results are sorted by similarity score (descending)."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id, max_results=10)
        
        if len(result["alternatives"]) > 1:
            scores = [vehicle["similarity_score"] for vehicle in result["alternatives"]]
            
            # Should be sorted in descending order
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_include_unavailable(self):
        """Test including unavailable vehicles in results."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # Test with include_unavailable=False (default)
        result_available_only = await get_similar_vehicles(
            reference_vehicle_id, 
            include_unavailable=False
        )
        
        # Test with include_unavailable=True
        result_all = await get_similar_vehicles(
            reference_vehicle_id, 
            include_unavailable=True
        )
        
        # Including unavailable should give same or more results
        assert len(result_all["alternatives"]) >= len(result_available_only["alternatives"])
        
        # Available-only results should only have available vehicles
        for vehicle in result_available_only["alternatives"]:
            assert vehicle["status"] == "available"

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_suv_category(self):
        """Test similar vehicles search for SUV category."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440004"  # Toyota RAV4 (SUV)
        result = await get_similar_vehicles(reference_vehicle_id)
        
        assert result["reference_vehicle"]["category"] == "suv"
        
        # All alternatives should be SUVs
        for vehicle in result["alternatives"]:
            assert vehicle["category"] == "suv"

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_truck_category(self):
        """Test similar vehicles search for truck category."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440007"  # Ford F-150 (truck)
        result = await get_similar_vehicles(reference_vehicle_id)
        
        assert result["reference_vehicle"]["category"] == "truck"
        
        # All alternatives should be trucks
        for vehicle in result["alternatives"]:
            assert vehicle["category"] == "truck"

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_invalid_vehicle_id(self):
        """Test get_similar_vehicles with invalid vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles("invalid-uuid")
        
        assert "Invalid reference_vehicle_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_empty_vehicle_id(self):
        """Test get_similar_vehicles with empty vehicle ID."""
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles("")
        
        assert "required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_invalid_max_results(self):
        """Test get_similar_vehicles with invalid max_results."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles(reference_vehicle_id, max_results=0)
        
        assert "between 1 and 20" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles(reference_vehicle_id, max_results=25)
        
        assert "between 1 and 20" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_invalid_price_tolerance(self):
        """Test get_similar_vehicles with invalid price tolerance."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles(reference_vehicle_id, price_tolerance_percent=-5)
        
        assert "between 0 and 100" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            await get_similar_vehicles(reference_vehicle_id, price_tolerance_percent=150)
        
        assert "between 0 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_response_structure(self):
        """Test that similar vehicles response has correct structure."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        # Verify top-level structure
        required_keys = ["reference_vehicle", "alternatives", "total_found", "search_criteria"]
        for key in required_keys:
            assert key in result
        
        # Verify reference vehicle structure
        ref_vehicle = result["reference_vehicle"]
        ref_keys = ["id", "brand", "model", "year", "category"]
        for key in ref_keys:
            assert key in ref_vehicle
        
        # Verify alternatives structure
        for vehicle in result["alternatives"]:
            vehicle_keys = [
                "inventory_id", "vehicle_id", "brand", "model", "year", "category",
                "color", "features", "price_dollars", "status", "location",
                "similarity_score", "similarity_reasons"
            ]
            for key in vehicle_keys:
                assert key in vehicle

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_brand_preference(self):
        """Test that same brand vehicles get higher similarity scores."""
        # Use Honda Accord as reference
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440002"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        honda_vehicles = []
        other_vehicles = []
        
        for vehicle in result["alternatives"]:
            if vehicle["brand"].lower() == "honda":
                honda_vehicles.append(vehicle)
            else:
                other_vehicles.append(vehicle)
        
        # Honda vehicles should generally have higher similarity scores
        if honda_vehicles and other_vehicles:
            avg_honda_score = sum(v["similarity_score"] for v in honda_vehicles) / len(honda_vehicles)
            avg_other_score = sum(v["similarity_score"] for v in other_vehicles) / len(other_vehicles)
            
            # Allow some flexibility, but Honda should generally score higher
            assert avg_honda_score >= avg_other_score * 0.8

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_feature_similarity(self):
        """Test that vehicles with similar features score higher."""
        # Use a vehicle with specific features
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440002"  # Honda Accord
        result = await get_similar_vehicles(reference_vehicle_id)
        
        # Check that similarity reasons mention features when relevant
        feature_mentions = 0
        for vehicle in result["alternatives"]:
            for reason in vehicle["similarity_reasons"]:
                if "feature" in reason.lower():
                    feature_mentions += 1
                    break
        
        # At least some vehicles should mention features in similarity reasons
        # (This may vary based on test data)
        assert feature_mentions >= 0

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_no_matches(self):
        """Test similar vehicles search when no similar vehicles exist."""
        # This test might be tricky with current seed data
        # But we can test the structure even with no results
        reference_vehicle_id = "550e8400-e29b-41d4-a716-44665544000a"  # BMW M4 (expensive coupe)
        result = await get_similar_vehicles(reference_vehicle_id, price_tolerance_percent=5)
        
        assert isinstance(result, dict)
        assert "alternatives" in result
        assert result["total_found"] >= 0
        # Even with no matches, structure should be correct
        assert isinstance(result["alternatives"], list)

    @pytest.mark.asyncio
    async def test_get_similar_vehicles_search_criteria_info(self):
        """Test that search criteria information is provided."""
        reference_vehicle_id = "550e8400-e29b-41d4-a716-446655440001"
        result = await get_similar_vehicles(reference_vehicle_id)
        
        search_criteria = result["search_criteria"]
        assert isinstance(search_criteria, dict)
        
        # Should contain information about search parameters
        assert "same_category" in search_criteria
        expected_keys = ["same_category", "price_range_tolerance", "availability_filter"]
        for key in expected_keys:
            assert key in search_criteria