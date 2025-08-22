"""
Google Calendar update_event tool for AI agents.

This tool provides comprehensive event updating capabilities with agent-friendly parameters.
Supports partial updates, attendee management, Google Meet integration, and recurring events.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_event(
    service,
    event_id: str,
    calendar_id: str,
    # Basic event fields
    summary: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    
    # Time fields
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    timezone: Optional[str] = None,
    all_day: Optional[bool] = None,
    
    # Attendee management
    attendees: Optional[List[str]] = None,
    optional_attendees: Optional[List[str]] = None,
    attendee_action: str = "replace",  # "replace", "add", "remove"
    
    # Conference/Meeting
    create_google_meet: Optional[bool] = None,
    remove_google_meet: bool = False,
    
    # Notifications
    send_notifications: str = "all",  # "all", "external_only", "none"
    guests_can_invite_others: Optional[bool] = None,
    guests_can_modify: Optional[bool] = None,
    guests_can_see_others: Optional[bool] = None,
    
    # Event properties
    visibility: Optional[str] = None,  # "default", "public", "private"
    color_id: Optional[int] = None,  # 1-24
    status: Optional[str] = None,  # "confirmed", "tentative", "cancelled"
    
    # Recurrence handling
    recurrence_rule: Optional[str] = None,
    remove_recurrence: bool = False,
    recurring_update_scope: str = "single",  # "single", "all", "following"
    
    # Reminders
    email_reminder_minutes: Optional[int] = None,
    popup_reminder_minutes: Optional[int] = None,
    use_default_reminders: Optional[bool] = None,
    clear_all_reminders: bool = False
) -> Dict[str, Any]:
    """
    Update an existing Google Calendar event with partial update support.
    
    Args:
        service: Authenticated Google Calendar API service
        event_id: Unique identifier of event to update
        calendar_id: Target calendar identifier
        summary: Event title/summary
        description: Event description
        location: Event location
        start_time: Event start time (ISO format)
        end_time: Event end time (ISO format)
        timezone: Event timezone (e.g., 'America/New_York')
        all_day: Whether event is all-day
        attendees: Required attendees list
        optional_attendees: Optional attendees list
        attendee_action: How to handle attendees ("replace", "add", "remove")
        create_google_meet: Add Google Meet to event
        remove_google_meet: Remove Google Meet from event
        send_notifications: Notification scope ("all", "external_only", "none")
        guests_can_invite_others: Allow guests to invite others
        guests_can_modify: Allow guests to modify event
        guests_can_see_others: Allow guests to see other guests
        visibility: Event visibility level
        color_id: Event color (1-24)
        status: Event status
        recurrence_rule: RRULE for recurring events
        remove_recurrence: Remove recurrence from event
        recurring_update_scope: Scope for recurring updates
        email_reminder_minutes: Email reminder time
        popup_reminder_minutes: Popup reminder time
        use_default_reminders: Use calendar default reminders
        clear_all_reminders: Remove all reminders
        
    Returns:
        Dict containing updated event data and metadata
        
    Raises:
        ValueError: For invalid parameters
        Exception: For API errors (404, 403, etc.)
    """
    
    # Input validation
    _validate_inputs(
        event_id, calendar_id, attendee_action, color_id, 
        create_google_meet, remove_google_meet, recurring_update_scope
    )
    
    try:
        # Get current event
        current_event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Track which fields we're updating
        updated_fields = []
        
        # Build update payload
        event_body = {}
        
        # Basic fields
        if summary is not None:
            event_body['summary'] = summary
            updated_fields.append('summary')
            
        if description is not None:
            event_body['description'] = description
            updated_fields.append('description')
            
        if location is not None:
            event_body['location'] = location
            updated_fields.append('location')
        
        # Time fields
        if start_time is not None or end_time is not None or all_day is not None:
            event_body.update(_build_time_fields(
                current_event, start_time, end_time, timezone, all_day
            ))
            if start_time is not None:
                updated_fields.append('start_time')
            if end_time is not None:
                updated_fields.append('end_time')
        
        # Attendees
        if attendees is not None or optional_attendees is not None:
            event_body['attendees'] = _build_attendees_list(
                current_event, attendees, optional_attendees, attendee_action
            )
            updated_fields.append('attendees')
        
        # Google Meet / Conference
        if create_google_meet or remove_google_meet:
            if remove_google_meet:
                # To remove conference data, we need to explicitly set it to null and use PATCH
                # Google Calendar API requires null to remove conference data
                event_body['conferenceData'] = None
            elif create_google_meet:
                conference_data = _build_conference_data(create_google_meet, remove_google_meet)
                event_body['conferenceData'] = conference_data
            updated_fields.append('conference_data')
        
        # Guest permissions
        if any(x is not None for x in [guests_can_invite_others, guests_can_modify, guests_can_see_others]):
            event_body.update(_build_guest_permissions(
                guests_can_invite_others, guests_can_modify, guests_can_see_others
            ))
            updated_fields.append('guest_permissions')
        
        # Event properties
        if visibility is not None:
            event_body['visibility'] = visibility
            updated_fields.append('visibility')
            
        if color_id is not None:
            event_body['colorId'] = str(color_id)
            updated_fields.append('color_id')
            
        if status is not None:
            event_body['status'] = status
            updated_fields.append('status')
        
        # Recurrence
        if recurrence_rule is not None:
            # Ensure recurrence rule has proper RRULE: prefix
            if not recurrence_rule.startswith('RRULE:'):
                recurrence_rule = f'RRULE:{recurrence_rule}'
            event_body['recurrence'] = [recurrence_rule]
            updated_fields.append('recurrence')
        elif remove_recurrence:
            event_body['recurrence'] = None
            updated_fields.append('recurrence')
        
        # Reminders
        if _should_update_reminders(email_reminder_minutes, popup_reminder_minutes, 
                                   use_default_reminders, clear_all_reminders):
            event_body['reminders'] = _build_reminders(
                email_reminder_minutes, popup_reminder_minutes,
                use_default_reminders, clear_all_reminders
            )
            updated_fields.append('reminders')
        
        # Map send_notifications to sendUpdates
        send_updates = _map_send_notifications(send_notifications)
        
        # Perform the update
        if not updated_fields:
            # No updates requested, return current event data
            logger.info(f"No updates requested for event {event_id}")
            return _format_response(current_event, [], attendee_action, recurring_update_scope, calendar_id)
        
        logger.info(f"Updating event {event_id} with fields: {updated_fields}")
        
        # Prepare patch parameters
        patch_params = {
            'calendarId': calendar_id,
            'eventId': event_id,
            'body': event_body,
            'sendUpdates': send_updates
        }
        
        # Add conferenceDataVersion if needed
        if create_google_meet or remove_google_meet:
            patch_params['conferenceDataVersion'] = 1
        
        updated_event = service.events().patch(**patch_params).execute()
        
        return _format_response(updated_event, updated_fields, attendee_action, recurring_update_scope, calendar_id)
        
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {str(e)}")
        _handle_api_errors(e, event_id, calendar_id)


def _validate_inputs(event_id, calendar_id, attendee_action, color_id, 
                    create_google_meet, remove_google_meet, recurring_update_scope):
    """Validate input parameters."""
    if not event_id or not calendar_id:
        raise ValueError("event_id and calendar_id are required")
    
    if attendee_action not in ["replace", "add", "remove"]:
        raise ValueError("Invalid attendee_action. Must be 'replace', 'add', or 'remove'")
    
    if color_id is not None and (color_id < 1 or color_id > 24):
        raise ValueError("color_id must be between 1 and 24")
    
    if create_google_meet and remove_google_meet:
        raise ValueError("Cannot both create and remove Google Meet in same update")
    
    if recurring_update_scope not in ["single", "all", "following"]:
        raise ValueError("Invalid recurring_update_scope. Must be 'single', 'all', or 'following'")


def _build_time_fields(current_event, start_time, end_time, timezone, all_day):
    """Build time-related fields for the event update."""
    time_fields = {}
    
    current_start = current_event.get('start', {})
    current_end = current_event.get('end', {})
    
    if all_day is True:
        # Converting to all-day event
        if start_time:
            start_date = start_time.split('T')[0]
        else:
            start_date = current_start.get('date') or current_start.get('dateTime', '').split('T')[0]
            
        if end_time:
            end_date = end_time.split('T')[0]
        else:
            end_date = current_end.get('date') or current_end.get('dateTime', '').split('T')[0]
            
        time_fields['start'] = {'date': start_date}
        time_fields['end'] = {'date': end_date}
        
    elif all_day is False:
        # Converting from all-day to timed event
        start_dt = start_time or current_start.get('dateTime')
        end_dt = end_time or current_end.get('dateTime')
        
        if timezone:
            time_fields['start'] = {'dateTime': start_dt, 'timeZone': timezone}
            time_fields['end'] = {'dateTime': end_dt, 'timeZone': timezone}
        else:
            time_fields['start'] = {'dateTime': start_dt}
            time_fields['end'] = {'dateTime': end_dt}
    
    else:
        # Regular time update (not changing all-day status)
        if start_time:
            if current_start.get('date'):
                # Currently all-day, keep as all-day
                time_fields['start'] = {'date': start_time.split('T')[0]}
            else:
                # Timed event
                time_fields['start'] = {'dateTime': start_time}
                if timezone:
                    time_fields['start']['timeZone'] = timezone
                    
        if end_time:
            if current_end.get('date'):
                # Currently all-day, keep as all-day
                time_fields['end'] = {'date': end_time.split('T')[0]}
            else:
                # Timed event  
                time_fields['end'] = {'dateTime': end_time}
                if timezone:
                    time_fields['end']['timeZone'] = timezone
    
    return time_fields


def _build_attendees_list(current_event, attendees, optional_attendees, attendee_action):
    """Build attendees list based on action type."""
    current_attendees = current_event.get('attendees', [])
    
    # Build new attendees list
    new_attendees = []
    if attendees:
        new_attendees.extend([{'email': email, 'responseStatus': 'needsAction'} for email in attendees])
    
    if optional_attendees:
        new_attendees.extend([{'email': email, 'optional': True, 'responseStatus': 'needsAction'} 
                             for email in optional_attendees])
    
    if attendee_action == "replace":
        return new_attendees
    
    elif attendee_action == "add":
        # Add new attendees to existing list
        existing_emails = {att.get('email') for att in current_attendees}
        result_attendees = current_attendees.copy()
        
        for new_att in new_attendees:
            if new_att['email'] not in existing_emails:
                result_attendees.append(new_att)
        
        return result_attendees
    
    elif attendee_action == "remove":
        # Remove specified attendees
        emails_to_remove = {att['email'] for att in new_attendees}
        return [att for att in current_attendees if att.get('email') not in emails_to_remove]
    
    return current_attendees


def _build_conference_data(create_google_meet, remove_google_meet):
    """Build conference data for Google Meet."""
    if remove_google_meet:
        return None
    
    if create_google_meet:
        return {
            'createRequest': {
                'requestId': f"meet-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        }
    
    return None


def _build_guest_permissions(guests_can_invite_others, guests_can_modify, guests_can_see_others):
    """Build guest permission fields."""
    permissions = {}
    
    if guests_can_invite_others is not None:
        permissions['guestsCanInviteOthers'] = guests_can_invite_others
    
    if guests_can_modify is not None:
        permissions['guestsCanModify'] = guests_can_modify
    
    if guests_can_see_others is not None:
        permissions['guestsCanSeeOtherGuests'] = guests_can_see_others
    
    return permissions


def _should_update_reminders(email_reminder_minutes, popup_reminder_minutes, 
                           use_default_reminders, clear_all_reminders):
    """Check if reminders should be updated."""
    return any(x is not None for x in [email_reminder_minutes, popup_reminder_minutes, 
                                      use_default_reminders]) or clear_all_reminders


def _build_reminders(email_reminder_minutes, popup_reminder_minutes, 
                    use_default_reminders, clear_all_reminders):
    """Build reminders configuration."""
    if clear_all_reminders:
        return {'useDefault': False, 'overrides': []}
    
    if use_default_reminders:
        return {'useDefault': True}
    
    # Custom reminders
    overrides = []
    
    if email_reminder_minutes is not None:
        overrides.append({'method': 'email', 'minutes': email_reminder_minutes})
    
    if popup_reminder_minutes is not None:
        overrides.append({'method': 'popup', 'minutes': popup_reminder_minutes})
    
    if overrides:
        return {'useDefault': False, 'overrides': overrides}
    
    return {'useDefault': False, 'overrides': []}


def _map_send_notifications(send_notifications):
    """Map send_notifications to Google API sendUpdates parameter."""
    mapping = {
        'all': 'all',
        'external_only': 'externalOnly', 
        'none': 'none'
    }
    return mapping.get(send_notifications, 'all')


def _format_response(event_data, updated_fields, attendee_action, recurring_update_scope, calendar_id=None):
    """Format the response with consistent structure."""
    response = {
        'event_id': event_data['id'],
        'calendar_id': calendar_id or event_data.get('organizer', {}).get('email', ''),
        'summary': event_data.get('summary', ''),
        'updated_fields': updated_fields,
        'html_link': event_data.get('htmlLink', ''),
        'attendee_action': attendee_action,
        'recurring_update_scope': recurring_update_scope
    }
    
    # Add optional fields if present
    if event_data.get('start', {}).get('dateTime'):
        response['start_time'] = event_data['start']['dateTime']
    
    if event_data.get('end', {}).get('dateTime'):
        response['end_time'] = event_data['end']['dateTime']
    
    if event_data.get('description'):
        response['description'] = event_data['description']
    
    if event_data.get('location'):
        response['location'] = event_data['location']
    
    if event_data.get('visibility'):
        response['visibility'] = event_data['visibility']
    
    if event_data.get('colorId'):
        response['color_id'] = int(event_data['colorId'])
    
    if event_data.get('status'):
        response['status'] = event_data['status']
    
    # Google Meet link
    conference_data = event_data.get('conferenceData', {})
    if conference_data:
        entry_points = conference_data.get('entryPoints', [])
        for entry in entry_points:
            if entry.get('entryPointType') == 'video':
                response['google_meet_link'] = entry.get('uri')
                break
    
    # Attendees info
    attendees = event_data.get('attendees', [])
    if attendees:
        response['attendees_notified'] = [att['email'] for att in attendees]
    
    # Recurring event info
    response['was_recurring'] = bool(event_data.get('recurrence'))
    
    return response


def _handle_api_errors(error, event_id, calendar_id):
    """Handle and re-raise API errors with helpful messages."""
    error_str = str(error).lower()
    
    if "404" in error_str or "not found" in error_str:
        raise Exception(f"Event not found: {event_id} in calendar {calendar_id}. "
                       f"Please verify the event ID and calendar ID are correct.")
    
    elif "403" in error_str or "forbidden" in error_str:
        raise Exception(f"Insufficient permissions to update event {event_id}. "
                       f"You may not have edit access to this calendar.")
    
    elif "409" in error_str or "conflict" in error_str:
        raise Exception(f"Conflict updating event {event_id}. This may be a recurring event issue.")
    
    elif "400" in error_str or "bad request" in error_str:
        raise Exception(f"Invalid update data for event {event_id}. Please check your parameters.")
    
    elif "410" in error_str:
        raise Exception(f"Event {event_id} has been cancelled or deleted and cannot be updated.")
    
    else:
        raise error