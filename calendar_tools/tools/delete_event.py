"""
Google Calendar Delete Event Tool

Agent-friendly event deletion with simple parameters to support
agent frameworks that cannot handle complex nested structures.
"""

from typing import Dict, Any, Optional
from googleapiclient.errors import HttpError


async def delete_event(
    service,
    event_id: str,
    calendar_id: str = "primary",
    send_notifications: bool = True,
    force_delete: bool = False
) -> Dict[str, Any]:
    """
    Delete a Google Calendar event with agent-friendly parameters.
    
    Args:
        service: Authenticated Google Calendar API service
        event_id: The unique identifier of the event to delete
        calendar_id: Target calendar identifier (defaults to "primary")
        send_notifications: Whether to send deletion notifications to attendees
        force_delete: Whether to attempt deletion even if event might not exist
    
    Returns:
        Dict containing deletion status and details
    
    Raises:
        ValueError: For invalid parameters
        HttpError: For API-related errors (unless force_delete=True)
    """
    try:
        # Validate required parameters
        if not event_id:
            raise ValueError("event_id is required")
        
        if not calendar_id:
            raise ValueError("calendar_id is required")
        
        # Map boolean to Google API format
        send_updates = "all" if send_notifications else "none"
        
        # Delete the event via Google Calendar API
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates=send_updates
        ).execute()
        
        # Success - API returns no content (204)
        return {
            'success': True,
            'event_id': event_id,
            'calendar_id': calendar_id,
            'message': 'Event deleted successfully',
            'notifications_sent': send_notifications
        }
        
    except HttpError as e:
        error_code = e.resp.status
        
        if error_code == 404:
            error_msg = f"Event not found: {event_id}"
            if force_delete:
                # Return success for already-deleted events when force_delete=True
                return {
                    'success': True,
                    'event_id': event_id,
                    'calendar_id': calendar_id,
                    'message': 'Event already deleted or not found',
                    'notifications_sent': False,
                    'was_missing': True
                }
        elif error_code == 403:
            error_msg = f"Insufficient permissions to delete event: {event_id}"
        elif error_code == 410:
            error_msg = f"Event was already deleted: {event_id}"
            if force_delete:
                return {
                    'success': True,
                    'event_id': event_id,
                    'calendar_id': calendar_id,
                    'message': 'Event was already deleted',
                    'notifications_sent': False,
                    'was_missing': True
                }
        else:
            error_msg = f"Google Calendar API error: {e}"
        
        if force_delete and error_code in [404, 410]:
            # Don't raise exception for missing events when force_delete=True
            pass
        else:
            # Re-raise the original HttpError for other cases
            raise HttpError(e.resp, e.content, error_msg)
    
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Error deleting event: {str(e)}")