#!/usr/bin/env python3
"""
Simple server entry point for automotive voice agent tools.
Runs FastAPI server exposing all 13 tools via HTTP endpoints.
"""

import uvicorn
from api.app import create_app
from dotenv import load_dotenv
load_dotenv()

def main():
    """Start the FastAPI server."""
    uvicorn.run(
        "api.app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        factory=True
    )

if __name__ == "__main__":
    main()
