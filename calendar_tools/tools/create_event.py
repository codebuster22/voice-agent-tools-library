"""
Google Calendar Create Event Tool

Agent-friendly event creation with flattened parameters to support
agent frameworks that cannot handle complex nested structures.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import uuid
from googleapiclient.errors import HttpError


async def create_event(
    service,
    calendar_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: Optional[str] = None,
    all_day: bool = False,
    attendees: Optional[List[str]] = None,
    optional_attendees: Optional[List[str]] = None,
    create_google_meet: bool = False,
    send_notifications: str = "all",
    guests_can_invite_others: bool = True,
    guests_can_modify: bool = False,
    guests_can_see_others: bool = True,
    visibility: str = "default",
    color_id: Optional[int] = None,
    recurrence_rule: Optional[str] = None,
    email_reminder_minutes: Optional[int] = None,
    popup_reminder_minutes: Optional[int] = None,
    use_default_reminders: bool = True
) -> Dict[str, Any]:
    """
    Create a new Google Calendar event with agent-friendly parameters.
    
    Args:
        service: Authenticated Google Calendar API service
        calendar_id: Target calendar identifier
        summary: Event title/name
        start_time: Event start datetime in ISO format
        end_time: Event end datetime in ISO format
        description: Event description/details
        location: Physical address, Google Meet, or map link
        timezone: Default timezone for event (e.g., "America/New_York")
        all_day: Boolean flag for all-day events
        attendees: List of attendee email addresses
        optional_attendees: List of optional attendee emails
        create_google_meet: Auto-create Google Meet link
        send_notifications: Send invitations ("all"/"external"/"none")
        guests_can_invite_others: Allow attendees to invite others
        guests_can_modify: Allow attendees to modify event
        guests_can_see_others: Allow attendees to see other guests
        visibility: Privacy level ("default"/"public"/"private"/"confidential")
        color_id: Event color ID 1-24
        recurrence_rule: RRULE string for recurring events
        email_reminder_minutes: Email reminder before event in minutes
        popup_reminder_minutes: Popup reminder before event in minutes
        use_default_reminders: Use calendar's default reminders
    
    Returns:
        Dict containing created event details
    
    Raises:
        ValueError: For invalid parameters
        HttpError: For API-related errors
    """
    try:
        # Validate required parameters
        if not calendar_id or not summary or not start_time or not end_time:
            raise ValueError("calendar_id, summary, start_time, and end_time are required")
        
        # Validate send_notifications parameter
        if send_notifications not in ["all", "external", "none"]:
            raise ValueError("send_notifications must be 'all', 'external', or 'none'")
        
        # Validate visibility parameter
        if visibility not in ["default", "public", "private", "confidential"]:
            raise ValueError("visibility must be 'default', 'public', 'private', or 'confidential'")
        
        # Validate color_id if provided
        if color_id is not None and (color_id < 1 or color_id > 24):
            raise ValueError("color_id must be between 1 and 24")
        
        # Parse and validate datetime strings
        try:
            if all_day:
                # For all-day events, expect date format (YYYY-MM-DD)
                parsed_start = datetime.fromisoformat(start_time).date()
                parsed_end = datetime.fromisoformat(end_time).date()
            else:
                # For timed events, expect datetime format
                parsed_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                parsed_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {e}")
        
        # Validate end time is after start time
        if not all_day and parsed_end <= parsed_start:
            raise ValueError("End time must be after start time")
        elif all_day and parsed_end <= parsed_start:
            raise ValueError("End date must be after start date")
        
        # Build the event object
        event = {
            'summary': summary,
            'start': {},
            'end': {}
        }
        
        # Set start and end times
        if all_day:
            event['start']['date'] = start_time
            event['end']['date'] = end_time
        else:
            event['start']['dateTime'] = start_time
            event['end']['dateTime'] = end_time
            
            # Add timezone - use provided timezone or default to UTC
            effective_timezone = timezone or "UTC"
            event['start']['timeZone'] = effective_timezone
            event['end']['timeZone'] = effective_timezone
        
        # Add optional fields
        if description:
            event['description'] = description
        
        if location:
            event['location'] = location
        
        if visibility != "default":
            event['visibility'] = visibility
        
        if color_id:
            event['colorId'] = str(color_id)
        
        # Handle recurrence
        if recurrence_rule:
            event['recurrence'] = [f"RRULE:{recurrence_rule}"]
        
        # Handle attendees
        if attendees or optional_attendees:
            event['attendees'] = []
            
            if attendees:
                for email in attendees:
                    event['attendees'].append({
                        'email': email,
                        'optional': False,
                        'responseStatus': 'needsAction'
                    })
            
            if optional_attendees:
                for email in optional_attendees:
                    event['attendees'].append({
                        'email': email,
                        'optional': True,
                        'responseStatus': 'needsAction'
                    })
            
            # Set guest permissions
            event['guestsCanInviteOthers'] = guests_can_invite_others
            event['guestsCanModify'] = guests_can_modify
            event['guestsCanSeeOtherGuests'] = guests_can_see_others
        
        # Handle Google Meet
        if create_google_meet:
            request_id = str(uuid.uuid4())
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': request_id,
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        
        # Handle reminders
        if not use_default_reminders or email_reminder_minutes is not None or popup_reminder_minutes is not None:
            event['reminders'] = {
                'useDefault': use_default_reminders,
                'overrides': []
            }
            
            if not use_default_reminders:
                if email_reminder_minutes is not None:
                    event['reminders']['overrides'].append({
                        'method': 'email',
                        'minutes': email_reminder_minutes
                    })
                
                if popup_reminder_minutes is not None:
                    event['reminders']['overrides'].append({
                        'method': 'popup',
                        'minutes': popup_reminder_minutes
                    })
        
        # Set query parameters for the API call
        query_params = {
            'sendUpdates': send_notifications
        }
        
        if create_google_meet:
            query_params['conferenceDataVersion'] = 1
        
        # Create the event via Google Calendar API
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            **query_params
        ).execute()
        
        # Format the response
        result = {
            'event_id': created_event['id'],
            'calendar_id': calendar_id,
            'summary': created_event['summary'],
            'start_time': created_event['start'].get('dateTime') or created_event['start'].get('date'),
            'end_time': created_event['end'].get('dateTime') or created_event['end'].get('date'),
            'html_link': created_event['htmlLink']
        }
        
        # Add Google Meet link if present
        if 'hangoutLink' in created_event:
            result['google_meet_link'] = created_event['hangoutLink']
        elif 'conferenceData' in created_event and created_event['conferenceData'].get('entryPoints'):
            for entry_point in created_event['conferenceData']['entryPoints']:
                if entry_point.get('entryPointType') == 'video':
                    result['google_meet_link'] = entry_point.get('uri', '')
                    break
        
        # Add attendee information if present
        if 'attendees' in created_event:
            result['attendees_notified'] = [
                attendee['email'] for attendee in created_event['attendees']
                if attendee.get('email')
            ]
        
        return result
        
    except HttpError as e:
        # Re-raise the original HttpError with additional context
        raise e
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Error creating event: {str(e)}")