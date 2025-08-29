"""
VAPI integration configuration settings.
Simple environment variable based configuration for VAPI SDK.
"""

import os
from typing import Optional


class VapiSettings:
    """VAPI configuration settings loaded from environment variables."""
    
    def __init__(self):
        self.vapi_api_token: str = os.getenv("VAPI_API_TOKEN", "")
        self.server_base_url: str = os.getenv("SERVER_BASE_URL", "http://localhost:8000")
        self.vapi_webhook_secret: Optional[str] = os.getenv("VAPI_WEBHOOK_SECRET")
        
        if not self.vapi_api_token:
            raise ValueError("VAPI_API_TOKEN environment variable is required")
    
    @property
    def webhook_url(self) -> str:
        """Full webhook URL for VAPI tool calls."""
        return f"{self.server_base_url}/vapi/tool-call"


# Global settings instance
vapi_settings = VapiSettings()