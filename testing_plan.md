# API Testing Plan for Automotive Voice Agent

## Overview
This document outlines the comprehensive testing strategy for the FastAPI endpoints in the automotive voice agent system. The API provides 13 endpoints across calendar management, knowledge base, and inventory operations.

## Testing Architecture

### Test Structure
```
tests/api/
├── __init__.py
├── conftest.py                    # Shared fixtures and test configuration
├── test_health.py                  # Health check endpoint tests
├── test_calendar_endpoints.py      # Calendar-related endpoint tests
├── test_kb_endpoints.py            # Knowledge base endpoint tests
└── test_inventory_endpoints.py     # Inventory management endpoint tests
```

### Technology Stack
- **Test Framework**: pytest
- **HTTP Testing**: FastAPI TestClient
- **Real Services**: Actual Google Calendar API integration
- **Assertions**: pytest assertions
- **Fixtures**: pytest fixtures for reusable test components

## Testing Strategy

### 1. Integration Testing Approach
- Test each endpoint with real service integration
- Use actual Google Calendar API with service account
- Focus on request validation and real API responses
- Verify error handling with actual service errors

### 2. Full Integration Testing
- Test actual tool function execution for all endpoints
- Verify proper service initialization and state management
- Test request flow from API to tool functions with real services
- Validate logging and monitoring with real operations

### 3. Real Service Testing

#### All Services Use Real Implementation
- **Google Calendar Service**: Uses real Google Calendar API
  - Service account with domain-wide delegation
  - Tests actual authentication and permissions
  - Validates real API integration
  - Handles actual API rate limits gracefully

#### Real Services Benefits
- **Inventory Tools**: Use actual implementation with test data
- **Knowledge Base Tools**: Use real GitHub and VAPI integration
- **Test Isolation**: Each test manages its own test data
- **Real Errors**: Catch actual API errors and edge cases
- **Production-like**: Tests mirror production behavior exactly

## Test Categories

### 1. Functional Tests
- **Input Validation**: Verify request model validation
- **Business Logic**: Test endpoint-specific logic
- **Response Format**: Ensure correct ToolResponse structure
- **Data Transformation**: Verify list wrapping and data formatting

### 2. Error Handling Tests
- **400 Bad Request**: Invalid input parameters
- **403 Forbidden**: Permission-based errors (if applicable)
- **500 Internal Server Error**: Tool execution failures
- **503 Service Unavailable**: Service initialization failures

### 3. Performance Tests
- **Response Time**: Ensure < 1000ms for most endpoints
- **Concurrent Requests**: Test parallel request handling
- **Resource Usage**: Monitor memory and CPU during tests

### 4. Security Tests
- **Input Sanitization**: Test against injection attacks
- **Authentication**: Verify service account authentication (for calendar)
- **Data Privacy**: Ensure no sensitive data leakage in logs

## Test Fixtures

### Core Fixtures

```python
@pytest.fixture
def test_client():
    """FastAPI test client with real calendar service."""
    
@pytest.fixture
def test_calendar_id():
    """Test calendar ID for isolation."""
    
@pytest.fixture
def sample_event_data():
    """Common calendar event test data."""
    
@pytest.fixture
def sample_inventory_data():
    """Common inventory test data."""
    
@pytest.fixture
def mock_datetime():
    """Frozen datetime for consistent testing."""
```

### Environment Fixtures

```python
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = TEST_SERVICE_ACCOUNT
    os.environ['GOOGLE_USER_EMAIL'] = 'test@example.com'
    os.environ['VAPI_API_KEY'] = 'test-api-key'
```

## Test Data Management

### Test Data Categories
1. **Valid Data**: Correct format and values for success cases
2. **Boundary Data**: Edge values (min/max, empty strings)
3. **Invalid Data**: Incorrect types, missing required fields
4. **Malformed Data**: Invalid formats (dates, emails, etc.)

### Data Fixtures
- Use factory patterns for generating test data
- Maintain separate datasets for different test scenarios
- Version control test data with the tests

## CI/CD Integration

### Test Execution Pipeline
1. **Pre-commit**: Run linting and type checking
2. **Pull Request**: Run full test suite
3. **Merge to Main**: Run tests + coverage analysis
4. **Deployment**: Run smoke tests post-deployment

