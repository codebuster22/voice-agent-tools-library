"""
FastAPI routes for automotive voice agent tools.
Simple, DRY endpoints that directly wrap existing tool functions.
"""

import time
from fastapi import APIRouter, HTTPException
from datetime import datetime

# Import tool functions
from calendar_tools import create_service
from calendar_tools.tools import (
    list_calendars, get_availability, get_events, 
    create_event, update_event, delete_event
)
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
    
    try:
        data = await tool_func(**kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        return ToolResponse(
            success=True,
            data=data,
            tool_name=tool_name,
            execution_time_ms=round(execution_time, 2)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{tool_name} failed: {str(e)}")


async def get_calendar_service(user_email: str):
    """Get authenticated calendar service for user."""
    try:
        return await create_service(user_email)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Calendar authentication failed: {str(e)}")


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
async def list_calendars_endpoint(request: ListCalendarsRequest):
    """List Google Calendar calendars."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "list_calendars",
        list_calendars,
        service=service,
        max_results=request.max_results,
        show_hidden=request.show_hidden,
        query_strings=request.query_strings,
        query_string_to_include=request.query_string_to_include
    )


@router.post("/calendar/get-availability", response_model=ToolResponse)
async def get_availability_endpoint(request: GetAvailabilityRequest):
    """Get calendar availability."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "get_availability",
        get_availability,
        service=service,
        calendar_ids=request.calendar_ids,
        start_time=request.start_time,
        end_time=request.end_time,
        working_hours_start=request.working_hours_start,
        working_hours_end=request.working_hours_end,
        working_days=request.working_days,
        time_zone=request.time_zone
    )


@router.post("/calendar/get-events", response_model=ToolResponse)
async def get_events_endpoint(request: GetEventsRequest):
    """Get calendar events."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "get_events",
        get_events,
        service=service,
        calendar_ids=request.calendar_ids,
        event_id=request.event_id,
        time_min=request.time_min,
        time_max=request.time_max,
        query=request.query,
        max_results=request.max_results,
        order_by=request.order_by,
        show_deleted=request.show_deleted,
        time_zone=request.time_zone
    )


@router.post("/calendar/create-event", response_model=ToolResponse)
async def create_event_endpoint(request: CreateEventRequest):
    """Create calendar event."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "create_event",
        create_event,
        service=service,
        calendar_id=request.calendar_id,
        summary=request.summary,
        start_time=request.start_time,
        end_time=request.end_time,
        description=request.description,
        location=request.location,
        timezone=request.timezone,
        all_day=request.all_day,
        attendees=request.attendees,
        optional_attendees=request.optional_attendees,
        create_google_meet=request.create_google_meet,
        send_notifications=request.send_notifications,
        guests_can_invite_others=request.guests_can_invite_others,
        guests_can_modify=request.guests_can_modify,
        guests_can_see_others=request.guests_can_see_others,
        visibility=request.visibility,
        color_id=request.color_id,
        recurrence_rule=request.recurrence_rule,
        email_reminder_minutes=request.email_reminder_minutes,
        popup_reminder_minutes=request.popup_reminder_minutes,
        use_default_reminders=request.use_default_reminders
    )


