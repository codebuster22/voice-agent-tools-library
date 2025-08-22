"""
Tests for delete_event function using real Google Calendar API.
Following TDD approach - these tests should initially fail, then guide implementation.
"""

import pytest
import pytest_asyncio
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
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING environment variable not set")
    return email


@pytest_asyncio.fixture
async def test_event():
    """Create a test event that can be deleted."""
    email = get_test_service()
    service = await create_service(email)
    
    # Create a test event in the future
    now = datetime.now()
    start_time = now + timedelta(hours=24)  # Tomorrow
    end_time = start_time + timedelta(hours=1)
    
    created_event = await create_event(
        service,
        calendar_id='primary',
        summary='Test Event for Deletion',
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        description='This event will be deleted by tests'
    )
    
    return {
        'service': service,
        'event_id': created_event['event_id'],
        'calendar_id': 'primary'
    }


class TestDeleteEventBasic:
    """Test basic event deletion functionality."""
    
    @pytest.mark.asyncio
    async def test_delete_event_success(self, test_event):
        """Test successfully deleting an event."""
        result = await delete_event(
            test_event['service'],
            event_id=test_event['event_id'],
            calendar_id=test_event['calendar_id']
        )
        
        assert result['success'] is True
        assert result['event_id'] == test_event['event_id']
        assert result['calendar_id'] == test_event['calendar_id']
        assert result['message'] == 'Event deleted successfully'
        assert result['notifications_sent'] is True
    
    @pytest.mark.asyncio
    async def test_delete_event_no_notifications(self, test_event):
        """Test deleting event without sending notifications."""
        result = await delete_event(
            test_event['service'],
            event_id=test_event['event_id'],
            send_notifications=False
        )
        
        assert result['success'] is True
        assert result['notifications_sent'] is False
    
    @pytest.mark.asyncio
    async def test_delete_event_default_calendar(self):
        """Test deleting event using default primary calendar."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create event to delete
        now = datetime.now()
        start_time = now + timedelta(hours=25)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Default Calendar Delete',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat()
        )
        
        # Delete using default calendar (should use "primary")
        result = await delete_event(
            service,
            event_id=created_event['event_id']
            # calendar_id defaults to "primary"
        )
        
        assert result['success'] is True
        assert result['calendar_id'] == 'primary'


class TestDeleteEventErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_event(self):
        """Test deleting an event that doesn't exist."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(Exception):  # Should raise HttpError with 404
            await delete_event(
                service,
                event_id="nonexistent_event_id_12345"
            )
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_event_force(self):
        """Test deleting nonexistent event with force_delete=True."""
        email = get_test_service()
        service = await create_service(email)
        
        result = await delete_event(
            service,
            event_id="nonexistent_event_id_12345",
            force_delete=True
        )
        
        assert result['success'] is True
        assert result['was_missing'] is True
        assert result['message'] == 'Event already deleted or not found'
        assert result['notifications_sent'] is False
    
    @pytest.mark.asyncio
    async def test_delete_already_deleted_event_force(self, test_event):
        """Test deleting an event twice with force_delete."""
        # First deletion
        result1 = await delete_event(
            test_event['service'],
            event_id=test_event['event_id']
        )
        assert result1['success'] is True
        
        # Second deletion with force_delete=True should succeed
        result2 = await delete_event(
            test_event['service'],
            event_id=test_event['event_id'],
            force_delete=True
        )
        
        assert result2['success'] is True
        assert result2['was_missing'] is True
    
    @pytest.mark.asyncio
    async def test_delete_invalid_calendar_id(self):
        """Test deleting event with invalid calendar ID."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(Exception):  # Should raise HttpError
            await delete_event(
                service,
                event_id="some_event_id",
                calendar_id="invalid_calendar_id_12345"
            )
    
    @pytest.mark.asyncio
    async def test_delete_empty_event_id(self):
        """Test validation with empty event ID."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(ValueError) as exc_info:
            await delete_event(
                service,
                event_id=""
            )
        
        assert "event_id is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_empty_calendar_id(self):
        """Test validation with empty calendar ID."""
        email = get_test_service()
        service = await create_service(email)
        
        with pytest.raises(ValueError) as exc_info:
            await delete_event(
                service,
                event_id="some_event_id",
                calendar_id=""
            )
        
        assert "calendar_id is required" in str(exc_info.value)


