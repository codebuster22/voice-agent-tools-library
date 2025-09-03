"""
FastAPI routes for automotive voice agent tools.
Simple, DRY endpoints that directly wrap existing tool functions.
"""

import time
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from logging_config import logger

# Import tool functions
from calendar_tools import create_service
from calendar_tools.tools.list_calendars import list_calendars
from calendar_tools.tools.get_availability import get_availability
from calendar_tools.tools.get_events import get_events
from calendar_tools.tools.create_event import create_event
from calendar_tools.tools.update_event import update_event
from calendar_tools.tools.delete_event import delete_event
from calendar_tools.tools.create_appointment import create_appointment
from kb_tools import fetch_latest_kb, sync_knowledge_base
from inventory import (
    check_inventory, get_expected_delivery_dates, get_prices,
    get_similar_vehicles, get_vehicle_details
)

# Import request/response models
from .models import (
    # Calendar models
    ListCalendarsRequest, GetAvailabilityRequest, GetEventsRequest,
    CreateEventRequest, UpdateEventRequest, DeleteEventRequest,
    # KB models
    FetchLatestKbRequest, SyncKnowledgeBaseRequest,
    # Inventory models
    CheckInventoryRequest, GetExpectedDeliveryDatesRequest, GetPricesRequest,
    GetSimilarVehiclesRequest, GetVehicleDetailsRequest,
    # Response models
    ToolResponse, HealthResponse
)

# Create router
router = APIRouter(prefix="/api/v1")


# =============================================================================
# Helper Functions
# =============================================================================

async def create_tool_response(tool_name: str, tool_func, **kwargs) -> ToolResponse:
    """Generic wrapper for tool functions with timing and error handling."""
    start_time = time.time()
    
    # Log tool execution start
    logger.info(f"Executing tool: {tool_name}", tool_name=tool_name, operation="start")
    
    # Debug level: log parameters
    if kwargs:
        # Filter out sensitive data and large objects
        debug_kwargs = {}
        for key, value in kwargs.items():
            if key in ['service', 'credentials']:
                debug_kwargs[key] = f"<{type(value).__name__}>"
            elif isinstance(value, str) and len(value) > 100:
                debug_kwargs[key] = f"{value[:50]}... ({len(value)} chars)"
            else:
                debug_kwargs[key] = value
        
        logger.debug(f"Tool parameters for {tool_name}", tool_name=tool_name, params=debug_kwargs)
    
    try:
        data = await tool_func(**kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        # Log successful execution
        logger.info(
            f"Tool completed successfully: {tool_name}",
            tool_name=tool_name,
            operation="success",
            duration_ms=round(execution_time, 2),
            result_type=type(data).__name__
        )
        
        # Debug level: log result size/preview
        if isinstance(data, list):
            logger.debug(
                f"Tool result details for {tool_name}",
                tool_name=tool_name,
                result_count=len(data),
                result_preview=data[:2] if len(data) > 0 else []
            )
        elif isinstance(data, dict):
            logger.debug(
                f"Tool result details for {tool_name}",
                tool_name=tool_name,
                result_keys=list(data.keys())[:10] if data else [],
                result_size=len(str(data))
            )
        
        # Wrap list results in a dict for ToolResponse compatibility
        if isinstance(data, list):
            data = {"items": data}
        
        return ToolResponse(
            success=True,
            data=data,
            tool_name=tool_name,
            execution_time_ms=round(execution_time, 2)
        )
        
    except ValueError as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(
            f"Tool validation error: {tool_name}",
            tool_name=tool_name,
            operation="validation_error",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(execution_time, 2)
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(
            f"Tool execution failed: {tool_name}",
            tool_name=tool_name,
            operation="error",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(execution_time, 2)
        )
        raise HTTPException(status_code=500, detail=f"{tool_name} failed: {str(e)}")


async def get_calendar_service(user_email: str = None, request: Request = None):
    """Get the shared calendar service from app state."""
    logger.debug("Getting shared calendar service")
    
    try:
        # Get the pre-initialized service from app state
        calendar_service = request.app.state.calendar_service
        calendar_email = request.app.state.calendar_email
        
        if not calendar_service:
            logger.error("Calendar service not initialized - check server startup logs")
            raise HTTPException(status_code=503, detail="Calendar service not available - server initialization failed")
        
        # Log which email this service is configured for (informational)
        if user_email and user_email != calendar_email:
            logger.warning("Requested email differs from configured email", 
                         requested=user_email, configured=calendar_email)
        
        logger.debug("Using shared calendar service", email=calendar_email)
        return calendar_service
        
    except AttributeError:
        logger.error("App state not properly initialized - calendar service missing")
        raise HTTPException(status_code=503, detail="Calendar service not available - app state not initialized")


# =============================================================================
# Health Check Endpoint
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        services={
            "database": "connected",
            "google_calendar": "available", 
            "vapi": "available"
        },
        tools_available=13,
        timestamp=datetime.now().isoformat()
    )


# =============================================================================
# Calendar Tool Endpoints
# =============================================================================

@router.post("/calendar/list-calendars", response_model=ToolResponse)
async def list_calendars_endpoint(request_data: ListCalendarsRequest, request: Request):
    """List Google Calendar calendars."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "list_calendars",
        list_calendars,
        service=service,
        max_results=request_data.max_results,
        show_hidden=request_data.show_hidden,
        query_strings=request_data.query_strings,
        query_string_to_include=request_data.query_string_to_include
    )


@router.post("/calendar/get-availability", response_model=ToolResponse)
async def get_availability_endpoint(request_data: GetAvailabilityRequest, request: Request):
    """Get calendar availability."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "get_availability",
        get_availability,
        service=service,
        calendar_ids=request_data.calendar_ids,
        start_time=request_data.start_time,
        end_time=request_data.end_time,
        working_hours_start=request_data.working_hours_start,
        working_hours_end=request_data.working_hours_end,
        working_days=request_data.working_days,
        time_zone=request_data.time_zone
    )


