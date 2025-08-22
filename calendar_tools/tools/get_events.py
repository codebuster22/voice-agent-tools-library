from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union


async def get_events(
    service,
    calendar_ids: Optional[List[str]] = None,
    event_id: Optional[str] = None,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    query: Optional[str] = None,
    max_results: int = 250,
    order_by: str = 'startTime',
    show_deleted: bool = False,
    time_zone: Optional[str] = None
) -> Union[Dict[str, Any], Dict[str, Any]]:
    """
    Get events from specified calendars or retrieve a single event by ID.
    
    Args:
        service: Authenticated Google Calendar service object
        calendar_ids: List of calendar IDs to query (defaults to ['primary'])
        event_id: Specific event ID to retrieve (returns single event if provided)
        time_min: Start of time range (defaults to today)
        time_max: End of time range (defaults to next week from time_min)
        query: Text search query across event fields
        max_results: Maximum number of events to return (default: 250, max: 2500)
        order_by: Sort order - 'startTime' or 'updated' (default: 'startTime')
        show_deleted: Include deleted events (default: False)
        time_zone: Timezone for returned times
        
    Returns:
        For single event (event_id provided): Dict with event details
        For multiple events: Dict containing:
        - events: List of matching events
        - summary: Query summary information
        - calendar_id: Calendar ID or 'multiple' for multi-calendar queries
        - date_range: Query date range used
        
    Raises:
        ValueError: If parameters are invalid
        Exception: If the API call fails
    """
    # Parameter validation
    if time_min and time_max and time_max <= time_min:
        raise ValueError("time_max must be after time_min")
    
    if calendar_ids is None:
        calendar_ids = ['primary']
    
    # Set default date range: today to next week
    if time_min is None:
        time_min = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if time_max is None:
        time_max = time_min + timedelta(days=7)
    
    try:
        # Handle single event retrieval
        if event_id:
            return await _get_single_event(service, calendar_ids[0], event_id)
        
        # Handle multiple events retrieval
        return await _get_multiple_events(
            service, calendar_ids, time_min, time_max, query, 
            max_results, order_by, show_deleted, time_zone
        )
        
    except Exception as e:
        # Re-raise with more context for specific errors
        if "not found" in str(e).lower() or "404" in str(e):
            raise Exception(f"Event not found: {str(e)}")
        raise Exception(f"Failed to get events: {str(e)}")


async def _get_single_event(service, calendar_id, event_id):
    """Retrieve a single event by ID."""
    event_request = service.events().get(calendarId=calendar_id, eventId=event_id)
    event = event_request.execute()
    
    # Standardize the response format
    return {
        'id': event.get('id'),
        'summary': event.get('summary', ''),
        'description': event.get('description', ''),
        'start': event.get('start', {}),
        'end': event.get('end', {}),
        'status': event.get('status', ''),
        'created': event.get('created', ''),
        'updated': event.get('updated', ''),
        'creator': event.get('creator', {}),
        'organizer': event.get('organizer', {}),
        'attendees': event.get('attendees', []),
        'location': event.get('location', ''),
        'htmlLink': event.get('htmlLink', ''),
        'hangoutLink': event.get('hangoutLink', ''),
        'calendar_id': calendar_id
    }


async def _get_multiple_events(service, calendar_ids, time_min, time_max, query, 
                             max_results, order_by, show_deleted, time_zone):
    """Retrieve multiple events with filtering."""
    all_events = []
    calendar_id_result = calendar_ids[0] if len(calendar_ids) == 1 else 'multiple'
    
    for calendar_id in calendar_ids:
        # Build request parameters
        params = {
            'calendarId': calendar_id,
            'timeMin': time_min.isoformat(),
            'timeMax': time_max.isoformat(),
            'maxResults': max_results,
            'singleEvents': True,
            'showDeleted': show_deleted
        }
        
        # Add optional parameters
        if query:
            params['q'] = query
            
        if order_by == 'startTime':
            params['orderBy'] = 'startTime'
        elif order_by == 'updated':
            params['orderBy'] = 'updated'
            
        if time_zone:
            params['timeZone'] = time_zone
        
        # Execute request
        events_request = service.events().list(**params)
        events_result = events_request.execute()
        
        # Process events
        calendar_events = events_result.get('items', [])
        for event in calendar_events:
            standardized_event = {
                'id': event.get('id'),
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'start': event.get('start', {}),
                'end': event.get('end', {}),
                'status': event.get('status', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', ''),
                'creator': event.get('creator', {}),
                'organizer': event.get('organizer', {}),
                'attendees': event.get('attendees', []),
                'location': event.get('location', ''),
                'htmlLink': event.get('htmlLink', ''),
                'hangoutLink': event.get('hangoutLink', ''),
                'calendar_id': calendar_id
            }
            all_events.append(standardized_event)
        
        # If we hit max_results for this calendar, stop processing others
        if len(all_events) >= max_results:
            all_events = all_events[:max_results]
            break
    
    # Build summary information
    summary = {
        'total_events': len(all_events),
        'max_results': max_results
    }
    
    if query:
        summary['query'] = query
    
    if order_by:
        summary['order_by'] = order_by
    
    return {
        'events': all_events,
        'summary': summary,
        'calendar_id': calendar_id_result,
        'date_range': {
            'start': time_min.isoformat(),
            'end': time_max.isoformat()
        }
    }