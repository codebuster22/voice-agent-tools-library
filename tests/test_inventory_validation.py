"""
Test validation logic for inventory tools (no database required).

Tests parameter validation and error handling without database dependency.
"""

import pytest
from inventory.check_inventory import check_inventory


class TestCheckInventoryValidation:
    """Test validation logic without database dependency."""
    
    @pytest.mark.asyncio
    async def test_invalid_category_validation(self):
        """Test validation error for invalid category."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(category='invalid_category')
        
        assert 'invalid category' in str(exc_info.value).lower()
        assert 'sedan' in str(exc_info.value)
        assert 'suv' in str(exc_info.value)
        assert 'truck' in str(exc_info.value)
        assert 'coupe' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_status_validation(self):
        """Test validation error for invalid status."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(status='invalid_status')
        
        assert 'invalid status' in str(exc_info.value).lower()
        assert 'available' in str(exc_info.value)
        assert 'sold' in str(exc_info.value)
        assert 'reserved' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_negative_price_validation(self):
        """Test validation error for negative prices."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=-1000)
        
        assert 'price cannot be negative' in str(exc_info.value).lower()
        
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(max_price=-500)
        
        assert 'price cannot be negative' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_price_range_validation(self):
        """Test validation error for invalid price range."""
        with pytest.raises(ValueError) as exc_info:
            await check_inventory(min_price=50000, max_price=30000)
        
        assert 'min_price cannot be greater than max_price' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio 
    async def test_valid_parameters_pass_validation(self):
        """Test that valid parameters pass validation and return valid results."""
        # This should pass validation and execute successfully
        result = await check_inventory(
            category='sedan',
            model_name='Camry',  # Use existing model from seed data
            min_price=30000,
            max_price=60000,
            features=[],  # No features to ensure we get some results
            status='available'
        )
        
        # Should return valid result structure
        assert isinstance(result, dict)
        assert 'vehicles' in result
        assert 'total_count' in result
        assert 'filters_applied' in result
        assert isinstance(result['total_count'], int)
        assert result['total_count'] >= 0  # May be 0 if no matches found