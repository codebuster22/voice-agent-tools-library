"""
Google Calendar service authentication using service account.
Provides domain-wide delegation to access user calendars.
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from logging_config import logger

# Load environment variables
load_dotenv()

# Google Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]


async def create_service(email: str = None) -> build:
    """
    Create authenticated Google Calendar service using service account.
    
    Args:
        email: User email address to impersonate (optional, falls back to env variable)
        
    Returns:
        Authenticated Google Calendar service
        
    Raises:
        ValueError: If no email provided and GOOGLE_USER_EMAIL not set
        Exception: If service account credentials not found or service creation fails
    """
    # Determine email to impersonate
    if not email:
        email = os.getenv('GOOGLE_USER_EMAIL')
        if not email:
            raise ValueError("Email must be provided either as parameter or in GOOGLE_USER_EMAIL env variable")
    
    logger.info("Creating calendar service with service account", email=email)
    
    # Get service account credentials from environment
    sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not sa_json:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
    
    try:
        # Parse service account JSON
        sa_info = json.loads(sa_json)
        
        # Create credentials with domain-wide delegation
        credentials = service_account.Credentials.from_service_account_info(
            sa_info, 
            scopes=SCOPES
        ).with_subject(email)  # Impersonate the specified user
        
        # Build and return the calendar service
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        
        logger.info("Calendar service created successfully", email=email)
        return service
        
    except json.JSONDecodeError as e:
        logger.error("Invalid service account JSON", error=str(e))
        raise Exception("Invalid GOOGLE_SERVICE_ACCOUNT_JSON format")
    except Exception as e:
        logger.error("Failed to create calendar service", email=email, error=str(e))
        raise