class TestDeleteEventWithAttendees:
    """Test deletion of events with attendees."""
    
    @pytest.mark.asyncio
    async def test_delete_event_with_attendees_notify(self):
        """Test deleting event with attendees and sending notifications."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create event with attendees
        now = datetime.now()
        start_time = now + timedelta(hours=26)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Event with Attendees',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat(),
            attendees=['test1@example.com', 'test2@example.com'],
            send_notifications='none'  # Don't spam during creation
        )
        
        # Delete with notifications
        result = await delete_event(
            service,
            event_id=created_event['event_id'],
            send_notifications=True
        )
        
        assert result['success'] is True
        assert result['notifications_sent'] is True
    
    @pytest.mark.asyncio
    async def test_delete_event_with_attendees_no_notify(self):
        """Test deleting event with attendees without notifications."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create event with attendees
        now = datetime.now()
        start_time = now + timedelta(hours=27)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Event with Attendees No Notify',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat(),
            attendees=['test3@example.com'],
            send_notifications='none'
        )
        
        # Delete without notifications
        result = await delete_event(
            service,
            event_id=created_event['event_id'],
            send_notifications=False
        )
        
        assert result['success'] is True
        assert result['notifications_sent'] is False


class TestDeleteRecurringEvents:
    """Test deletion of recurring events."""
    
    @pytest.mark.asyncio
    async def test_delete_recurring_event_series(self):
        """Test deleting an entire recurring event series."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create recurring event
        now = datetime.now()
        start_time = now + timedelta(hours=28)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Recurring Event Series',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat(),
            recurrence_rule='FREQ=WEEKLY;COUNT=3'
        )
        
        # Delete the entire series
        result = await delete_event(
            service,
            event_id=created_event['event_id']
        )
        
        assert result['success'] is True


class TestDeleteSpecialEvents:
    """Test deletion of special event types."""
    
    @pytest.mark.asyncio
    async def test_delete_all_day_event(self):
        """Test deleting an all-day event."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create all-day event
        tomorrow = (datetime.now() + timedelta(days=2)).date()
        day_after = tomorrow + timedelta(days=1)
        
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test All Day Event Delete',
            start_time=tomorrow.isoformat(),
            end_time=day_after.isoformat(),
            all_day=True
        )
        
        # Delete the all-day event
        result = await delete_event(
            service,
            event_id=created_event['event_id']
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_delete_google_meet_event(self):
        """Test deleting event with Google Meet."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create Google Meet event
        now = datetime.now()
        start_time = now + timedelta(hours=29)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Google Meet Event Delete',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat(),
            create_google_meet=True
        )
        
        # Delete the Google Meet event
        result = await delete_event(
            service,
            event_id=created_event['event_id']
        )
        
        assert result['success'] is True


class TestIntegratedCreateDelete:
    """Test create-then-delete workflow for clean testing."""
    
    @pytest.mark.asyncio
    async def test_create_and_delete_workflow(self):
        """Test complete create-then-delete workflow."""
        email = get_test_service()
        service = await create_service(email)
        
        # Create event
        now = datetime.now()
        start_time = now + timedelta(hours=30)
        created_event = await create_event(
            service,
            calendar_id='primary',
            summary='Test Create-Delete Workflow',
            start_time=start_time.isoformat(),
            end_time=(start_time + timedelta(hours=1)).isoformat(),
            description='This event tests the complete workflow'
        )
        
        # Verify event was created
        assert 'event_id' in created_event
        event_id = created_event['event_id']
        
        # Delete the event
        delete_result = await delete_event(
            service,
            event_id=event_id
        )
        
        # Verify deletion was successful
        assert delete_result['success'] is True
        assert delete_result['event_id'] == event_id
        
        # Verify event is actually deleted (second delete should fail unless force=True)
        delete_result2 = await delete_event(
            service,
            event_id=event_id,
            force_delete=True
        )
        
        assert delete_result2['success'] is True
        assert delete_result2['was_missing'] is True
    
    @pytest.mark.asyncio 
    async def test_batch_create_delete(self):
        """Test creating and deleting multiple events."""
        email = get_test_service()
        service = await create_service(email)
        
        created_events = []
        
        # Create multiple test events
        for i in range(3):
            now = datetime.now()
            start_time = now + timedelta(hours=31 + i)
            
            created_event = await create_event(
                service,
                calendar_id='primary',
                summary=f'Batch Test Event {i+1}',
                start_time=start_time.isoformat(),
                end_time=(start_time + timedelta(hours=1)).isoformat()
            )
            created_events.append(created_event['event_id'])
        
        # Delete all created events
        for event_id in created_events:
            result = await delete_event(
                service,
                event_id=event_id,
                send_notifications=False  # Don't spam notifications
            )
            assert result['success'] is True