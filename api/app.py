"""
FastAPI application factory for automotive voice agent tools.
Simple, open endpoints with no authentication for MVP.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from logging_config import configure_logging, logger
from middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - runs on startup and shutdown."""
    # Configure logging first
    configure_logging()
    logger.info("Starting automotive voice agent server")
    
    # Startup: Initialize Google Calendar authentication
    
    # Initialize Google Calendar auth on startup
    try:
        logger.info("Initializing Google Calendar authentication")
        from calendar_tools.auth import create_service
        
        email = os.getenv('GOOGLE_USER_EMAIL')
        if email:
            service = await create_service(email)
            logger.info("Google Calendar authenticated", email=email)
            
            # Store service in app state for reuse
            app.state.calendar_service = service
            app.state.calendar_email = email
        else:
            logger.warning("GOOGLE_USER_EMAIL not set - calendar tools will require manual auth")
            
    except Exception as e:
        logger.error("Google Calendar auth failed", error=str(e), error_type=type(e).__name__)
        logger.warning("Calendar tools may require manual authentication")
    
    logger.info("Server startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down automotive voice agent server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Automotive Voice Agent API",
        description="Complete toolkit for car dealership voice agents",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add logging middleware (before CORS for proper request tracking)
    app.add_middleware(LoggingMiddleware)
    
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

