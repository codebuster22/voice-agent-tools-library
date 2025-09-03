"""
Test configuration and fixtures for automotive voice agent tests.
Provides test environment setup for service account authentication.
"""

import os
import pytest
import asyncio

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_email():
    """Get test email from environment."""
    email = os.getenv('EMAIL_FOR_TESTING')
    if not email:
        pytest.skip("EMAIL_FOR_TESTING environment variable not set")
    return email


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their dependencies."""
    for item in items:
        # Mark tests that use real calendar services
        if "create_service" in item.nodeid or "get_availability" in item.nodeid:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure proper test environment setup."""
    # Verify required environment variables
    required_vars = ['GOOGLE_SERVICE_ACCOUNT_JSON']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")
    
    yield