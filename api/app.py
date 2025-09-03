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
    
    # Startup: Initialize Google Calendar service (single instance for all requests)
    
    # Create calendar service for the configured email
    try:
        logger.info("Initializing calendar service")
        from calendar_tools.auth import create_service
        
        # Get the email that will be used for all calendar operations
        email = os.getenv('GOOGLE_USER_EMAIL')
        if not email:
            logger.error("GOOGLE_USER_EMAIL environment variable is required")
            raise ValueError("GOOGLE_USER_EMAIL environment variable must be set")
        
        # Create the calendar service (authenticates with service account)
        logger.info("Creating calendar service for production use", email=email)
        calendar_service = await create_service(email)
        
        # Store service in app state for reuse across all requests
        app.state.calendar_service = calendar_service
        app.state.calendar_email = email
        
        logger.info("Calendar service initialized successfully", email=email)
        
    except Exception as e:
        logger.error("Calendar service initialization failed", error=str(e), error_type=type(e).__name__)
        # Don't store anything in app.state on failure
        app.state.calendar_service = None
        app.state.calendar_email = None
        logger.error("Server will not be able to handle calendar requests")
    
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

