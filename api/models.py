"""
Pydantic request and response models for automotive voice agent API.
Simple, DRY models that match existing tool function signatures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# =============================================================================
# Base Response Model
# =============================================================================

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = True
    message: Optional[str] = None


# =============================================================================
# Calendar Tool Models
# =============================================================================

class ListCalendarsRequest(BaseModel):
    """Request model for list_calendars tool."""
    user_email: str = Field(..., description="User email for authentication")
    max_results: int = Field(100, ge=1, le=1000)
    show_hidden: bool = False
    query_strings: Optional[List[str]] = None
    query_string_to_include: bool = True


class GetAvailabilityRequest(BaseModel):
    """Request model for get_availability tool."""
    user_email: str = Field(..., description="User email for authentication")
    calendar_ids: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    working_hours_start: int = Field(9, ge=0, le=23)
    working_hours_end: int = Field(17, ge=0, le=23)
    working_days: Optional[List[int]] = None
    time_zone: Optional[str] = None


class GetEventsRequest(BaseModel):
    """Request model for get_events tool."""
    user_email: str = Field(..., description="User email for authentication")
    calendar_ids: Optional[List[str]] = None
    event_id: Optional[str] = None
    time_min: Optional[datetime] = None
    time_max: Optional[datetime] = None
    query: Optional[str] = None
    max_results: int = Field(250, ge=1, le=2500)
    order_by: str = Field("startTime", pattern="^(startTime|updated)$")
    show_deleted: bool = False
    time_zone: Optional[str] = None


class CreateEventRequest(BaseModel):
    """Request model for create_event tool."""
    user_email: str = Field(..., description="User email for authentication")
    calendar_id: str
    summary: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    all_day: bool = False
    attendees: Optional[List[str]] = None
    optional_attendees: Optional[List[str]] = None
    create_google_meet: bool = False
    send_notifications: str = Field("all", pattern="^(all|external|none)$")
    guests_can_invite_others: bool = True
    guests_can_modify: bool = False
    guests_can_see_others: bool = True
    visibility: str = Field("default", pattern="^(default|public|private|confidential)$")
    color_id: Optional[int] = Field(None, ge=1, le=24)
    recurrence_rule: Optional[str] = None
    email_reminder_minutes: Optional[int] = None
    popup_reminder_minutes: Optional[int] = None
    use_default_reminders: bool = True


class UpdateEventRequest(BaseModel):
    """Request model for update_event tool."""
    user_email: str = Field(..., description="User email for authentication")
    event_id: str
    calendar_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    all_day: Optional[bool] = None
    attendees: Optional[List[str]] = None
    optional_attendees: Optional[List[str]] = None
    attendee_action: str = Field("replace", pattern="^(replace|add|remove)$")
    create_google_meet: Optional[bool] = None
    remove_google_meet: bool = False
    send_notifications: str = Field("all", pattern="^(all|external_only|none)$")
    guests_can_invite_others: Optional[bool] = None
    guests_can_modify: Optional[bool] = None
    guests_can_see_others: Optional[bool] = None
    visibility: Optional[str] = Field(None, pattern="^(default|public|private)$")
    color_id: Optional[int] = Field(None, ge=1, le=24)
    status: Optional[str] = Field(None, pattern="^(confirmed|tentative|cancelled)$")
    recurrence_rule: Optional[str] = None
    remove_recurrence: bool = False
    recurring_update_scope: str = Field("single", pattern="^(single|all|following)$")
    email_reminder_minutes: Optional[int] = None
    popup_reminder_minutes: Optional[int] = None
    use_default_reminders: Optional[bool] = None
    clear_all_reminders: bool = False


class DeleteEventRequest(BaseModel):
    """Request model for delete_event tool."""
    user_email: str = Field(..., description="User email for authentication")
    event_id: str
    calendar_id: str = "primary"
    send_notifications: bool = True
    force_delete: bool = False


# =============================================================================
# Knowledge Base Tool Models
# =============================================================================

class FetchLatestKbRequest(BaseModel):
    """Request model for fetch_latest_kb tool."""
    github_raw_urls: List[str] = Field(..., min_length=1)
    cache_duration_minutes: int = Field(30, ge=1)
    max_file_size_mb: int = Field(10, ge=1)
    timeout_seconds: int = Field(30, ge=5)


class SyncKnowledgeBaseRequest(BaseModel):
    """Request model for sync_knowledge_base tool."""
    vapi_api_key: str
    knowledge_base_tool_id: str
    markdown_files: List[Dict[str, str]] = Field(..., min_length=1)
    file_name_prefix: str = "kb_"
    vapi_base_url: str = "https://api.vapi.ai"
    timeout_seconds: int = Field(30, ge=5)


# =============================================================================
# Inventory Tool Models
# =============================================================================

class CheckInventoryRequest(BaseModel):
    """Request model for check_inventory tool."""
    category: Optional[str] = Field(None, pattern="^(sedan|suv|truck|coupe)$")
    model_name: Optional[str] = None
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    features: Optional[List[str]] = None
    status: str = Field("available", pattern="^(available|sold|reserved|all)$")


class GetExpectedDeliveryDatesRequest(BaseModel):
    """Request model for get_expected_delivery_dates tool."""
    vehicle_id: str
    features: Optional[List[str]] = None


class GetPricesRequest(BaseModel):
    """Request model for get_prices tool."""
    query_type: str = Field("specific", pattern="^(specific|by_features)$")
    vehicle_id: Optional[str] = None
    inventory_id: Optional[str] = None
    features: Optional[List[str]] = None


class GetSimilarVehiclesRequest(BaseModel):
    """Request model for get_similar_vehicles tool."""
    reference_vehicle_id: str
    max_results: int = Field(5, ge=1, le=20)
    price_tolerance_percent: int = Field(20, ge=0, le=100)
    include_unavailable: bool = False


class GetVehicleDetailsRequest(BaseModel):
    """Request model for get_vehicle_details tool."""
    vehicle_id: Optional[str] = None
    inventory_id: Optional[str] = None
    include_pricing: bool = True
    include_similar: bool = False


# =============================================================================
# Response Models
# =============================================================================

class ToolResponse(BaseResponse):
    """Generic tool response wrapper."""
    data: Dict[str, Any]
    tool_name: str
    execution_time_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    services: Dict[str, str]
    tools_available: int
    timestamp: str

