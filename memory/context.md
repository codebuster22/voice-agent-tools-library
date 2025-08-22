# Google Calendar Tools - Development Context

## Project Goal
Create a set of Google Calendar API tools for AI agents that can be used both via direct import and API access patterns.

## Architecture Standards
- **Simplicity First**: Avoid over-engineering, prefer simple solutions
- **Tool-Focused Design**: Individual functions for specific operations, no monolithic classes
- **Dual Access**: Support both programmatic import and API wrapper usage
- **Native Async**: All functions use async/await patterns

## Project Structure
```
├── main.py                    # Main entry point (only file in root)
├── README.md                  # Project documentation
├── pyproject.toml             # Python project configuration
├── uv.lock                    # UV dependency lock file
├── calendar_tools/
│   ├── auth.py                # OAuth 2.0 authentication
│   ├── tools/
│   │   ├── list_calendars.py  # ✅ Complete with regex filtering + simplified output
│   │   ├── get_availability.py # ✅ Complete with working hours filtering
│   │   ├── get_events.py      # ✅ Complete with flexible event retrieval
│   │   ├── create_event.py    # 🔄 Planned
│   │   ├── update_event.py    # 🔄 Planned
│   │   └── delete_event.py    # 🔄 Planned
│   └── __init__.py            # Public exports
├── tests/
│   ├── test_list_calendars.py # ✅ 13 comprehensive tests
│   ├── test_get_availability.py # ✅ 13 comprehensive tests
│   └── test_get_events.py     # ✅ 14 comprehensive tests
├── examples/
│   └── demo_calendar_tools.py # Comprehensive demo script
├── docs/
│   └── UPDATED_OUTPUT_FORMATS.md # Output format documentation
├── memory/
│   └── context.md             # Development context (this file)
└── tokens/                    # OAuth token storage (gitignored)
```

## Progress Summary

### ✅ Completed
1. **Authentication System**
   - OAuth 2.0 with refresh token support
   - Local server callback flow (localhost:8080)
   - Automatic token refresh and secure storage
   - Email-based token management
   - Environment variable support (GOOGLE_CLIENT_ID/SECRET) with .json fallback

2. **list_calendars Tool**
   - Basic calendar listing functionality
   - Optional parameters: `max_results`, `show_hidden`
   - Regex filtering: `query_strings`, `query_string_to_include`
   - Case-insensitive, multi-field search (summary, description, id)
   - **Simplified Output Format**: Returns clean list of dicts with `calendarId`, `calendarName`, `description`
   - 13 comprehensive tests covering all scenarios
   - Real API testing validated (30 calendars → 6 after filtering)

3. **get_availability Tool**
   - Freebusy API integration for optimal performance
   - Working hours filtering (default 9AM-5PM, Mon-Fri)
   - Configurable working days and hours
   - Default date range (today to next week)
   - Multiple calendar support
   - Timezone handling with pytz
   - Duration calculation for free slots
   - Comprehensive parameter validation
   - 13 comprehensive tests, all passing with real API

4. **get_events Tool**
   - Flexible event retrieval: single event by ID or bulk queries
   - Date range filtering (default: today to next week)
   - Text-based search across event fields (summary, description)
   - Multiple calendar support with aggregated results
   - Configurable result limits and ordering (startTime/updated)
   - Complete event details: attendees, location, times, metadata
   - Error handling for invalid event IDs and parameters
   - 14 comprehensive tests, all passing with real API

5. **create_event Tool**
   - Agent-friendly event creation with 23 flattened parameters
   - Google Meet integration with automatic link generation
   - Attendee management (required and optional attendees)
   - Recurring events with RRULE pattern support
   - Custom reminders (email and popup) and notification control
   - All-day events, custom colors, and visibility settings
   - Comprehensive validation and error handling
   - 22 comprehensive tests with automatic cleanup

6. **delete_event Tool**
   - Clean event deletion with agent-friendly parameters
   - Smart error handling with force delete option
   - Attendee notification control (send/silent deletion)
   - Handles missing events, permission errors gracefully
   - Idempotent operations for reliable cleanup
   - 15 comprehensive tests with real API integration

### 🔄 Remaining Tools (1)
- update_event: Modify existing events

## Development Process Standards

