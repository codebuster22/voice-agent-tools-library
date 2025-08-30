"""Async Railway REST API client for managing environment variables."""

import os
import json
import time
import aiohttp
import asyncio
from logging_config import railway_api_logger

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
        
        # Log API call
        railway_api_logger.log_call(
            "update_variable",
            params={"name": name, "value_size": len(str(value))},
            level="debug"
        )
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        railway_api_logger.log_response(
                            "update_variable",
                            success=True,
                            response={"variable": name},
                            duration_ms=duration_ms
                        )
                        return True
                    else:
                        response_text = await response.text()
                        railway_api_logger.log_response(
                            "update_variable",
                            success=False,
                            error=f"HTTP {response.status}: {response_text[:200]}",
                            duration_ms=duration_ms
                        )
                        return False
                        
        except aiohttp.ClientError as e:
            duration_ms = (time.time() - start_time) * 1000
            railway_api_logger.log_response(
                "update_variable",
                success=False,
                error=f"Client error: {str(e)}",
                duration_ms=duration_ms
            )
            return False
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            railway_api_logger.log_response(
                "update_variable",
                success=False,
                error=f"Unexpected error: {str(e)}",
                duration_ms=duration_ms
            )
            return False


# Global instance
railway_client = RailwayClient()