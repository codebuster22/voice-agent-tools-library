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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - runs on startup and shutdown."""
    # Startup: Initialize Google Calendar authentication
    print("🚀 Starting automotive voice agent server...")
    
    # Initialize Google Calendar auth on startup
    try:
        print("🔐 Initializing Google Calendar authentication...")
        from calendar_tools.auth import create_service
        
        email = os.getenv('GOOGLE_USER_EMAIL')
        if email:
            service = await create_service(email)
            print(f"✅ Google Calendar authenticated for {email}")
            
            # Store service in app state for reuse
            app.state.calendar_service = service
            app.state.calendar_email = email
        else:
            print("⚠️  GOOGLE_USER_EMAIL not set - calendar tools will require manual auth")
            
    except Exception as e:
        print(f"⚠️  Google Calendar auth failed: {e}")
        print("📝 Calendar tools may require manual authentication")
    
    print("✅ Server startup complete")
    yield
    
    # Shutdown
    print("👋 Shutting down automotive voice agent server...")


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

