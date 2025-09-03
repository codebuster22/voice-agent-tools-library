import pytest
from datetime import datetime, timezone, timedelta
from calendar_tools.tools.get_availability import get_availability
from calendar_tools.auth import create_service


def _parse_datetime(iso_string):
    """Parse datetime string, handling 'Z' UTC suffix."""
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    return datetime.fromisoformat(iso_string)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_availability_default_parameters(test_email):
    """Test get_availability with default parameters (today to next week, working hours)."""
    # This test will use real Google Calendar API with service account
    email = test_email
    
    service = await create_service(email)
    availability = await get_availability(service)
    
    # Verify response structure
    assert isinstance(availability, dict)
    assert 'free_slots' in availability
    assert 'busy_periods' in availability
    assert 'working_hours' in availability
    assert 'date_range' in availability
    
    # Verify working hours defaults
    assert availability['working_hours']['start'] == 9
    assert availability['working_hours']['end'] == 17
    assert availability['working_hours']['days'] == [0, 1, 2, 3, 4]  # Mon-Fri


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_availability_custom_date_range(test_email):
    """Test get_availability with custom start and end times."""
    email = test_email
    
    service = await create_service(email)
    start_time = datetime(2024, 8, 26, 0, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 8, 27, 23, 59, 59, tzinfo=timezone.utc)
    
    availability = await get_availability(
        service,
        start_time=start_time,
        end_time=end_time
    )
    
    # Verify date range is correctly applied
    assert availability['date_range']['start'] == start_time.isoformat()
    assert availability['date_range']['end'] == end_time.isoformat()


@pytest.mark.asyncio
async def test_get_availability_multiple_calendars():
    """Test get_availability with multiple calendar IDs."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    calendar_ids = ['primary']  # Start with just primary for testing
    
    availability = await get_availability(service, calendar_ids=calendar_ids)
    
    # Should handle multiple calendars
    assert isinstance(availability['busy_periods'], list)


@pytest.mark.asyncio
async def test_get_availability_custom_working_hours():
    """Test get_availability with custom working hours."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    availability = await get_availability(
        service,
        working_hours_start=8,
        working_hours_end=18,
        working_days=[0, 1, 2, 3, 4, 5]  # Monday to Saturday
    )
    
    # Verify custom working hours are applied
    assert availability['working_hours']['start'] == 8
    assert availability['working_hours']['end'] == 18
    assert availability['working_hours']['days'] == [0, 1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_get_availability_weekend_exclusion():
    """Test that weekends are excluded by default from working days."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    # Get availability for a date range that includes weekend
    start_time = datetime(2024, 8, 23, 0, 0, 0, tzinfo=timezone.utc)  # Friday
    end_time = datetime(2024, 8, 26, 23, 59, 59, tzinfo=timezone.utc)   # Monday
    
    availability = await get_availability(
        service,
        start_time=start_time,
        end_time=end_time
    )
    
    # Free slots should not include Saturday/Sunday
    free_slots = availability['free_slots']
    for slot in free_slots:
        slot_date = _parse_datetime(slot['start'])
        # 5=Saturday, 6=Sunday should not be present
        assert slot_date.weekday() not in [5, 6], f"Weekend slot found: {slot}"


@pytest.mark.asyncio
async def test_get_availability_invalid_working_hours():
    """Test get_availability with invalid working hours parameters."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Test invalid working hours (end before start)
    with pytest.raises(ValueError) as exc_info:
        await get_availability(
            service,
            working_hours_start=17,
            working_hours_end=9
        )
    
    assert "working_hours_start must be less than working_hours_end" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_availability_invalid_working_days():
    """Test get_availability with invalid working days."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Test invalid working days (outside 0-6 range)
    with pytest.raises(ValueError) as exc_info:
        await get_availability(
            service,
            working_days=[0, 1, 2, 7, 8]  # 7 and 8 are invalid
        )
    
    assert "working_days must contain values between 0-6" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_availability_response_format():
    """Test that get_availability returns data in expected format."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    availability = await get_availability(service)
    
    # Verify response structure
    assert isinstance(availability, dict)
    assert 'free_slots' in availability
    assert 'busy_periods' in availability
    assert 'working_hours' in availability
    assert 'date_range' in availability
    
    # Verify free_slots format
    for slot in availability['free_slots']:
        assert 'start' in slot
        assert 'end' in slot
        assert 'duration_minutes' in slot
        assert isinstance(slot['duration_minutes'], int)
    
    # Verify busy_periods format
    for period in availability['busy_periods']:
        assert 'start' in period
        assert 'end' in period
        assert 'calendar_id' in period


@pytest.mark.asyncio
async def test_get_availability_slot_duration_calculation():
    """Test that free slot durations are calculated correctly."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    availability = await get_availability(service)
    
    # Verify duration calculation for free slots
    for slot in availability['free_slots']:
        start_time = _parse_datetime(slot['start'])
        end_time = _parse_datetime(slot['end'])
        expected_duration = int((end_time - start_time).total_seconds() / 60)
        assert slot['duration_minutes'] == expected_duration


@pytest.mark.asyncio
async def test_get_availability_timezone_handling():
    """Test get_availability with custom timezone."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Test with specific timezone
    availability = await get_availability(
        service,
        time_zone='US/Eastern'
    )
    
    # Should handle timezone without errors
    assert 'free_slots' in availability


@pytest.mark.asyncio
async def test_get_availability_empty_calendar():
    """Test get_availability when calendar has no busy periods."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Use a future date range likely to be empty
    start_time = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 12, 2, 23, 59, 59, tzinfo=timezone.utc)
    
    availability = await get_availability(
        service,
        start_time=start_time,
        end_time=end_time
    )
    
    # Should return working hours as free slots when no busy periods
    assert len(availability['free_slots']) > 0
    assert isinstance(availability['busy_periods'], list)


@pytest.mark.asyncio 
async def test_get_availability_working_hours_only():
    """Test that only working hours slots are returned, not 24/7."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    availability = await get_availability(service)
    
    # All free slots should be within working hours (9-17 by default)
    for slot in availability['free_slots']:
        start_time = _parse_datetime(slot['start'])
        end_time = _parse_datetime(slot['end'])
        
        # Check that slots are within working hours
        assert 9 <= start_time.hour < 17, f"Slot starts outside working hours: {slot}"
        assert 9 < end_time.hour <= 17, f"Slot ends outside working hours: {slot}"


@pytest.mark.asyncio
async def test_get_availability_default_date_range():
    """Test that default date range is today to next week."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    availability = await get_availability(service)
    
    # Parse the date range
    start_date = _parse_datetime(availability['date_range']['start'])
    end_date = _parse_datetime(availability['date_range']['end'])
    
    # Should be approximately 7 days difference (today to next week)
    date_diff = (end_date - start_date).days
    assert 6 <= date_diff <= 8, f"Expected ~7 days, got {date_diff} days"