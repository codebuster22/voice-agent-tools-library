"""
Simple appointment creation wrapper for voice agent.

Creates standardized 30-minute appointments with notifications.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dateutil import parser
from .create_event import create_event


async def create_appointment(
    service,
    calendar_id: str,
    summary: str,
    start_time: str,
    customer_email: str,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a simple 30-minute customer appointment with standardized settings.
    
    Args:
        service: Authenticated Google Calendar service object
        calendar_id: Target calendar identifier
        summary: Appointment title/summary
        start_time: Appointment start time (ISO format string)
        customer_email: Customer's email address for notifications
        description: Optional appointment description
        location: Optional physical location
        
    Returns:
        Dict containing created appointment details
        
    Raises:
        ValueError: For invalid parameters
        Exception: For API-related errors
    """
    # Parse start time and calculate end time (30 minutes later)
    try:
        start_dt = parser.isoparse(start_time)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid start_time format: {start_time}. Please use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    end_dt = start_dt + timedelta(minutes=30)
    
    # Call the full create_event function with standardized parameters
    return await create_event(
        service=service,
        calendar_id=calendar_id,
        summary=summary,
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat(),
        description=description,
        location=location,
        attendees=[customer_email],  # Single customer attendee
        create_google_meet=False,    # No Google Meet
        send_notifications="all",    # Send notifications
        email_reminder_minutes=60,   # 1 hour reminder
        popup_reminder_minutes=15,   # 15 minute popup
        use_default_reminders=False  # Use our custom reminders
    )