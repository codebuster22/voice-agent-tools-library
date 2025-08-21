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
│   ├── get_availability.py    # 🔄 Planned
│   ├── get_events.py          # 🔄 Planned
│   ├── create_event.py        # 🔄 Planned
│   ├── update_event.py        # 🔄 Planned
│   └── delete_event.py        # 🔄 Planned
├── __init__.py                # Public exports
tests/
├── test_list_calendars.py     # ✅ 13 comprehensive tests
tokens/                        # OAuth token storage (gitignored)
```

## Progress Summary

### ✅ Completed
1. **Authentication System**
   - OAuth 2.0 with refresh token support
   - Local server callback flow (localhost:8080)
   - Automatic token refresh and secure storage
   - Email-based token management

2. **list_calendars Tool**
   - Basic calendar listing functionality
   - Optional parameters: `max_results`, `show_hidden`
   - Regex filtering: `query_strings`, `query_string_to_include`
   - Case-insensitive, multi-field search (summary, description, id)
   - 13 comprehensive tests covering all scenarios
   - Real API testing validated (30 calendars → 6 after filtering)

### 🔄 Remaining Tools (5)
- get_availability: Check free/busy status
- get_events: Fetch events from date range
- create_event: Create new calendar events
- update_event: Modify existing events
- delete_event: Remove calendar events

## Development Process Standards

### 1. Test-Driven Development
- Write comprehensive tests first
- Cover success, error, and edge cases
- Mock external dependencies
- Validate with real API calls

### 2. Implementation Flow
1. Consult Google Calendar API expert agent for guidance
2. Design tool interface and parameters
3. Write test cases with mock data
4. Implement function to pass tests
5. Test with real API
6. Document and move to next tool

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
- `pytest>=8.0.0` (test group)
- `pytest-asyncio>=1.0.0` (test group)

### Environment Variables
- `GOOGLE_USER_EMAIL`: Default email for authentication
- `EMAIL_FOR_TESTING`: Email for main.py testing

### Authentication Files
- `client_secret.json`: OAuth client credentials (desktop app type)
- `tokens/{email}_tokens.json`: Stored refresh tokens per user

## Key Decisions Made

1. **OAuth over Service Account**: Better access to user's actual calendars
2. **Individual tool functions**: More flexible than monolithic class
3. **Regex filtering**: Powerful calendar filtering with include/exclude modes
4. **Local server callback**: User-friendly OAuth flow
5. **Async-first design**: Native async support throughout

## Testing Strategy
- Unit tests with mocks for isolated testing
- Integration tests with real API for validation
- Comprehensive edge case coverage
- Error scenario testing

## Next Steps
Continue with remaining 5 calendar tools following the same development process and standards established for `list_calendars`.