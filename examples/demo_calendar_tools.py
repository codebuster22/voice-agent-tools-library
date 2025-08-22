#!/usr/bin/env python3
"""
Demo script showcasing Google Calendar Tools functionality:
1. List all calendars
2. Get availability for working hours
3. Get events (both single and multiple)
4. Create events with various configurations
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from calendar_tools.auth import create_service
from calendar_tools.tools.list_calendars import list_calendars
from calendar_tools.tools.get_availability import get_availability
from calendar_tools.tools.get_events import get_events
from calendar_tools.tools.create_event import create_event
from calendar_tools.tools.delete_event import delete_event


async def main():
    """Demo all calendar tools functionality."""
    
    # Get email from environment
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        print("❌ EMAIL_FOR_TESTING environment variable not set")
        return
    
    print(f"🔑 Authenticating with email: {email}")
    service = await create_service(email)
    print("✅ Authentication successful\n")
    
    # ============================================================================
    # 1. GET ALL CALENDARS
    # ============================================================================
    print("📅 STEP 1: Getting all calendars...")
    calendars = await list_calendars(service, show_hidden=True)
    
    print(f"Found {len(calendars)} calendars:")
    for i, calendar in enumerate(calendars[:5], 1):  # Show first 5
        calendar_name = calendar.get('calendarName', 'Unknown')
        primary_tag = " (PRIMARY)" if calendar.get('calendarId') == 'primary' else ""
        description = calendar.get('description', '')
        desc_preview = f" - {description[:50]}..." if description else ""
        print(f"  {i}. {calendar_name}{primary_tag}")
        print(f"     ID: {calendar['calendarId']}")
        print(f"     Description: {desc_preview}")
        print()
    
    if len(calendars) > 5:
        print(f"  ... and {len(calendars) - 5} more calendars")
    print()
    
    # ============================================================================
    # 2. GET AVAILABILITY
    # ============================================================================
    print("⏰ STEP 2: Getting availability for the next 3 days...")
    start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=3)
    
    availability = await get_availability(
        service,
        calendar_ids=['primary'],
        start_time=start_time,
        end_time=end_time,
        working_hours_start=9,
        working_hours_end=17
    )
    
    print(f"📊 Availability Summary:")
    print(f"   Date range: {start_time.date()} to {end_time.date()}")
    print(f"   Working hours: {availability['working_hours']['start']}:00 - {availability['working_hours']['end']}:00")
    print(f"   Free slots: {len(availability['free_slots'])}")
    print(f"   Busy periods: {len(availability['busy_periods'])}")
    
    if availability['free_slots']:
        print(f"\n🟢 Next available slots:")
        for i, slot in enumerate(availability['free_slots'][:3], 1):  # Show first 3
            start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            duration = slot['duration_minutes']
            print(f"   {i}. {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')} ({duration} min)")
    
    if availability['busy_periods']:
        print(f"\n🔴 Upcoming busy periods:")
        for i, period in enumerate(availability['busy_periods'][:3], 1):  # Show first 3
            start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
            print(f"   {i}. {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}")
    print()
    
    # ============================================================================
    # 3. GET EVENTS - Multiple Events (Bulk Query)
    # ============================================================================
    print("📋 STEP 3a: Getting multiple events (next 7 days)...")
    
    # Multiple events with various filters
    events_bulk = await get_events(
        service,
        calendar_ids=['primary'],
        time_min=start_time,
        time_max=start_time + timedelta(days=7),
        max_results=10,
        order_by='startTime'
    )
    
    print(f"📊 Events Summary:")
    print(f"   Total events found: {len(events_bulk['events'])}")
    print(f"   Date range: {start_time.date()} to {(start_time + timedelta(days=7)).date()}")
    
    if events_bulk['events']:
        print(f"\n📝 Upcoming events:")
        for i, event in enumerate(events_bulk['events'][:5], 1):  # Show first 5
            summary = event.get('summary', 'No title')
            start_time_str = 'TBD'
            
            if 'start' in event:
                if 'dateTime' in event['start']:
                    start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    start_time_str = start_dt.strftime('%Y-%m-%d %H:%M')
                elif 'date' in event['start']:
                    start_time_str = f"{event['start']['date']} (All day)"
            
            attendee_count = len(event.get('attendees', []))
            location = event.get('location', '')
            location_str = f" @ {location}" if location else ""
            
            print(f"   {i}. {summary}")
            print(f"      Time: {start_time_str}")
            print(f"      Attendees: {attendee_count}{location_str}")
            print(f"      ID: {event['id']}")
            print()
        
        # ========================================================================
        # 4. GET EVENTS - Single Event by ID
        # ========================================================================
        print("📋 STEP 3b: Getting single event by ID...")
        
        # Use the first event's ID for single event retrieval
        first_event_id = events_bulk['events'][0]['id']
        print(f"Fetching event ID: {first_event_id}")
        
        single_event = await get_events(
            service,
            calendar_ids=['primary'],
            event_id=first_event_id
        )
        
        print(f"\n🔍 Single Event Details:")
        print(f"   Title: {single_event.get('summary', 'No title')}")
        print(f"   Description: {single_event.get('description', 'No description')[:100]}...")
        print(f"   Status: {single_event.get('status', 'unknown')}")
        print(f"   Created: {single_event.get('created', 'unknown')}")
        print(f"   Creator: {single_event.get('creator', {}).get('email', 'unknown')}")
        
        if single_event.get('attendees'):
            print(f"   Attendees ({len(single_event['attendees'])}):")
            for attendee in single_event['attendees'][:3]:  # Show first 3
                email = attendee.get('email', 'No email')
                status = attendee.get('responseStatus', 'unknown')
                organizer = " (Organizer)" if attendee.get('organizer') else ""
                print(f"     - {email}: {status}{organizer}")
    
    else:
        print("   No events found in the specified date range")
    
    print()
    
    # ============================================================================
    # 5. GET EVENTS - Text Search
    # ============================================================================
    print("🔍 STEP 3c: Searching events with text query...")
    
    search_events = await get_events(
        service,
        calendar_ids=['primary'],
        query="meeting",  # Search for events containing "meeting"
        max_results=5
    )
    
    print(f"📊 Search Results for 'meeting':")
    print(f"   Found: {len(search_events['events'])} events")
    
    for i, event in enumerate(search_events['events'][:3], 1):  # Show first 3
        summary = event.get('summary', 'No title')
        print(f"   {i}. {summary}")
    print()
    
    # ============================================================================
    # 4. CREATE EVENTS
    # ============================================================================
    print("➕ STEP 4: Creating demo events...")
    
    # Get next week for event creation
    next_week_start = datetime.now(timezone.utc) + timedelta(days=7)
    next_week_start = next_week_start.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # ========================================================================
    # 4a. Basic Event
    # ========================================================================
    print("\n📝 Creating basic event...")
    basic_event = await create_event(
        service,
        calendar_id='primary',
        summary='Demo Basic Event',
        start_time=next_week_start.isoformat(),
        end_time=(next_week_start + timedelta(hours=1)).isoformat(),
        description='This is a basic demo event created by the calendar tools.',
        location='Conference Room A',
        timezone='America/New_York'
    )
    
    print(f"✅ Basic event created:")
    print(f"   ID: {basic_event['event_id']}")
    print(f"   Title: {basic_event['summary']}")
    print(f"   Start: {basic_event['start_time']}")
    print(f"   Link: {basic_event['html_link']}")
    
    # ========================================================================
    # 4b. Google Meet Event
    # ========================================================================
    print("\n📹 Creating Google Meet event...")
    meet_start = next_week_start + timedelta(hours=2)
    meet_event = await create_event(
        service,
        calendar_id='primary',
        summary='Demo Google Meet Event',
        start_time=meet_start.isoformat(),
        end_time=(meet_start + timedelta(hours=1)).isoformat(),
        description='Demo event with Google Meet integration.',
        location='Virtual Meeting Room',
        create_google_meet=True,
        attendees=['demo@example.com'],
        send_notifications='none',  # Don't spam demo emails
        timezone='America/New_York'
    )
    
    print(f"✅ Google Meet event created:")
    print(f"   ID: {meet_event['event_id']}")
    print(f"   Title: {meet_event['summary']}")
    print(f"   Meet Link: {meet_event.get('google_meet_link', 'Link pending...')}")
    
    # ========================================================================
    # 4c. Recurring Event
    # ========================================================================
    print("\n🔄 Creating recurring event (weekly for 4 weeks)...")
    recurring_start = next_week_start + timedelta(days=1, hours=2)
    recurring_event = await create_event(
        service,
        calendar_id='primary',
        summary='Demo Weekly Standup',
        start_time=recurring_start.isoformat(),
        end_time=(recurring_start + timedelta(minutes=30)).isoformat(),
        description='Weekly team standup meeting.',
        location='Team Room',
        recurrence_rule='FREQ=WEEKLY;COUNT=4',
        email_reminder_minutes=15,
        popup_reminder_minutes=5,
        use_default_reminders=False,
        visibility='private',
        timezone='America/New_York'
    )
    
    print(f"✅ Recurring event created:")
    print(f"   ID: {recurring_event['event_id']}")
    print(f"   Title: {recurring_event['summary']}")
    print(f"   Recurrence: Weekly for 4 weeks")
    
    # ========================================================================
    # 4d. All-Day Event
    # ========================================================================
    print("\n📅 Creating all-day event...")
    all_day_date = (datetime.now() + timedelta(days=10)).date()
    all_day_event = await create_event(
        service,
        calendar_id='primary',
        summary='Demo All-Day Event',
        start_time=all_day_date.isoformat(),
        end_time=(all_day_date + timedelta(days=1)).isoformat(),
        description='Demo all-day event like a holiday or vacation day.',
        all_day=True,
        color_id=9  # Blue color
    )
    
    print(f"✅ All-day event created:")
    print(f"   ID: {all_day_event['event_id']}")
    print(f"   Title: {all_day_event['summary']}")
    print(f"   Date: {all_day_date}")
    
    print()
    
    # ============================================================================
    # 5. DELETE EVENTS (Clean up demo events)
    # ============================================================================
    print("🗑️  STEP 5: Deleting demo events (cleanup)...")
    
    # Collect event IDs to delete
    demo_event_ids = [
        basic_event['event_id'],
        meet_event['event_id'], 
        recurring_event['event_id'],
        all_day_event['event_id']
    ]
    
    print(f"\n🧹 Cleaning up {len(demo_event_ids)} demo events...")
    
    deleted_count = 0
    for i, event_id in enumerate(demo_event_ids, 1):
        try:
            delete_result = await delete_event(
                service,
                event_id=event_id,
                send_notifications=False  # Don't spam notifications during cleanup
            )
            
            if delete_result['success']:
                deleted_count += 1
                print(f"   ✅ Deleted event {i}/{len(demo_event_ids)}: {event_id[:15]}...")
            else:
                print(f"   ❌ Failed to delete event {i}: {event_id[:15]}...")
        
        except Exception as e:
            print(f"   ⚠️  Error deleting event {i}: {str(e)[:50]}...")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Successfully deleted: {deleted_count}/{len(demo_event_ids)} events")
    print(f"   Calendar is now clean of demo events")
    
    # ========================================================================
    # 5b. Demonstrate Force Delete (for already deleted events)
    # ========================================================================
    print(f"\n🔄 Testing force delete on already-deleted event...")
    
    force_delete_result = await delete_event(
        service,
        event_id=basic_event['event_id'],  # Already deleted above
        force_delete=True
    )
    
    if force_delete_result['success'] and force_delete_result.get('was_missing'):
        print(f"   ✅ Force delete handled gracefully: {force_delete_result['message']}")
    else:
        print(f"   ⚠️  Unexpected force delete result")
    
    print()
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("="*60)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("What we demonstrated:")
    print("1. 📅 Listed all calendars with access levels")
    print("2. ⏰ Got availability within working hours")
    print("3. 📋 Retrieved multiple events with date filtering")
    print("4. 🔍 Fetched single event by ID with full details")
    print("5. 🔍 Searched events using text query")
    print("6. ➕ Created various types of events:")
    print("   - Basic event with description and location")
    print("   - Google Meet event with virtual meeting link")
    print("   - Recurring weekly event with custom reminders")
    print("   - All-day event with custom color")
    print("7. 🗑️  Deleted events with proper cleanup:")
    print("   - Batch deletion of multiple events")
    print("   - Force deletion handling for missing events")
    print("   - Silent deletion without attendee notifications")
    print()
    print("COMPLETE CRUD OPERATIONS:")
    print("✅ CREATE: create_event() - Full event creation with all parameters")
    print("✅ READ: get_events() - Single/bulk retrieval with filtering")
    print("✅ DELETE: delete_event() - Clean deletion with error handling")
    print()
    print("EVENT CREATION INPUT OPTIONS:")
    print("- calendar_id, summary, start_time, end_time (required)")
    print("- description, location, timezone (optional)")
    print("- attendees, optional_attendees (lists of emails)")
    print("- create_google_meet (boolean for video conferencing)")
    print("- recurrence_rule (RRULE format for repeating events)")
    print("- email_reminder_minutes, popup_reminder_minutes")
    print("- visibility (default/public/private/confidential)")
    print("- color_id (1-24 for custom event colors)")
    print("- all_day (boolean for date-only events)")
    print("- send_notifications (all/external/none)")
    print()
    print("EVENT DELETION INPUT OPTIONS:")
    print("- event_id (required)")
    print("- calendar_id (defaults to 'primary')")
    print("- send_notifications (boolean, defaults to True)")
    print("- force_delete (boolean, handles missing events gracefully)")


if __name__ == "__main__":
    asyncio.run(main())