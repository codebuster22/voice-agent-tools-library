#!/usr/bin/env python3
"""
Simple server entry point for automotive voice agent tools.
Runs FastAPI server exposing all 13 tools via HTTP endpoints.
"""

import os
import uvicorn
from api.app import create_app
from dotenv import load_dotenv
load_dotenv()

def main():
    """Start the FastAPI server."""
    # Get log level from environment variable, default to DEBUG
    log_level = os.getenv('LOG_LEVEL', 'DEBUG').lower()
    
    uvicorn.run(
        "api.app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=log_level,
        factory=True
    )

if __name__ == "__main__":
    main()
