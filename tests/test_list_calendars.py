import pytest
from unittest.mock import Mock, AsyncMock, patch
from calendar_tools.tools.list_calendars import list_calendars


@pytest.fixture
def mock_service():
    """Create a mock Google Calendar service."""
    service = Mock()
    calendar_list = Mock()
    list_request = Mock()
    
    service.calendarList.return_value = calendar_list
    calendar_list.list.return_value = list_request
    list_request.execute.return_value = {
        "kind": "calendar#calendarList",
        "items": [
            {
                "id": "primary",
                "summary": "Primary Calendar",
                "accessRole": "owner",
                "primary": True,
                "timeZone": "America/New_York",
                "description": "Main personal calendar"
            },
            {
                "id": "team@example.com",
                "summary": "Team Calendar", 
                "accessRole": "reader",
                "timeZone": "America/New_York",
                "description": "Shared team events"
            },
            {
                "id": "work@company.com",
                "summary": "Work Calendar",
                "accessRole": "writer", 
                "timeZone": "America/Los_Angeles"
            }
        ]
    }
    
    return service


@pytest.mark.asyncio
async def test_list_calendars_success(mock_service):
    """Test successful calendar listing."""
    calendars = await list_calendars(mock_service)
    
    # Verify we get the expected number of calendars
    assert len(calendars) == 3
    
    # Verify first calendar (primary)
    primary_cal = calendars[0]
    assert primary_cal["calendarId"] == "primary"
    assert primary_cal["calendarName"] == "Primary Calendar"
    assert primary_cal["description"] == "Main personal calendar"
    
    # Verify second calendar (team)
    team_cal = calendars[1]
    assert team_cal["calendarId"] == "team@example.com"
    assert team_cal["calendarName"] == "Team Calendar"
    assert team_cal["description"] == "Shared team events"
    
    # Verify third calendar (work)
    work_cal = calendars[2]
    assert work_cal["calendarId"] == "work@company.com"
    assert work_cal["calendarName"] == "Work Calendar"
    assert work_cal["description"] == ""
    
    # Verify service was called correctly
    mock_service.calendarList.assert_called_once()
    mock_service.calendarList().list.assert_called_once()


@pytest.mark.asyncio
async def test_list_calendars_with_parameters(mock_service):
    """Test calendar listing with optional parameters."""
    await list_calendars(mock_service, max_results=50, show_hidden=True)
    
    # Verify parameters were passed correctly
    mock_service.calendarList().list.assert_called_once_with(
        maxResults=50,
        showHidden=True
    )


@pytest.mark.asyncio
async def test_list_calendars_empty_response(mock_service):
    """Test handling of empty calendar list."""
    # Mock empty response
    mock_service.calendarList().list().execute.return_value = {
        "kind": "calendar#calendarList",
        "items": []
    }
    
    calendars = await list_calendars(mock_service)
    assert calendars == []


@pytest.mark.asyncio
async def test_list_calendars_missing_items_key(mock_service):
    """Test handling of response without 'items' key."""
    # Mock response without items
    mock_service.calendarList().list().execute.return_value = {
        "kind": "calendar#calendarList"
    }
    
    calendars = await list_calendars(mock_service)
    assert calendars == []


@pytest.mark.asyncio
async def test_list_calendars_api_error(mock_service):
    """Test handling of Google API errors."""
    from googleapiclient.errors import HttpError
    
    # Mock API error
    mock_service.calendarList().list().execute.side_effect = HttpError(
        resp=Mock(status=403),
        content=b'{"error": {"code": 403, "message": "Forbidden"}}'
    )
    
    with pytest.raises(Exception) as exc_info:
        await list_calendars(mock_service)
    
    assert "Failed to list calendars" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_calendars_network_error(mock_service):
    """Test handling of network connectivity errors."""
    # Mock network error
    mock_service.calendarList().list().execute.side_effect = ConnectionError("Network unreachable")
    
    with pytest.raises(Exception) as exc_info:
        await list_calendars(mock_service)
    
    assert "Failed to list calendars" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_calendars_filters_required_fields():
    """Test that function returns only required calendar fields."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "cal1@test.com",
                "summary": "Test Calendar",
                "accessRole": "owner",
                "timeZone": "UTC",
                "description": "Test description",
                "etag": "some-etag",
                "kind": "calendar#calendarListEntry",
                "colorId": "1",
                "backgroundColor": "#ac725e"
            }
        ]
    }
    
    calendars = await list_calendars(service)
    calendar = calendars[0]
    
    # Should contain core fields with simplified names
    assert "calendarId" in calendar
    assert "calendarName" in calendar  
    assert "description" in calendar
    
    # Should NOT contain raw API fields (they're filtered out)
    assert "timeZone" not in calendar
    assert "accessRole" not in calendar
    assert "etag" not in calendar


@pytest.mark.asyncio
async def test_list_calendars_regex_filter_include():
    """Test regex filtering to include matching calendars."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "primary",
                "summary": "Primary Calendar",
                "accessRole": "owner",
                "description": "Main calendar"
            },
            {
                "id": "team@example.com",
                "summary": "Team Calendar",
                "accessRole": "reader",
                "description": "Shared team events"
            },
            {
                "id": "transferred@example.com",
                "summary": "Transferred from old.user@example.com",
                "accessRole": "owner",
                "description": "Old calendar data"
            }
        ]
    }
    
    # Filter to include only calendars with "team" in them
    calendars = await list_calendars(
        service, 
        query_strings=["team"],
        query_string_to_include=True
    )
    
    assert len(calendars) == 1
    assert calendars[0]["calendarName"] == "Team Calendar"


