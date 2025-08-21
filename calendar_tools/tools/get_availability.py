from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any


async def get_availability(
    service,
    calendar_ids: Optional[List[str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    working_hours_start: int = 9,
    working_hours_end: int = 17,
    working_days: Optional[List[int]] = None,
    time_zone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get availability for specified calendars within working hours.
    
    Args:
        service: Authenticated Google Calendar service object
        calendar_ids: List of calendar IDs to check (defaults to ['primary'])
        start_time: Start datetime (defaults to today)
        end_time: End datetime (defaults to next week from start_time)
        working_hours_start: Working day start hour 0-23 (default: 9)
        working_hours_end: Working day end hour 0-23 (default: 17)
        working_days: List of working days 0-6 (Mon-Sun, defaults to Mon-Fri: [0,1,2,3,4])
        time_zone: Timezone for the query (defaults to UTC)
        
    Returns:
        Dict containing:
        - free_slots: List of available time slots within working hours
        - busy_periods: List of busy periods from the calendars
        - working_hours: Applied working hours configuration
        - date_range: Query date range used
        
    Raises:
        ValueError: If parameters are invalid
        Exception: If the API call fails
    """
    # Parameter validation
    if working_hours_start >= working_hours_end:
        raise ValueError("working_hours_start must be less than working_hours_end")
    
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]  # Monday-Friday
    
    if any(day < 0 or day > 6 for day in working_days):
        raise ValueError("working_days must contain values between 0-6 (Monday=0, Sunday=6)")
    
    if calendar_ids is None:
        calendar_ids = ['primary']
    
    # Set default date range: today to next week
    if start_time is None:
        start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end_time is None:
        end_time = start_time + timedelta(days=7)
    
    try:
        # Build freebusy query
        freebusy_body = {
            'timeMin': start_time.isoformat(),
            'timeMax': end_time.isoformat(),
            'items': [{'id': calendar_id} for calendar_id in calendar_ids]
        }
        
        if time_zone:
            freebusy_body['timeZone'] = time_zone
        
        # Query Google Calendar freebusy API
        freebusy_request = service.freebusy().query(body=freebusy_body)
        freebusy_result = freebusy_request.execute()
        
        # Extract busy periods from all calendars
        busy_periods = []
        calendars_data = freebusy_result.get('calendars', {})
        
        for calendar_id in calendar_ids:
            calendar_busy = calendars_data.get(calendar_id, {}).get('busy', [])
            for period in calendar_busy:
                busy_periods.append({
                    'start': period['start'],
                    'end': period['end'],
                    'calendar_id': calendar_id
                })
        
        # Generate working hours time slots
        working_slots = _generate_working_hours_slots(
            start_time, end_time, working_hours_start, working_hours_end, working_days, time_zone
        )
        
        # Filter out busy periods from working slots
        free_slots = _filter_busy_periods(working_slots, busy_periods)
        
        # Calculate duration for each free slot
        for slot in free_slots:
            start = _parse_datetime(slot['start'])
            end = _parse_datetime(slot['end'])
            slot['duration_minutes'] = int((end - start).total_seconds() / 60)
        
        return {
            'free_slots': free_slots,
            'busy_periods': busy_periods,
            'working_hours': {
                'start': working_hours_start,
                'end': working_hours_end,
                'days': working_days
            },
            'date_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }
        
    except Exception as e:
        raise Exception(f"Failed to get availability: {str(e)}")


def _generate_working_hours_slots(start_time, end_time, working_hours_start, working_hours_end, working_days, time_zone):
    """Generate time slots for working hours within the date range."""
    slots = []
    current_date = start_time.date()
    end_date = end_time.date()
    
    while current_date <= end_date:
        # Check if this day is a working day
        if current_date.weekday() in working_days:
            # Create working hours slot for this day
            if time_zone:
                import pytz
                tz = pytz.timezone(time_zone)
                slot_start = tz.localize(datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_start)))
                slot_end = tz.localize(datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_end)))
                # Convert to UTC for consistency
                slot_start = slot_start.astimezone(timezone.utc)
                slot_end = slot_end.astimezone(timezone.utc)
            else:
                slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_start), timezone.utc)
                slot_end = datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_end), timezone.utc)
            
            # Ensure slot is within the requested range
            if slot_start < start_time:
                slot_start = start_time
            if slot_end > end_time:
                slot_end = end_time
            
            # Only add if there's actual time in the slot
            if slot_start < slot_end:
                slots.append({
                    'start': slot_start.isoformat(),
                    'end': slot_end.isoformat()
                })
        
        current_date += timedelta(days=1)
    
    return slots


def _parse_datetime(iso_string):
    """Parse datetime string, handling 'Z' UTC suffix."""
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    return datetime.fromisoformat(iso_string)


def _filter_busy_periods(working_slots, busy_periods):
    """Filter out busy periods from working hours slots to find free time."""
    free_slots = []
    
    for slot in working_slots:
        slot_start = _parse_datetime(slot['start'])
        slot_end = _parse_datetime(slot['end'])
        
        # Find all busy periods that overlap with this slot
        overlapping_busy = []
        for busy in busy_periods:
            busy_start = _parse_datetime(busy['start'])
            busy_end = _parse_datetime(busy['end'])
            
            # Check for overlap
            if busy_start < slot_end and busy_end > slot_start:
                overlapping_busy.append((busy_start, busy_end))
        
        # Sort overlapping busy periods by start time
        overlapping_busy.sort()
        
        # Find free time segments within this slot
        current_time = slot_start
        
        for busy_start, busy_end in overlapping_busy:
            # If there's free time before this busy period
            if current_time < busy_start:
                free_end = min(busy_start, slot_end)
                if current_time < free_end:
                    free_slots.append({
                        'start': current_time.isoformat(),
                        'end': free_end.isoformat()
                    })
            
            # Move current time to end of busy period
            current_time = max(current_time, busy_end)
        
        # If there's free time after all busy periods
        if current_time < slot_end:
            free_slots.append({
                'start': current_time.isoformat(),
                'end': slot_end.isoformat()
            })
    
    return free_slots