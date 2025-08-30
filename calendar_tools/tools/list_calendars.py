import re
import time
from typing import List, Optional
from logging_config import google_calendar_logger

async def list_calendars(
    service, 
    max_results=100, 
    show_hidden=False,
    query_strings: Optional[List[str]] = None,
    query_string_to_include: bool = True
):
    """
    List all accessible calendars with optional regex filtering.
    
    Args:
        service: Authenticated Google Calendar service object
        max_results: Maximum number of calendars to return (default: 100)
        show_hidden: Whether to include hidden calendars (default: False)
        query_strings: List of regex patterns to filter calendars (optional)
        query_string_to_include: If True, include calendars matching patterns; 
                               If False, exclude calendars matching patterns (default: True)
        
    Returns:
        List of calendar dictionaries with simplified format:
        [
            {
                'calendarId': 'primary',
                'calendarName': 'John Doe',
                'description': 'Main calendar'
            },
            ...
        ]
        
    Raises:
        Exception: If the API call fails
    """
    try:
        # Log API call
        google_calendar_logger.log_call(
            "calendarList.list",
            params={
                "maxResults": max_results,
                "showHidden": show_hidden,
                "query_filters": len(query_strings) if query_strings else 0
            }
        )
        
        start_time = time.time()
        request = service.calendarList().list(
            maxResults=max_results,
            showHidden=show_hidden
        )
        response = request.execute()
        duration_ms = (time.time() - start_time) * 1000
        
        # Log successful response
        calendars_count = len(response.get('items', []))
        google_calendar_logger.log_response(
            "calendarList.list",
            success=True,
            response={"calendars_count": calendars_count},
            duration_ms=duration_ms
        )
        
        calendars = response.get('items', [])
        
        # Apply regex filtering if query_strings provided
        if query_strings:
            filtered_calendars = []
            
            for calendar in calendars:
                # Check all searchable fields
                searchable_text = " ".join([
                    calendar.get('summary', ''),
                    calendar.get('description', ''),
                    calendar.get('id', '')
                ]).lower()
                
                # Check if any pattern matches
                pattern_matches = any(
                    re.search(pattern, searchable_text, re.IGNORECASE) 
                    for pattern in query_strings
                )
                
                # Include/exclude based on query_string_to_include flag
                if query_string_to_include:
                    # Include if pattern matches
                    if pattern_matches:
                        filtered_calendars.append(calendar)
                else:
                    # Exclude if pattern matches (include if NOT matching)
                    if not pattern_matches:
                        filtered_calendars.append(calendar)
            
            return _format_calendars(filtered_calendars)
        
        return _format_calendars(calendars)
        
    except Exception as e:
        # Log error
        google_calendar_logger.log_response(
            "calendarList.list",
            success=False,
            error=str(e)
        )
        raise Exception(f"Failed to list calendars: {str(e)}")


def _format_calendars(calendars):
    """Format raw calendar data into clean, simplified structure."""
    formatted_calendars = []
    
    for calendar in calendars:
        formatted_calendar = {
            'calendarId': calendar.get('id', ''),
            'calendarName': calendar.get('summary', ''),
            'description': calendar.get('description', ''),
        }
        formatted_calendars.append(formatted_calendar)
    
    return formatted_calendars