"""Async Railway REST API client for managing environment variables."""

import os
import json
import aiohttp
import asyncio

class RailwayClient:
    """Async Railway API client following KISS principles."""
    
    def __init__(self):
        self._initialized = False
        self.token = None
        self.service_id = None
        self.environment_id = None
    
    def _ensure_initialized(self):
        """Lazy initialization of Railway credentials."""
        if self._initialized:
            return
        
        self.token = os.getenv('RAILWAY_TOKEN')
        self.service_id = os.getenv('RAILWAY_SERVICE_ID')
        self.environment_id = os.getenv('RAILWAY_ENVIRONMENT_ID')
        
        if not all([self.token, self.service_id, self.environment_id]):
            missing = [k for k, v in {
                'RAILWAY_TOKEN': self.token,
                'RAILWAY_SERVICE_ID': self.service_id,
                'RAILWAY_ENVIRONMENT_ID': self.environment_id
            }.items() if not v]
            raise ValueError(f"Missing Railway environment variables: {missing}")
        
        self._initialized = True
    
    async def update_variable(self, name, value):
        """Update environment variable via Railway API."""
        self._ensure_initialized()
        
        url = "https://backboard.railway.app/v2/variables"
        
        payload = {
            "serviceId": self.service_id,
            "environmentId": self.environment_id,
            "name": name,
            "value": value
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        print(f"Updated Railway variable: {name}")
                        return True
                    else:
                        print(f"Railway API error: {response.status}")
                        return False
                        
        except aiohttp.ClientError as e:
            print(f"Railway API request failed: {e}")
            return False
        except Exception as e:
            print(f"Railway API unexpected error: {e}")
            return False


# Global instance
railway_client = RailwayClient()