@router.post("/calendar/get-events", response_model=ToolResponse)
async def get_events_endpoint(request_data: GetEventsRequest, request: Request):
    """Get calendar events."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "get_events",
        get_events,
        service=service,
        calendar_ids=request_data.calendar_ids,
        event_id=request_data.event_id,
        time_min=request_data.time_min,
        time_max=request_data.time_max,
        query=request_data.query,
        max_results=request_data.max_results,
        order_by=request_data.order_by,
        show_deleted=request_data.show_deleted,
        time_zone=request_data.time_zone
    )


@router.post("/calendar/create-event", response_model=ToolResponse)
async def create_event_endpoint(request_data: CreateEventRequest, request: Request):
    """Create simple 30-minute customer appointment."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "create_appointment",
        create_appointment,
        service=service,
        calendar_id=request_data.calendar_id,
        summary=request_data.summary,
        start_time=request_data.start_time,
        customer_email=request_data.customer_email,
        description=request_data.description,
        location=request_data.location
    )


@router.post("/calendar/update-event", response_model=ToolResponse)
async def update_event_endpoint(request_data: UpdateEventRequest, request: Request):
    """Update calendar event."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "update_event",
        update_event,
        service=service,
        event_id=request_data.event_id,
        calendar_id=request_data.calendar_id,
        summary=request_data.summary,
        description=request_data.description,
        location=request_data.location,
        start_time=request_data.start_time,
        end_time=request_data.end_time,
        timezone=request_data.timezone,
        all_day=request_data.all_day,
        attendees=request_data.attendees,
        optional_attendees=request_data.optional_attendees,
        attendee_action=request_data.attendee_action,
        create_google_meet=request_data.create_google_meet,
        remove_google_meet=request_data.remove_google_meet,
        send_notifications=request_data.send_notifications,
        guests_can_invite_others=request_data.guests_can_invite_others,
        guests_can_modify=request_data.guests_can_modify,
        guests_can_see_others=request_data.guests_can_see_others,
        visibility=request_data.visibility,
        color_id=request_data.color_id,
        status=request_data.status,
        recurrence_rule=request_data.recurrence_rule,
        remove_recurrence=request_data.remove_recurrence,
        recurring_update_scope=request_data.recurring_update_scope,
        email_reminder_minutes=request_data.email_reminder_minutes,
        popup_reminder_minutes=request_data.popup_reminder_minutes,
        use_default_reminders=request_data.use_default_reminders,
        clear_all_reminders=request_data.clear_all_reminders
    )


@router.post("/calendar/delete-event", response_model=ToolResponse)
async def delete_event_endpoint(request_data: DeleteEventRequest, request: Request):
    """Delete calendar event."""
    service = await get_calendar_service(None, request)
    
    return await create_tool_response(
        "delete_event",
        delete_event,
        service=service,
        event_id=request_data.event_id,
        calendar_id=request_data.calendar_id,
        send_notifications=request_data.send_notifications,
        force_delete=request_data.force_delete
    )


# =============================================================================
# Knowledge Base Tool Endpoints
# =============================================================================

@router.post("/knowledge-base/fetch-latest", response_model=ToolResponse)
async def fetch_latest_kb_endpoint(request_data: FetchLatestKbRequest):
    """Fetch latest knowledge base from GitHub using server configuration."""
    return await create_tool_response(
        "fetch_latest_kb",
        fetch_latest_kb
    )


@router.post("/knowledge-base/sync", response_model=ToolResponse)
async def sync_knowledge_base_endpoint(request_data: SyncKnowledgeBaseRequest):
    """Sync knowledge base with VAPI using server configuration."""
    return await create_tool_response(
        "sync_knowledge_base",
        sync_knowledge_base
    )


# =============================================================================
# Inventory Tool Endpoints
# =============================================================================

@router.post("/inventory/check-inventory", response_model=ToolResponse)
async def check_inventory_endpoint(request_data: CheckInventoryRequest):
    """Check vehicle inventory."""
    return await create_tool_response(
        "check_inventory",
        check_inventory,
        category=request_data.category,
        model_name=request_data.model_name,
        min_price=request_data.min_price,
        max_price=request_data.max_price,
        features=request_data.features,
        status=request_data.status
    )


@router.post("/inventory/get-delivery-dates", response_model=ToolResponse)
async def get_delivery_dates_endpoint(request_data: GetExpectedDeliveryDatesRequest):
    """Get expected delivery dates."""
    return await create_tool_response(
        "get_expected_delivery_dates",
        get_expected_delivery_dates,
        vehicle_id=request_data.vehicle_id,
        features=request_data.features
    )


@router.post("/inventory/get-prices", response_model=ToolResponse)
async def get_prices_endpoint(request_data: GetPricesRequest):
    """Get vehicle prices."""
    return await create_tool_response(
        "get_prices",
        get_prices,
        query_type=request_data.query_type,
        vehicle_id=request_data.vehicle_id,
        inventory_id=request_data.inventory_id,
        features=request_data.features
    )


@router.post("/inventory/get-similar-vehicles", response_model=ToolResponse)
async def get_similar_vehicles_endpoint(request_data: GetSimilarVehiclesRequest):
    """Get similar vehicles."""
    return await create_tool_response(
        "get_similar_vehicles",
        get_similar_vehicles,
        reference_vehicle_id=request_data.reference_vehicle_id,
        max_results=request_data.max_results,
        price_tolerance_percent=request_data.price_tolerance_percent,
        include_unavailable=request_data.include_unavailable
    )


@router.post("/inventory/get-vehicle-details", response_model=ToolResponse)
async def get_vehicle_details_endpoint(request_data: GetVehicleDetailsRequest):
    """Get vehicle details."""
    return await create_tool_response(
        "get_vehicle_details",
        get_vehicle_details,
        vehicle_id=request_data.vehicle_id,
        inventory_id=request_data.inventory_id,
        include_pricing=request_data.include_pricing,
        include_similar=request_data.include_similar
    )

