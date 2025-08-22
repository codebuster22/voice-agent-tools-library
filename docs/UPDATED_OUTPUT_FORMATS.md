# Updated Output Formats for Calendar Tools

## Summary of Changes
✅ **list_calendars()**: Now returns simplified, clean list of dicts  
✅ **get_availability()**: Already has good structured format  
✅ **get_events()**: Already has structured format (with minor inconsistency between single/multiple)

---

## 1. list_calendars() - NEW SIMPLIFIED FORMAT

**Returns:** List of dictionaries with essential calendar information

```python
[
    {
        "calendarId": "primary",
        "calendarName": "John Doe",
        "description": "Main personal calendar"
    },
    {
        "calendarId": "team@company.com", 
        "calendarName": "Team Calendar",
        "description": "Shared team events and meetings"
    },
    {
        "calendarId": "c_1234567890@group.calendar.google.com",
        "calendarName": "Project Alpha",
        "description": ""
    }
]
```

**Key Benefits:**
- ✅ Clean, minimal structure with only essential fields
- ✅ Consistent naming: `calendarId`, `calendarName`, `description`
- ✅ Easy to parse and display
- ✅ Removes Google API complexity

---

## 2. get_availability() - EXISTING STRUCTURED FORMAT

**Returns:** Dictionary with availability data and metadata

```python
{
    "free_slots": [
        {
            "start": "2025-08-21T09:00:00+00:00",
            "end": "2025-08-21T17:00:00+00:00",
            "duration_minutes": 480
        }
    ],
    "busy_periods": [
        {
            "start": "2025-08-21T03:30:00+00:00",
            "end": "2025-08-21T08:00:00+00:00", 
            "calendar_id": "primary"
        }
    ],
    "working_hours": {
        "start": 9,
        "end": 17,
        "days": [0, 1, 2, 3, 4]
    },
    "date_range": {
        "start": "2025-08-21T00:00:00+00:00",
        "end": "2025-08-24T00:00:00+00:00"
    }
}
```

---

## 3. get_events() - EXISTING STRUCTURED FORMAT

**Returns:** Dictionary with events and metadata (structure varies for single vs multiple)

### Multiple Events:
```python
{
    "events": [
        {
            "id": "abc123",
            "summary": "Team Meeting",
            "description": "Weekly sync",
            "start": {"dateTime": "2025-08-21T10:00:00+00:00"},
            "end": {"dateTime": "2025-08-21T11:00:00+00:00"},
            "status": "confirmed",
            "attendees": [...],
            "location": "Conference Room A",
            "calendar_id": "primary"
        }
    ],
    "summary": {
        "total_events": 1,
        "max_results": 250,
        "order_by": "startTime"
    },
    "calendar_id": "primary",
    "date_range": {
        "start": "2025-08-21T00:00:00+00:00",
        "end": "2025-08-28T00:00:00+00:00"
    }
}
```

### Single Event (by ID):
```python
{
    "id": "abc123",
    "summary": "Team Meeting",
    "description": "Weekly sync",
    "start": {"dateTime": "2025-08-21T10:00:00+00:00"},
    "end": {"dateTime": "2025-08-21T11:00:00+00:00"},
    "status": "confirmed",
    "attendees": [...],
    "location": "Conference Room A",
    "calendar_id": "primary"
}
```

---

## Usage Examples

```python
# 1. List calendars
calendars = await list_calendars(service)
for cal in calendars:
    print(f"Calendar: {cal['calendarName']} ({cal['calendarId']})")

# 2. Get availability  
availability = await get_availability(service)
print(f"Free slots: {len(availability['free_slots'])}")

# 3. Get multiple events
events_data = await get_events(service)
events = events_data['events']
print(f"Found {events_data['summary']['total_events']} events")

# 4. Get single event
single_event = await get_events(service, event_id="abc123")
print(f"Event: {single_event['summary']}")
```

---

## Next Steps

The output formats are now clean and structured:
- **list_calendars()**: ✅ Simplified and consistent
- **get_availability()**: ✅ Already well-structured  
- **get_events()**: ✅ Structured but could be unified (minor inconsistency between single/multiple)

All functions provide structured, predictable output that's easy to work with in AI agent scenarios!