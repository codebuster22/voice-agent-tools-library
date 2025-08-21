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
calendar_tools/
├── auth.py                    # OAuth 2.0 authentication
├── tools/
│   ├── list_calendars.py      # ✅ Complete with regex filtering
│   ├── get_availability.py    # ✅ Complete with working hours filtering
│   ├── get_events.py          # 🔄 Planned
│   ├── create_event.py        # 🔄 Planned
│   ├── update_event.py        # 🔄 Planned
│   └── delete_event.py        # 🔄 Planned
├── __init__.py                # Public exports
tests/
├── test_list_calendars.py     # ✅ 13 comprehensive tests
├── test_get_availability.py   # ✅ 13 comprehensive tests
tokens/                        # OAuth token storage (gitignored)
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

### 🔄 Remaining Tools (4)
- get_events: Fetch events from date range
- create_event: Create new calendar events
- update_event: Modify existing events
- delete_event: Remove calendar events

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

### 3. Authentication Pattern
- OAuth 2.0 preferred over Service Account (better user calendar access)
- One-time consent flow with browser authorization
- Automatic token refresh handling
- Secure token storage with 600 permissions

### 4. Error Handling
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