import re
from typing import List, Optional

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
        List of calendar dictionaries with id, summary, accessRole, etc.
        
    Raises:
        Exception: If the API call fails
    """
    try:
        request = service.calendarList().list(
            maxResults=max_results,
            showHidden=show_hidden
        )
        response = request.execute()
        
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
            
            return filtered_calendars
        
        return calendars
        
    except Exception as e:
        raise Exception(f"Failed to list calendars: {str(e)}")