"""
FastAPI application factory for automotive voice agent tools.
Simple, open endpoints with no authentication for MVP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Automotive Voice Agent API",
        description="Complete toolkit for car dealership voice agents",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Enable CORS for all origins (MVP - open access)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include all API routes
    app.include_router(router)
    
    return app