### Coverage Requirements
- **Minimum Coverage**: 80% overall
- **Critical Paths**: 95% for calendar operations
- **Error Paths**: 90% for all error scenarios

## Test Execution

### Local Development
```bash
# Run all API tests
uv run pytest tests/api/ -v

# Run specific test file
uv run pytest tests/api/test_calendar_endpoints.py -v

# Run with coverage
uv run pytest tests/api/ --cov=api --cov-report=html

# Run specific test
uv run pytest tests/api/test_calendar_endpoints.py::test_list_calendars_success -v
```

### Continuous Integration
```yaml
- name: Run API Tests
  run: |
    uv run pytest tests/api/ \
      --cov=api \
      --cov-report=xml \
      --cov-report=term \
      --junit-xml=test-results.xml
```

## Test Data Management with Real Services

### Calendar Test Data Strategy
```python
@pytest.fixture
async def test_calendar_cleanup():
    """Cleanup test events after each test."""
    created_events = []
    yield created_events
    
    # Cleanup: Delete all test events
    for event_id, calendar_id in created_events:
        await delete_event(service, event_id, calendar_id)

@pytest.fixture
async def create_test_event():
    """Create a test event for testing."""
    event_data = {
        "summary": f"TEST_EVENT_{uuid.uuid4()}",
        "start_time": datetime.now().isoformat(),
        "description": "Test event - safe to delete"
    }
    return await create_event(service, "primary", **event_data)
```

### Real Service Response Validation
```python
def validate_real_response(response):
    """Validate actual API response structure."""
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "execution_time_ms" in data
    assert data["execution_time_ms"] > 0
```

## Error Testing Strategy

### Systematic Error Testing
1. **Missing Required Fields**: Omit each required field individually
2. **Invalid Data Types**: Wrong type for each field
3. **Boundary Violations**: Values outside acceptable ranges
4. **Format Errors**: Invalid formats for dates, emails, etc.
5. **Business Rule Violations**: Invalid combinations of fields

### Error Response Validation
```python
def assert_error_response(response, status_code, error_substring):
    assert response.status_code == status_code
    assert error_substring in response.json()['detail']
```

## Performance Testing

### Response Time Benchmarks
- **Simple Queries**: < 200ms
- **Complex Operations**: < 500ms
- **Bulk Operations**: < 1000ms
- **Timeout Threshold**: 30 seconds

### Load Testing
```python
async def test_concurrent_requests():
    """Test handling of concurrent API requests."""
    tasks = [
        client.get("/api/v1/health") 
        for _ in range(100)
    ]
    responses = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in responses)
```

## Test Maintenance

### Best Practices
1. **Keep Tests Independent**: No shared state between tests
2. **Use Descriptive Names**: Clear test purpose from name
3. **Document Complex Tests**: Add docstrings for complex scenarios
4. **Regular Cleanup**: Remove obsolete tests
5. **Update with API Changes**: Keep tests synchronized with API

### Test Review Checklist
- [ ] All endpoints have basic success tests
- [ ] All required parameters have validation tests
- [ ] Error scenarios are covered
- [ ] Response format is validated
- [ ] Performance benchmarks are met
- [ ] Mocks are properly isolated
- [ ] Test data is appropriate
- [ ] Documentation is updated

## Monitoring & Reporting

### Test Metrics
- **Test Count**: Total number of tests
- **Pass Rate**: Percentage of passing tests
- **Coverage**: Code coverage percentage
- **Execution Time**: Total test suite runtime
- **Flaky Tests**: Tests with intermittent failures

### Reporting Tools
- **pytest-html**: HTML test reports
- **pytest-cov**: Coverage reports
- **allure**: Comprehensive test reporting
- **pytest-json**: JSON output for CI integration

## Future Enhancements

### Planned Improvements
1. **Contract Testing**: Validate API contracts with consumers
2. **Property-Based Testing**: Use hypothesis for generative testing
3. **Mutation Testing**: Verify test quality with mutmut
4. **API Versioning Tests**: Support multiple API versions
5. **Performance Profiling**: Detailed performance analysis

### Long-term Goals
- Achieve 95% code coverage
- Reduce test execution time to < 1 minute
- Implement automated regression testing
- Add visual regression testing for responses
- Create test data generation utilities