### 1. Test-Driven Development (No Mocks)
- Write comprehensive tests first using real Google Calendar API
- Cover success, error, and edge cases with authentic API responses
- Use real service authentication for all test cases
- Follow TDD cycle: Red (failing tests) → Green (implement) → Refactor
- Tests should initially fail, then guide implementation development
- Update tests only if initial expectations were incorrect, not to make code pass

### 2. Implementation Flow (Test-Driven Development)
1. Consult Google Calendar API expert agent for guidance
2. Design tool interface and parameters with comprehensive documentation
3. Write comprehensive test cases using real Google Calendar API (no mocks)
4. Run tests to verify they fail as expected (TDD red phase)
5. Implement function logic to make tests pass (TDD green phase)
6. Run tests iteratively and refactor as needed (TDD refactor phase)
7. If tests fail: analyze if logic is wrong OR if test expectations need updating
8. Validate final implementation with real API testing
9. Document and move to next tool

**Note**: We do NOT use mocks in our testing approach. All tests use real Google Calendar API calls for authentic validation.

## Function Output Formats

All calendar tools return structured, predictable formats optimized for AI agent integration:

### 1. list_calendars() → List[Dict]
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
        "description": "Shared team events"
    }
]
```

### 2. get_availability() → Dict
```python
{
    "free_slots": [{"start": "...", "end": "...", "duration_minutes": 480}],
    "busy_periods": [{"start": "...", "end": "...", "calendar_id": "primary"}],
    "working_hours": {"start": 9, "end": 17, "days": [0,1,2,3,4]},
    "date_range": {"start": "...", "end": "..."}
}
```

### 3. get_events() → Dict
**Multiple events:**
```python
{
    "events": [...],  # Array of event objects
    "summary": {"total_events": 5, "max_results": 250, "order_by": "startTime"},
    "calendar_id": "primary",
    "date_range": {"start": "...", "end": "..."}
}
```
**Single event:** Returns event object directly with all fields.

### 4. Authentication Pattern
- OAuth 2.0 preferred over Service Account (better user calendar access)
- One-time consent flow with browser authorization
- Automatic token refresh handling
- Secure token storage with 600 permissions

### 5. Error Handling
- Comprehensive exception handling
- User-friendly error messages
- Network and API error resilience
- Graceful degradation

## Technical Specifications

### Dependencies
- `google-api-python-client==2.179.0`
- `python-dotenv>=1.0.0`
- `pytz>=2023.3`
- `pytest>=8.0.0` (test group)
- `pytest-asyncio>=1.0.0` (test group)

### Environment Variables
- `GOOGLE_CLIENT_ID`: OAuth client ID (preferred over client_secret.json)
- `GOOGLE_CLIENT_SECRET`: OAuth client secret (preferred over client_secret.json)
- `GOOGLE_USER_EMAIL`: Default email for authentication
- `EMAIL_FOR_TESTING`: Email for main.py testing

### Authentication Files
- `client_secret.json`: OAuth client credentials (fallback if env vars not set)
- `tokens/{email}_tokens.json`: Stored refresh tokens per user

## Key Decisions Made

1. **OAuth over Service Account**: Better access to user's actual calendars
2. **Individual tool functions**: More flexible than monolithic class
3. **Regex filtering**: Powerful calendar filtering with include/exclude modes
4. **Local server callback**: User-friendly OAuth flow
5. **Async-first design**: Native async support throughout
6. **Environment-first authentication**: Prefer .env over .json files for credentials
7. **Working hours filtering**: Application-level since Google Calendar API doesn't expose user working hours

## Testing Strategy
- Real API integration tests (no mocks)
- TDD approach: Red → Green → Refactor
- Comprehensive edge case coverage
- Error scenario testing
- Parameter validation testing

## Next Steps
Continue with remaining 4 calendar tools following the same TDD process and standards established for `list_calendars` and `get_availability`.

## Recent Completion: get_availability Tool

Successfully implemented `get_availability` tool (August 2025) with complete TDD methodology:

**Key Features Implemented:**
- Google Calendar Freebusy API integration for optimal availability checking
- Working hours filtering (configurable, defaults: 9AM-5PM Mon-Fri)
- Smart business logic: excludes weekends, respects working hours only
- Default behavior: today to next week when no parameters provided  
- Multiple calendar support with timezone handling (pytz)
- Comprehensive parameter validation with clear error messages
- ISO datetime parsing with 'Z' UTC suffix support

**Technical Achievement:**
- 13/13 tests passing with real Google Calendar API data
- Proper TDD cycle: Red (failing) → Green (implement) → Refactor
- Environment variable authentication (moved from client_secret.json)
- Duration calculation in minutes for each free slot
- Handles overlapping busy periods and complex scheduling scenarios

**Validation Results:** Successfully tested with real calendar data showing 7 busy periods and 4 available slots during working hours, with accurate 480-minute (8-hour) duration calculations.

## Recent Completion: get_events Tool

Successfully implemented `get_events` tool (August 2025) following established TDD methodology:

**Key Features Implemented:**
- Dual-mode operation: single event by ID or bulk event queries
- Google Calendar Events API integration with full parameter support  
- Comprehensive filtering: date range, text search, result limits, ordering
- Multi-calendar aggregation with standardized event format
- Complete event metadata: attendees, location, creator, organizer details
- Robust error handling for invalid IDs and parameter validation

**Technical Achievement:**
- 14/14 tests passing with real Google Calendar API data
- Hybrid approach: events.get() for single events, events.list() for bulk queries
- Smart parameter mapping and response normalization
- Handles recurring events, timezone conversions, and edge cases
- Flexible API supporting both AI agent patterns and direct usage

**Validation Results:** Successfully tested with real calendar events including single event retrieval, bulk queries with filtering, and complex recurring event scenarios.

## Recent Updates: Output Format Standardization & Project Cleanup

Successfully standardized output formats (August 2025) for better AI agent integration:

**Output Format Changes:**
- **list_calendars()**: Updated to return simplified list of dicts with `calendarId`, `calendarName`, `description` fields only
- **get_availability()**: Maintains existing well-structured dict format with `free_slots`, `busy_periods`, metadata
- **get_events()**: Maintains existing structured format (slight inconsistency between single/multiple remains)

**Project Structure Cleanup:**
- Cleaned root directory to contain only essential files: `main.py`, `README.md`, `pyproject.toml`, `uv.lock`
- Organized development files into proper directories: `examples/`, `docs/`, `memory/`
- Removed temporary development files: `check_output_formats.py`, `standardized_formats.py`, etc.
- Updated all tests to work with new `list_calendars` format

**Benefits Achieved:**
- Consistent, predictable output formats across all functions
- Clean, maintainable project structure  
- Simplified integration for AI agents
- Better separation of concerns (core vs examples vs documentation)

## Recent Completion: delete_event Tool & Clean Testing Pattern

Successfully implemented `delete_event` tool and solved calendar pollution in testing (August 2025):

**Key Features Implemented:**
- **Agent-Friendly Parameters**: Simple primitive types only (`event_id`, `calendar_id`, `send_notifications`, `force_delete`)
- **Smart Error Handling**: Graceful handling of 404/410 errors with `force_delete=True` option
- **Comprehensive Validation**: Parameter validation with clear error messages for missing/invalid inputs
- **Flexible Notification Control**: Boolean `send_notifications` mapped to Google API's `sendUpdates` format
- **Robust Delete Operations**: Handles already-deleted events, permission errors, and edge cases

**Technical Achievement:**
- 15/15 tests passing with real Google Calendar API integration
- Complete create-then-delete workflow validation with actual event lifecycle testing
- Error resilience for missing events, invalid calendars, and permission scenarios
- Force delete functionality for idempotent deletion operations

**Clean Testing Pattern Implemented:**
- **Zero Calendar Pollution**: All 22 create_event tests now use create-then-delete pattern
- **Automatic Cleanup**: `create_and_cleanup_event()` helper ensures events are deleted after tests
- **Guaranteed Cleanup**: `try/finally` blocks ensure deletion even if test assertions fail
- **Silent Operations**: Test cleanup uses `send_notifications=False` and `force_delete=True` for reliability

**Complete CRUD Operations Now Available:**
- ✅ **CREATE**: `create_event()` - Full-featured event creation with 23 agent-friendly parameters
- ✅ **READ**: `get_events()` - Single/bulk event retrieval with comprehensive filtering
- ✅ **DELETE**: `delete_event()` - Clean event deletion with error handling and force options

**Demo Integration Enhanced:**
- Updated demo script shows complete CRUD workflow with cleanup demonstration
- Four event types created, then systematically deleted for clean demonstration
- Force delete demonstration on already-deleted events
- Batch deletion patterns for multiple events

**Validation Results:** Successfully tested complete workflow with real Google Calendar API including event creation, Google Meet integration, recurring events, attendee management, and reliable cleanup deletion.