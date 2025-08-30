"""Async in-memory token manager with Railway persistence."""

import os
import json
import asyncio
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .railway_client import railway_client


class TokenManager:
    """Thread-safe async token manager."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tokens = {}
        self._initialized = True
    
    def _load_from_env(self):
        """Load tokens from environment variable."""
        tokens_json = os.getenv('GOOGLE_TOKENS_JSON')
        if not tokens_json:
            print("No GOOGLE_TOKENS_JSON found")
            return
        
        try:
            token_data = json.loads(tokens_json)
            email = token_data.get('email')
            if email:
                self._tokens[email] = token_data
                print(f"Loaded tokens for {email}")
        except json.JSONDecodeError as e:
            print(f"Error loading tokens: {e}")
    
    def get_credentials(self, email):
        """Get Google credentials for email."""
        # Lazy load tokens if not already loaded
        if not self._tokens:
            self._load_from_env()
            
        token_data = self._tokens.get(email)
        if not token_data:
            return None
        
        # Parse expiry if available
        expiry = None
        if token_data.get('expiry'):
            from datetime import datetime
            import dateutil.parser
            expiry = dateutil.parser.parse(token_data['expiry'])
        
        return Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', []),
            expiry=expiry
        )
    
    async def refresh_and_persist(self, email, credentials):
        """Refresh token and update Railway environment."""
        try:
            # Refresh the token (sync operation from Google)
            credentials.refresh(Request())
            
            # Update memory
            if email in self._tokens:
                self._tokens[email].update({
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })
                
                # Update Railway environment
                updated_json = json.dumps(self._tokens[email], separators=(',', ':'))
                success = await railway_client.update_variable('GOOGLE_TOKENS_JSON', updated_json)
                
                if success:
                    print(f"Refreshed and persisted tokens for {email}")
                else:
                    print(f"Token refreshed but Railway update failed for {email}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False
    
    def has_tokens(self, email):
        """Check if tokens exist for email."""
        return email in self._tokens


# Global instance
token_manager = TokenManager()