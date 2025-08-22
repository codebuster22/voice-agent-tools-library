import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime, timedelta, timezone
from calendar_tools.auth import create_service
from calendar_tools.tools.create_event import create_event
from calendar_tools.tools.delete_event import delete_event
from calendar_tools.tools.update_event import update_event


class TestUpdateEvent:
    """Comprehensive tests for update_event function using real Google Calendar API."""
    
    @pytest.fixture(scope="class")
    def event_loop(self):
        """Create event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest_asyncio.fixture(scope="class")
    async def service(self):
        """Create authenticated Google Calendar service."""
        email = os.getenv('EMAIL_FOR_TESTING')
        service = await create_service(email)
        return service
    
    @pytest.fixture(scope="class")
    def calendar_id(self):
        """Use primary calendar for tests."""
        return "primary"
    
    async def create_and_cleanup_event(self, service, calendar_id, **event_params):
        """Helper to create event for testing and ensure cleanup."""
        default_params = {
            'summary': 'Test Event for Update',
            'description': 'Original description',
            'location': 'Original Location',
            'start_time': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            'end_time': (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            'send_notifications': 'none'
        }
        default_params.update(event_params)
        
        event_data = await create_event(service, calendar_id, **default_params)
        event_id = event_data['event_id']
        
        try:
            yield event_id, event_data
        finally:
            # Cleanup: delete the event
            try:
                await delete_event(service, event_id, calendar_id, 
                                 send_notifications='none', force_delete=True)
            except Exception:
                pass  # Silent cleanup
    
    @pytest.mark.asyncio
    async def test_update_basic_fields(self, service, calendar_id):
        """Test updating basic event fields (summary, description, location)."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                summary='Updated Summary',
                description='Updated description',
                location='Updated Location'
            )
            
            assert result['event_id'] == event_id
            assert result['calendar_id'] == calendar_id
            assert result['summary'] == 'Updated Summary'
            assert 'summary' in result['updated_fields']
            assert 'description' in result['updated_fields']
            assert 'location' in result['updated_fields']
            assert 'html_link' in result
    
    @pytest.mark.asyncio
    async def test_update_single_field(self, service, calendar_id):
        """Test updating only one field leaves others unchanged."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            summary='Original Title',
            description='Original Desc'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                summary='Only Title Changed'
            )
            
            assert result['summary'] == 'Only Title Changed'
            assert result['updated_fields'] == ['summary']
            assert len(result['updated_fields']) == 1
    
    @pytest.mark.asyncio
    async def test_update_time_fields(self, service, calendar_id):
        """Test updating event start and end times."""
        new_start = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        new_end = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
        
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                start_time=new_start,
                end_time=new_end
            )
            
            # Times may be converted by Google Calendar, just check they're updated
            assert 'start_time' in result
            assert 'end_time' in result
            assert 'start_time' in result['updated_fields']
            assert 'end_time' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_update_attendees_replace(self, service, calendar_id):
        """Test replacing attendees list."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            attendees=['test1@example.com'],
            send_notifications='none'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                attendees=['test2@example.com', 'test3@example.com'],
                attendee_action='replace',
                send_notifications='none'
            )
            
            assert 'attendees' in result['updated_fields']
            # Verify attendees were updated (not necessarily that notifications were sent)
            assert 'attendees_notified' in result
            assert 'test2@example.com' in result['attendees_notified']
            assert 'test3@example.com' in result['attendees_notified']
    
    @pytest.mark.asyncio
    async def test_update_attendees_add(self, service, calendar_id):
        """Test adding attendees to existing list."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            attendees=['existing@example.com'],
            send_notifications='none'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                attendees=['new@example.com'],
                attendee_action='add',
                send_notifications='none'
            )
            
            assert 'attendees' in result['updated_fields']
            assert result['attendee_action'] == 'add'
    
    @pytest.mark.asyncio
    async def test_update_attendees_remove(self, service, calendar_id):
        """Test removing specific attendees."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            attendees=['keep@example.com', 'remove@example.com'],
            send_notifications='none'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                attendees=['remove@example.com'],
                attendee_action='remove',
                send_notifications='none'
            )
            
            assert 'attendees' in result['updated_fields']
            assert result['attendee_action'] == 'remove'
    
    @pytest.mark.asyncio
    async def test_add_google_meet(self, service, calendar_id):
        """Test adding Google Meet to existing event."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                create_google_meet=True
            )
            
            assert 'google_meet_link' in result
            assert result['google_meet_link'].startswith('https://meet.google.com/')
            assert 'conference_data' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_remove_google_meet(self, service, calendar_id):
        """Test removing Google Meet from existing event."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            create_google_meet=True
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                remove_google_meet=True
            )
            
            assert result.get('google_meet_link') is None
            assert 'conference_data' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_update_visibility_and_color(self, service, calendar_id):
        """Test updating event visibility and color."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                visibility='private',
                color_id=5
            )
            
            assert result['visibility'] == 'private'
            assert result['color_id'] == 5
            assert 'visibility' in result['updated_fields']
            assert 'color_id' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_update_status(self, service, calendar_id):
        """Test updating event status."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                status='tentative'
            )
            
            assert result['status'] == 'tentative'
            assert 'status' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_update_reminders(self, service, calendar_id):
        """Test updating event reminders."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                email_reminder_minutes=60,
                popup_reminder_minutes=15
            )
            
            assert 'reminders' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_clear_all_reminders(self, service, calendar_id):
        """Test clearing all event reminders."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            email_reminder_minutes=30,
            popup_reminder_minutes=10
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                clear_all_reminders=True
            )
            
            assert 'reminders' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_invalid_event_id(self, service, calendar_id):
        """Test error handling for invalid event ID."""
        with pytest.raises(Exception) as exc_info:
            await update_event(
                service,
                event_id='invalid_event_id',
                calendar_id=calendar_id,
                summary='Should Fail'
            )
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_calendar_id(self, service):
        """Test error handling for invalid calendar ID."""
        with pytest.raises(Exception) as exc_info:
            await update_event(
                service,
                event_id='any_event_id',
                calendar_id='invalid_calendar_id',
                summary='Should Fail'
            )
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_conflicting_google_meet_params(self, service, calendar_id):
        """Test error handling for conflicting Google Meet parameters."""
        with pytest.raises(ValueError) as exc_info:
            await update_event(
                service,
                event_id='any_id',
                calendar_id=calendar_id,
                create_google_meet=True,
                remove_google_meet=True
            )
        
        assert "cannot both create and remove" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_attendee_action(self, service, calendar_id):
        """Test error handling for invalid attendee_action."""
        with pytest.raises(ValueError) as exc_info:
            await update_event(
                service,
                event_id='any_id',
                calendar_id=calendar_id,
                attendees=['test@example.com'],
                attendee_action='invalid_action'
            )
        
        assert "invalid attendee_action" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_color_id(self, service, calendar_id):
        """Test error handling for invalid color_id."""
        with pytest.raises(ValueError) as exc_info:
            await update_event(
                service,
                event_id='any_id',
                calendar_id=calendar_id,
                color_id=99  # Invalid range
            )
        
        assert "color_id must be between 1 and 24" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_no_updates_provided(self, service, calendar_id):
        """Test handling when no update fields are provided."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id
            )
            
            assert result['event_id'] == event_id
            assert result['updated_fields'] == []
            assert result['summary'] == original_event['summary']  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_recurring_event_single_update(self, service, calendar_id):
        """Test updating single instance of recurring event."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            recurrence_rule='FREQ=DAILY;COUNT=3'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                summary='Updated Single Instance',
                recurring_update_scope='single'
            )
            
            assert result['summary'] == 'Updated Single Instance'
            assert result['recurring_update_scope'] == 'single'
            assert 'summary' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_add_recurrence_to_single_event(self, service, calendar_id):
        """Test adding recurrence to a single event."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                recurrence_rule='FREQ=WEEKLY;COUNT=4'
            )
            
            assert 'recurrence' in result['updated_fields']
    
    @pytest.mark.asyncio
    async def test_remove_recurrence(self, service, calendar_id):
        """Test removing recurrence from recurring event."""
        async for event_id, original_event in self.create_and_cleanup_event(
            service, calendar_id,
            recurrence_rule='FREQ=DAILY;COUNT=3'
        ):
            result = await update_event(
                service,
                event_id=event_id,
                calendar_id=calendar_id,
                remove_recurrence=True
            )
            
            assert 'recurrence' in result['updated_fields']