"""
Tests for create_event function using real Google Calendar API.
Following TDD approach - these tests should initially fail, then guide implementation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calendar_tools.auth import create_service
from calendar_tools.tools.create_event import create_event
from calendar_tools.tools.delete_event import delete_event


def get_test_service():
    """Helper function to get authenticated service for testing."""
    import os
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING environment variable not set")
    return email


async def create_and_cleanup_event(service, **kwargs):
    """Helper function to create event and return both result and cleanup function."""
    created_event = await create_event(service, **kwargs)
    
    async def cleanup():
        try:
            await delete_event(
                service,
                event_id=created_event['event_id'],
                send_notifications=False,  # Don't spam notifications during cleanup
                force_delete=True  # Handle already-deleted gracefully
            )
        except Exception:
            pass  # Ignore cleanup errors
    
    return created_event, cleanup


@pytest.fixture
def base_event_data():
    """Base event data for testing."""
    now = datetime.now()
    start_time = now + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)
    
    return {
        'calendar_id': 'primary',
        'summary': 'Test Event',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat()
    }


class TestCreateEventBasic:
    """Test basic event creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_basic_event_minimal_params(self, base_event_data):
        """Test creating event with only required parameters."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create event with cleanup helper
        result, cleanup = await create_and_cleanup_event(
            service,
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
            assert result['calendar_id'] == 'primary'
            assert result['summary'] == 'Test Event'
            assert 'start_time' in result
            assert 'end_time' in result
            assert 'html_link' in result
        finally:
            # Clean up the created event
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_description_and_location(self, base_event_data):
        """Test creating event with description and location."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            description="This is a test event description",
            location="123 Main St, Anytown, USA",
            **base_event_data
        )
        
        try:
            assert result['summary'] == 'Test Event'
            assert 'event_id' in result
            assert 'html_link' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_timezone(self, base_event_data):
        """Test creating event with explicit timezone."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            timezone="America/New_York",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
            assert result['calendar_id'] == 'primary'
        finally:
            await cleanup()


class TestCreateEventAttendees:
    """Test attendee-related functionality."""
    
    @pytest.mark.asyncio
    async def test_create_event_with_attendees(self, base_event_data):
        """Test creating event with attendees."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            attendees=["test1@example.com", "test2@example.com"],
            send_notifications="none",  # Don't spam test emails
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
            assert 'attendees_notified' in result or 'attendees' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_optional_attendees(self, base_event_data):
        """Test creating event with optional attendees."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            attendees=["required@example.com"],
            optional_attendees=["optional@example.com"],
            send_notifications="none",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_guest_permissions(self, base_event_data):
        """Test creating event with guest permission settings."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            attendees=["guest@example.com"],
            guests_can_invite_others=False,
            guests_can_modify=True,
            guests_can_see_others=False,
            send_notifications="none",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()


class TestCreateEventGoogleMeet:
    """Test Google Meet integration."""
    
    @pytest.mark.asyncio
    async def test_create_event_with_google_meet(self, base_event_data):
        """Test creating event with Google Meet link."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create Google Meet event with cleanup
        result, cleanup = await create_and_cleanup_event(
            service,
            create_google_meet=True,
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
            assert 'google_meet_link' in result or 'conference_link' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_google_meet_and_location(self, base_event_data):
        """Test creating event with both Google Meet and physical location."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            create_google_meet=True,
            location="Conference Room A",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
            assert 'google_meet_link' in result or 'conference_link' in result
        finally:
            await cleanup()


class TestCreateEventAllDay:
    """Test all-day event functionality."""
    
    @pytest.mark.asyncio
    async def test_create_all_day_event(self):
        """Test creating an all-day event."""
        email = get_test_service()
        service = await create_service(email)
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            calendar_id='primary',
            summary='All Day Test Event',
            start_time=tomorrow.isoformat(),
            end_time=day_after.isoformat(),
            all_day=True
        )
        
        try:
            assert 'event_id' in result
            assert result['summary'] == 'All Day Test Event'
        finally:
            await cleanup()