@router.post("/calendar/update-event", response_model=ToolResponse)
async def update_event_endpoint(request: UpdateEventRequest):
    """Update calendar event."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "update_event",
        update_event,
        service=service,
        event_id=request.event_id,
        calendar_id=request.calendar_id,
        summary=request.summary,
        description=request.description,
        location=request.location,
        start_time=request.start_time,
        end_time=request.end_time,
        timezone=request.timezone,
        all_day=request.all_day,
        attendees=request.attendees,
        optional_attendees=request.optional_attendees,
        attendee_action=request.attendee_action,
        create_google_meet=request.create_google_meet,
        remove_google_meet=request.remove_google_meet,
        send_notifications=request.send_notifications,
        guests_can_invite_others=request.guests_can_invite_others,
        guests_can_modify=request.guests_can_modify,
        guests_can_see_others=request.guests_can_see_others,
        visibility=request.visibility,
        color_id=request.color_id,
        status=request.status,
        recurrence_rule=request.recurrence_rule,
        remove_recurrence=request.remove_recurrence,
        recurring_update_scope=request.recurring_update_scope,
        email_reminder_minutes=request.email_reminder_minutes,
        popup_reminder_minutes=request.popup_reminder_minutes,
        use_default_reminders=request.use_default_reminders,
        clear_all_reminders=request.clear_all_reminders
    )


@router.post("/calendar/delete-event", response_model=ToolResponse)
async def delete_event_endpoint(request: DeleteEventRequest):
    """Delete calendar event."""
    service = await get_calendar_service(request.user_email)
    
    return await create_tool_response(
        "delete_event",
        delete_event,
        service=service,
        event_id=request.event_id,
        calendar_id=request.calendar_id,
        send_notifications=request.send_notifications,
        force_delete=request.force_delete
    )


# =============================================================================
# Knowledge Base Tool Endpoints
# =============================================================================

@router.post("/knowledge-base/fetch-latest", response_model=ToolResponse)
async def fetch_latest_kb_endpoint(request: FetchLatestKbRequest):
    """Fetch latest knowledge base from GitHub."""
    return await create_tool_response(
        "fetch_latest_kb",
        fetch_latest_kb,
        github_raw_urls=request.github_raw_urls,
        cache_duration_minutes=request.cache_duration_minutes,
        max_file_size_mb=request.max_file_size_mb,
        timeout_seconds=request.timeout_seconds
    )


@router.post("/knowledge-base/sync", response_model=ToolResponse)
async def sync_knowledge_base_endpoint(request: SyncKnowledgeBaseRequest):
    """Sync knowledge base with Vapi."""
    return await create_tool_response(
        "sync_knowledge_base",
        sync_knowledge_base,
        vapi_api_key=request.vapi_api_key,
        knowledge_base_tool_id=request.knowledge_base_tool_id,
        markdown_files=request.markdown_files,
        file_name_prefix=request.file_name_prefix,
        vapi_base_url=request.vapi_base_url,
        timeout_seconds=request.timeout_seconds
    )


# =============================================================================
# Inventory Tool Endpoints
# =============================================================================

@router.post("/inventory/check-inventory", response_model=ToolResponse)
async def check_inventory_endpoint(request: CheckInventoryRequest):
    """Check vehicle inventory."""
    return await create_tool_response(
        "check_inventory",
        check_inventory,
        category=request.category,
        model_name=request.model_name,
        min_price=request.min_price,
        max_price=request.max_price,
        features=request.features,
        status=request.status
    )


@router.post("/inventory/get-delivery-dates", response_model=ToolResponse)
async def get_delivery_dates_endpoint(request: GetExpectedDeliveryDatesRequest):
    """Get expected delivery dates."""
    return await create_tool_response(
        "get_expected_delivery_dates",
        get_expected_delivery_dates,
        vehicle_id=request.vehicle_id,
        features=request.features
    )


@router.post("/inventory/get-prices", response_model=ToolResponse)
async def get_prices_endpoint(request: GetPricesRequest):
    """Get vehicle prices."""
    return await create_tool_response(
        "get_prices",
        get_prices,
        query_type=request.query_type,
        vehicle_id=request.vehicle_id,
        inventory_id=request.inventory_id,
        features=request.features
    )


@router.post("/inventory/get-similar-vehicles", response_model=ToolResponse)
async def get_similar_vehicles_endpoint(request: GetSimilarVehiclesRequest):
    """Get similar vehicles."""
    return await create_tool_response(
        "get_similar_vehicles",
        get_similar_vehicles,
        reference_vehicle_id=request.reference_vehicle_id,
        max_results=request.max_results,
        price_tolerance_percent=request.price_tolerance_percent,
        include_unavailable=request.include_unavailable
    )


@router.post("/inventory/get-vehicle-details", response_model=ToolResponse)
async def get_vehicle_details_endpoint(request: GetVehicleDetailsRequest):
    """Get vehicle details."""
    return await create_tool_response(
        "get_vehicle_details",
        get_vehicle_details,
        vehicle_id=request.vehicle_id,
        inventory_id=request.inventory_id,
        include_pricing=request.include_pricing,
        include_similar=request.include_similar
    )