@pytest.mark.asyncio
async def test_list_calendars_regex_filter_exclude():
    """Test regex filtering to exclude matching calendars."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "primary",
                "summary": "Primary Calendar",
                "accessRole": "owner",
                "description": "Main calendar"
            },
            {
                "id": "team@example.com",
                "summary": "Team Calendar",
                "accessRole": "reader",
                "description": "Shared team events"
            },
            {
                "id": "transferred@example.com",
                "summary": "Transferred from old.user@example.com",
                "accessRole": "owner",
                "description": "Old calendar data"
            }
        ]
    }
    
    # Filter to exclude calendars with "transferred from" in them
    calendars = await list_calendars(
        service, 
        query_strings=["transferred from"],
        query_string_to_include=False
    )
    
    assert len(calendars) == 2
    assert all("Transferred from" not in cal["calendarName"] for cal in calendars)
    assert any(cal["calendarName"] == "Primary Calendar" for cal in calendars)
    assert any(cal["calendarName"] == "Team Calendar" for cal in calendars)


@pytest.mark.asyncio
async def test_list_calendars_multiple_regex_patterns():
    """Test filtering with multiple regex patterns."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "primary",
                "summary": "Primary Calendar",
                "accessRole": "owner",
                "description": "Main calendar"
            },
            {
                "id": "work@company.com",
                "summary": "Work Calendar",
                "accessRole": "reader",
                "description": "Work related events"
            },
            {
                "id": "personal@gmail.com",
                "summary": "Personal Events",
                "accessRole": "owner",
                "description": "Personal calendar"
            },
            {
                "id": "holidays@group.calendar.google.com",
                "summary": "Holidays in US",
                "accessRole": "reader",
                "description": "Holiday calendar"
            }
        ]
    }
    
    # Include calendars matching either "work" or "personal"
    calendars = await list_calendars(
        service, 
        query_strings=["work", "personal"],
        query_string_to_include=True
    )
    
    assert len(calendars) == 2
    summaries = [cal["calendarName"] for cal in calendars]
    assert "Work Calendar" in summaries
    assert "Personal Events" in summaries


@pytest.mark.asyncio
async def test_list_calendars_regex_case_insensitive():
    """Test that regex filtering is case insensitive."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "test@example.com",
                "summary": "TEAM CALENDAR",
                "accessRole": "reader",
                "description": "Team Events"
            },
            {
                "id": "other@example.com",
                "summary": "Other Calendar",
                "accessRole": "owner",
                "description": "Other events"
            }
        ]
    }
    
    # Search for "team" (lowercase) should match "TEAM CALENDAR" (uppercase)
    calendars = await list_calendars(
        service, 
        query_strings=["team"],
        query_string_to_include=True
    )
    
    assert len(calendars) == 1
    assert calendars[0]["calendarName"] == "TEAM CALENDAR"


@pytest.mark.asyncio
async def test_list_calendars_regex_searches_all_fields():
    """Test that regex filtering searches summary, description, and id."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {
                "id": "special@example.com",
                "summary": "Normal Calendar",
                "accessRole": "owner",
                "description": "Regular events"
            },
            {
                "id": "regular@example.com",
                "summary": "Another Calendar",
                "accessRole": "reader",
                "description": "Contains special keyword"
            },
            {
                "id": "other@example.com",
                "summary": "Third Calendar",
                "accessRole": "owner",
                "description": "Nothing here"
            }
        ]
    }
    
    # Search for "special" - should match both ID and description
    calendars = await list_calendars(
        service, 
        query_strings=["special"],
        query_string_to_include=True
    )
    
    assert len(calendars) == 2
    ids = [cal["calendarId"] for cal in calendars]
    assert "special@example.com" in ids
    assert "regular@example.com" in ids


@pytest.mark.asyncio
async def test_list_calendars_no_query_strings():
    """Test that no filtering is applied when query_strings is None."""
    service = Mock()
    service.calendarList().list().execute.return_value = {
        "items": [
            {"id": "cal1", "summary": "Calendar 1", "accessRole": "owner"},
            {"id": "cal2", "summary": "Calendar 2", "accessRole": "reader"}
        ]
    }
    
    # Should return all calendars when no query_strings provided
    calendars = await list_calendars(service, query_strings=None)
    
    assert len(calendars) == 2