class TestCreateEventRecurrence:
    """Test recurring event functionality."""
    
    @pytest.mark.asyncio
    async def test_create_recurring_event_weekly(self, base_event_data):
        """Test creating a weekly recurring event."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            recurrence_rule="FREQ=WEEKLY;COUNT=5",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_recurring_event_daily(self, base_event_data):
        """Test creating a daily recurring event."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            recurrence_rule="FREQ=DAILY;COUNT=3",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()


class TestCreateEventReminders:
    """Test reminder functionality."""
    
    @pytest.mark.asyncio
    async def test_create_event_with_email_reminder(self, base_event_data):
        """Test creating event with email reminder."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            email_reminder_minutes=60,
            use_default_reminders=False,
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_popup_reminder(self, base_event_data):
        """Test creating event with popup reminder."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            popup_reminder_minutes=15,
            use_default_reminders=False,
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_multiple_reminders(self, base_event_data):
        """Test creating event with both email and popup reminders."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            email_reminder_minutes=1440,  # 24 hours
            popup_reminder_minutes=15,
            use_default_reminders=False,
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()


class TestCreateEventProperties:
    """Test event properties and metadata."""
    
    @pytest.mark.asyncio
    async def test_create_event_with_visibility_private(self, base_event_data):
        """Test creating private event."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            visibility="private",
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()
    
    @pytest.mark.asyncio
    async def test_create_event_with_color(self, base_event_data):
        """Test creating event with custom color."""
        email = get_test_service()
        service = await create_service(email)
        
        result, cleanup = await create_and_cleanup_event(
            service,
            color_id=5,  # Valid color ID
            **base_event_data
        )
        
        try:
            assert 'event_id' in result
        finally:
            await cleanup()


class TestCreateEventValidation:
    """Test parameter validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_calendar_id(self, base_event_data):
        """Test creating event with invalid calendar ID."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(Exception):  # Should raise HttpError or ValueError
            await create_event(
                service,
                calendar_id="invalid_calendar_id_12345",
                **base_event_data
            )
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_time_format(self):
        """Test creating event with invalid datetime format."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(ValueError):
            await create_event(
                service,
                calendar_id='primary',
                summary='Invalid Time Test',
                start_time="invalid-datetime",
                end_time="also-invalid"
            )
    
    @pytest.mark.asyncio
    async def test_create_event_end_before_start(self):
        """Test creating event where end time is before start time."""
        email = get_test_service()
        service = await create_service(email)
        
        now = datetime.now()
        start_time = now + timedelta(hours=2)
        end_time = now + timedelta(hours=1)  # Before start time
        
        with pytest.raises(ValueError):
            await create_event(
                service,
                calendar_id='primary',
                summary='Invalid Time Range Test',
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_color_id(self, base_event_data):
        """Test creating event with invalid color ID."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(ValueError):
            await create_event(
                service,
                color_id=99,  # Invalid color ID
                **base_event_data
            )
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_send_notifications(self, base_event_data):
        """Test creating event with invalid send_notifications value."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(ValueError):
            await create_event(
                service,
                send_notifications="invalid_option",
                **base_event_data
            )


class TestCreateEventDifferentCalendars:
    """Test creating events in different calendars."""
    
    @pytest.mark.asyncio
    async def test_create_event_in_primary_calendar(self, base_event_data):
        """Test creating event in primary calendar explicitly."""
        email = get_test_service()
        service = await create_service(email)
        
        # Remove calendar_id from base_event_data to avoid conflict
        event_data = base_event_data.copy()
        event_data['calendar_id'] = 'primary'
        
        result, cleanup = await create_and_cleanup_event(
            service,
            **event_data
        )
        
        try:
            assert 'event_id' in result
            assert result['calendar_id'] == 'primary'
        finally:
            await cleanup()