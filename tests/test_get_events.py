import pytest
from datetime import datetime, timezone, timedelta
from calendar_tools.tools.get_events import get_events
from calendar_tools.auth import create_service


@pytest.mark.asyncio
async def test_get_events_default_parameters():
    """Test get_events with default parameters (today to next week)."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    events = await get_events(service)
    
    # Verify response structure
    assert isinstance(events, dict)
    assert 'events' in events
    assert 'summary' in events
    assert 'calendar_id' in events
    assert 'date_range' in events
    
    # Verify events list structure
    assert isinstance(events['events'], list)
    
    # If there are events, verify their structure
    for event in events['events']:
        assert 'id' in event
        assert 'summary' in event
        assert 'start' in event
        assert 'end' in event


@pytest.mark.asyncio
async def test_get_events_single_event_by_id():
    """Test retrieving a single event by ID."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # First get some events to find a valid event ID
    all_events = await get_events(service)
    if not all_events['events']:
        pytest.skip("No events found to test single event retrieval")
    
    # Use the first event's ID
    test_event_id = all_events['events'][0]['id']
    
    # Retrieve single event
    single_event = await get_events(service, event_id=test_event_id)
    
    # Should return single event format
    assert 'id' in single_event
    assert 'summary' in single_event
    assert 'start' in single_event
    assert 'end' in single_event
    assert single_event['id'] == test_event_id


@pytest.mark.asyncio
async def test_get_events_custom_date_range():
    """Test get_events with custom date range."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    time_min = datetime(2024, 8, 26, 0, 0, 0, tzinfo=timezone.utc)
    time_max = datetime(2024, 8, 27, 23, 59, 59, tzinfo=timezone.utc)
    
    events = await get_events(
        service,
        time_min=time_min,
        time_max=time_max
    )
    
    # Verify date range is applied
    assert events['date_range']['start'] == time_min.isoformat()
    assert events['date_range']['end'] == time_max.isoformat()
    
    # Verify events are within date range (if any)
    for event in events['events']:
        if 'dateTime' in event['start']:
            event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            assert time_min <= event_start <= time_max


@pytest.mark.asyncio
async def test_get_events_with_text_query():
    """Test get_events with text search query."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    query = "meeting"  # Common search term
    
    events = await get_events(service, query=query)
    
    # Should return filtered results
    assert isinstance(events['events'], list)
    assert 'query' in events['summary']
    assert events['summary']['query'] == query


@pytest.mark.asyncio
async def test_get_events_max_results():
    """Test get_events with max_results parameter."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    max_results = 5
    
    events = await get_events(service, max_results=max_results)
    
    # Should respect max_results limit
    assert len(events['events']) <= max_results
    assert 'max_results' in events['summary']
    assert events['summary']['max_results'] == max_results


@pytest.mark.asyncio
async def test_get_events_multiple_calendars():
    """Test get_events with multiple calendar IDs."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    calendar_ids = ['primary']  # Start with primary for testing
    
    events = await get_events(service, calendar_ids=calendar_ids)
    
    # Should handle multiple calendars
    assert isinstance(events, dict)
    assert 'events' in events
    assert events['calendar_id'] in calendar_ids or events['calendar_id'] == 'multiple'


@pytest.mark.asyncio
async def test_get_events_order_by_start_time():
    """Test get_events with startTime ordering."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    events = await get_events(service, order_by='startTime')
    
    # Should be ordered by start time if multiple events
    if len(events['events']) > 1:
        prev_time = None
        for event in events['events']:
            if 'dateTime' in event['start']:
                current_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                if prev_time:
                    assert current_time >= prev_time
                prev_time = current_time


@pytest.mark.asyncio
async def test_get_events_show_deleted():
    """Test get_events with show_deleted parameter."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    events = await get_events(service, show_deleted=True)
    
    # Should include deleted events if any exist
    assert isinstance(events['events'], list)
    # Note: We can't easily verify deleted events without creating/deleting one


@pytest.mark.asyncio
async def test_get_events_timezone_handling():
    """Test get_events with custom timezone."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    events = await get_events(service, time_zone='US/Eastern')
    
    # Should handle timezone without errors
    assert isinstance(events['events'], list)


@pytest.mark.asyncio
async def test_get_events_invalid_event_id():
    """Test get_events with invalid event ID."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    invalid_id = "invalid_event_id_that_does_not_exist"
    
    # Should raise exception for invalid event ID
    with pytest.raises(Exception) as exc_info:
        await get_events(service, event_id=invalid_id)
    
    assert "not found" in str(exc_info.value).lower() or "404" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_events_invalid_date_range():
    """Test get_events with invalid date range (end before start)."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    time_min = datetime(2024, 8, 27, 0, 0, 0, tzinfo=timezone.utc)
    time_max = datetime(2024, 8, 26, 0, 0, 0, tzinfo=timezone.utc)  # Before start
    
    with pytest.raises(ValueError) as exc_info:
        await get_events(service, time_min=time_min, time_max=time_max)
    
    assert "time_max must be after time_min" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_events_response_format_consistency():
    """Test that get_events returns consistent format for both single and multiple events."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Get multiple events
    multiple_events = await get_events(service)
    
    if multiple_events['events']:
        # Get single event
        single_event_result = await get_events(service, event_id=multiple_events['events'][0]['id'])
        
        # Single event should have required fields
        required_fields = ['id', 'summary', 'start', 'end']
        for field in required_fields:
            assert field in single_event_result


@pytest.mark.asyncio
async def test_get_events_empty_calendar():
    """Test get_events when calendar has no events in date range."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    
    # Use far future date range likely to be empty
    time_min = datetime(2030, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    time_max = datetime(2030, 12, 2, 23, 59, 59, tzinfo=timezone.utc)
    
    events = await get_events(service, time_min=time_min, time_max=time_max)
    
    # Should return events list (may be empty or contain recurring events)
    assert isinstance(events['events'], list)
    # We can't guarantee empty results due to possible recurring events
    # But we can verify the structure is correct
    for event in events['events']:
        assert 'id' in event
        assert 'start' in event
        assert 'end' in event


@pytest.mark.asyncio
async def test_get_events_default_date_range():
    """Test that default date range is today to next week."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING not set")
    
    service = await create_service(email)
    events = await get_events(service)
    
    # Parse the date range
    start_date = datetime.fromisoformat(events['date_range']['start'])
    end_date = datetime.fromisoformat(events['date_range']['end'])
    
    # Should be approximately 7 days difference
    date_diff = (end_date - start_date).days
    assert 6 <= date_diff <= 8, f"Expected ~7 days, got {date_diff} days"