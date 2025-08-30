"""
VAPI tool manager for registering automotive dealership tools.
Handles programmatic registration of all 13 tools using VAPI SDK with correct DTO format.
"""

import json
from typing import List, Dict, Any, Optional
from vapi import Vapi
from vapi.types.create_function_tool_dto import CreateFunctionToolDto
from vapi.types.open_ai_function import OpenAiFunction
from vapi.types.server import Server
from vapi.types.create_assistant_dto import CreateAssistantDto
from vapi.types.assistant_voice import AssistantVoice
from vapi.types.eleven_labs_voice import ElevenLabsVoice
from config.vapi_settings import vapi_settings


class VapiToolManager:
    """Manager for registering automotive tools with VAPI using correct DTO format."""
    
    def __init__(self, api_token: Optional[str] = None, server_base_url: Optional[str] = None):
        """Initialize VAPI tool manager."""
        self.api_token = api_token or vapi_settings.vapi_api_token
        self.server_base_url = server_base_url or vapi_settings.server_base_url
        self.client = Vapi(token=self.api_token)
    
    def get_inventory_tools(self) -> List[CreateFunctionToolDto]:
        """Get all 5 inventory management tools as DTO objects."""
        return [
            # 1. Check Vehicle Inventory
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="check_vehicle_inventory",
                    description="Search dealership inventory for available vehicles matching customer criteria including category, price range, model, features, and availability status. Perfect for helping customers find vehicles that meet their specific needs and preferences.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["sedan", "suv", "truck", "coupe"],
                                "description": "Vehicle category type customer is interested in (sedan for family cars, SUV for space and versatility, truck for hauling, coupe for style)"
                            },
                            "model_name": {
                                "type": "string",
                                "description": "Specific car model name if mentioned by customer (e.g., 'Toyota Camry', 'Honda CR-V', 'Ford F-150')"
                            },
                            "min_price": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Minimum price customer is willing to pay in dollars"
                            },
                            "max_price": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Maximum price customer wants to spend in dollars"
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Desired vehicle features like 'leather seats', 'sunroof', 'AWD', 'navigation', 'backup camera', 'heated seats'"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["available", "sold", "reserved", "all"],
                                "default": "available",
                                "description": "Vehicle availability status filter - use 'available' for customers looking to buy"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/check-inventory")
            ),
            
            # 2. Get Vehicle Delivery Dates
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_delivery_dates",
                    description="Get expected delivery date ranges for a specific vehicle showing earliest and latest availability across all inventory. Provides realistic delivery timelines to help customers plan their purchase and set proper expectations.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Vehicle ID to get delivery date ranges for (UUID format)"
                            }
                        },
                        "required": ["vehicle_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-delivery-dates")
            ),
            
            # 3. Get Vehicle Pricing
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_pricing",
                    description="Get comprehensive pricing information for vehicles including base price, feature costs, taxes, fees, and total pricing. Supports both specific vehicle pricing and estimated pricing based on desired features.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["specific", "by_features"],
                                "default": "specific",
                                "description": "Type of pricing query - 'specific' for exact vehicle/inventory pricing, 'by_features' for estimated pricing based on desired features"
                            },
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Vehicle ID for base pricing information"
                            },
                            "inventory_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Specific inventory item ID for exact pricing of a particular car on the lot"
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Additional features customer wants to add for pricing calculation"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-prices")
            ),
            
            # 4. Find Similar Vehicles
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="find_similar_vehicles",
                    description="Find vehicles similar to a reference vehicle based on category, price range, and features. Great for showing alternatives when the customer's first choice isn't available or for expanding their options.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "reference_vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Reference vehicle ID to find similar vehicles based on"
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 20,
                                "default": 5,
                                "description": "Maximum number of similar vehicles to return"
                            },
                            "price_tolerance_percent": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 20,
                                "description": "Price tolerance as percentage (e.g., 20 = ±20% from reference vehicle price)"
                            },
                            "include_unavailable": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether to include sold or reserved vehicles in similarity results"
                            }
                        },
                        "required": ["reference_vehicle_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-similar-vehicles")
            ),
            
            # 5. Get Vehicle Details
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_details",
                    description="Get comprehensive details about a specific vehicle including specifications, features, condition, history, and all available information. Perfect for answering detailed customer questions about specific vehicles.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Vehicle ID to get detailed information for (UUID format)"
                            },
                            "inventory_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "Specific inventory item ID for exact details of a particular car on the lot (preferred over vehicle_id)"
                            },
                            "include_pricing": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to include detailed pricing breakdown and financing estimates"
                            },
                            "include_similar": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether to include similar vehicle suggestions for alternatives"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-vehicle-details")
            )
        ]
    
    def get_calendar_tools(self) -> List[CreateFunctionToolDto]:
        """Get all 6 calendar management tools as DTO objects."""
        return [
            # 1. List Available Calendars
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="list_available_calendars",
                    description="List all available calendars for appointment scheduling with optional filtering. Helps identify which calendars are available for booking customer appointments.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10,
                                "description": "Maximum number of calendars to return"
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether to include hidden calendars in results"
                            },
                            "query_strings": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Search patterns to filter calendars (regex supported)"
                            },
                            "query_string_to_include": {
                                "type": "string",
                                "description": "Single search pattern that calendars must match to be included"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/list-calendars")
            ),
            
            # 2. Check Availability
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="check_availability",
                    description="Check calendar availability for appointment scheduling within specified date ranges and working hours. Essential for finding open time slots for customer appointments.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of calendar IDs to check availability for"
                            },
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for availability check (YYYY-MM-DD format)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date", 
                                "description": "End date for availability check (YYYY-MM-DD format)"
                            },
                            "working_hours_start": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 23,
                                "default": 9,
                                "description": "Start of working hours (24-hour format)"
                            },
                            "working_hours_end": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 23,
                                "default": 17,
                                "description": "End of working hours (24-hour format)"
                            },
                            "working_days": {
                                "type": "array",
                                "items": {"type": "integer", "minimum": 0, "maximum": 6},
                                "default": [0, 1, 2, 3, 4],
                                "description": "Working days (0=Monday, 6=Sunday)"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/get-availability")
            ),
            
            # 3. Get Calendar Events
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_calendar_events",
                    description="Retrieve calendar events with flexible filtering options. Can get specific events by ID or search for events within date ranges. Useful for checking existing appointments and schedules.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of calendar IDs to search for events"
                            },
                            "event_id": {
                                "type": "string",
                                "description": "Specific event ID to retrieve (for single event lookup)"
                            },
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for event search (YYYY-MM-DD format)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for event search (YYYY-MM-DD format)"
                            },
                            "search_query": {
                                "type": "string",
                                "description": "Text search query to filter events by title, description, or content"
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 250,
                                "default": 50,
                                "description": "Maximum number of events to return"
                            },
                            "order_by": {
                                "type": "string",
                                "enum": ["startTime", "updated"],
                                "default": "startTime",
                                "description": "How to order the returned events"
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/get-events")
            ),
            
            # 4. Create Appointment
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="create_appointment",
                    description="Create new appointments/events in Google Calendar with comprehensive options including attendees, reminders, and Google Meet integration. Perfect for scheduling customer appointments.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID where the appointment should be created"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Appointment title/summary (e.g., 'Vehicle Test Drive - John Smith')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed appointment description with customer notes and requirements"
                            },
                            "start_datetime": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Appointment start time in ISO format (e.g., '2024-01-15T10:00:00')"
                            },
                            "end_datetime": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Appointment end time in ISO format (e.g., '2024-01-15T11:00:00')"
                            },
                            "timezone": {
                                "type": "string",
                                "default": "America/New_York",
                                "description": "Timezone for the appointment (e.g., 'America/New_York', 'America/Los_Angeles')"
                            },
                            "attendee_emails": {
                                "type": "array",
                                "items": {"type": "string", "format": "email"},
                                "description": "List of required attendee email addresses"
                            },
                            "optional_attendee_emails": {
                                "type": "array",
                                "items": {"type": "string", "format": "email"},
                                "description": "List of optional attendee email addresses"
                            },
                            "location": {
                                "type": "string",
                                "description": "Physical location for the appointment (dealership address, specific lot location)"
                            },
                            "add_google_meet": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether to add Google Meet video conferencing to the appointment"
                            },
                            "send_notifications": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to send email notifications to attendees about the appointment"
                            },
                            "email_reminder_minutes": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Minutes before appointment to send email reminder (e.g., 1440 for 24 hours)"
                            },
                            "popup_reminder_minutes": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Minutes before appointment to show popup reminder (e.g., 30 for 30 minutes)"
                            }
                        },
                        "required": ["calendar_id", "summary", "start_datetime", "end_datetime"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/create-event")
            ),
            
            # 5. Update Appointment
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="update_appointment",
                    description="Update existing appointments with partial update support. Can modify any aspect of an appointment including time, attendees, location, or description. Essential for rescheduling and appointment modifications.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID where the appointment exists"
                            },
                            "event_id": {
                                "type": "string",
                                "description": "Event ID of the appointment to update"
                            },
                            "summary": {
                                "type": "string",
                                "description": "New appointment title/summary"
                            },
                            "description": {
                                "type": "string",
                                "description": "New appointment description"
                            },
                            "start_datetime": {
                                "type": "string",
                                "format": "date-time",
                                "description": "New start time in ISO format"
                            },
                            "end_datetime": {
                                "type": "string", 
                                "format": "date-time",
                                "description": "New end time in ISO format"
                            },
                            "timezone": {
                                "type": "string",
                                "description": "New timezone for the appointment"
                            },
                            "location": {
                                "type": "string",
                                "description": "New location for the appointment"
                            },
                            "attendee_emails": {
                                "type": "array",
                                "items": {"type": "string", "format": "email"},
                                "description": "New list of required attendee email addresses (replaces existing)"
                            },
                            "attendee_action": {
                                "type": "string",
                                "enum": ["replace", "add", "remove"],
                                "default": "replace",
                                "description": "How to handle attendee updates: replace all, add new, or remove specified"
                            },
                            "add_google_meet": {
                                "type": "boolean",
                                "description": "Add or remove Google Meet from the appointment"
                            },
                            "send_notifications": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to send notifications about the update"
                            }
                        },
                        "required": ["calendar_id", "event_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/update-event")
            ),
            
            # 6. Cancel Appointment
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="cancel_appointment",
                    description="Cancel/delete appointments from Google Calendar with notification options. Handles appointment cancellations gracefully with attendee notifications.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID where the appointment exists"
                            },
                            "event_id": {
                                "type": "string",
                                "description": "Event ID of the appointment to cancel"
                            },
                            "send_notifications": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to send cancellation notifications to attendees"
                            },
                            "force_delete": {
                                "type": "boolean",
                                "default": False,
                                "description": "Force delete even if there are permission issues"
                            }
                        },
                        "required": ["calendar_id", "event_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/delete-event")
            )
        ]
    
    def get_knowledge_base_tools(self) -> List[CreateFunctionToolDto]:
        """Get all 2 knowledge base management tools as DTO objects."""
        return [
            # 1. Fetch Latest Knowledge Base
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="fetch_latest_knowledge_base",
                    description="Fetch the latest knowledge base content from configured GitHub sources including dealership information, financing options, services, and current offers. Updates automatically using server configuration.",
                    parameters={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/knowledge-base/fetch-latest")
            ),
            
            # 2. Sync Knowledge Base to VAPI
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="sync_knowledge_base_to_vapi",
                    description="Synchronize knowledge base content to VAPI automatically. Fetches latest content from configured sources and updates VAPI knowledge base. Complete workflow for keeping voice agent updated with latest dealership information.",
                    parameters={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/knowledge-base/sync")
            )
        ]
    
    def get_all_tools(self) -> List[CreateFunctionToolDto]:
        """Get all 13 automotive tools as DTO objects."""
        tools = []
        tools.extend(self.get_inventory_tools())
        tools.extend(self.get_calendar_tools()) 
        tools.extend(self.get_knowledge_base_tools())
        return tools
    
    async def register_all_tools(self) -> List[str]:
        """Register all 13 tools with VAPI and return list of tool IDs."""
        tool_ids = []
        tools = self.get_all_tools()
        
        for tool in tools:
            try:
                print(f"📝 Registering {tool.function.name}...")
                result = self.client.tools.create(request=tool)
                tool_ids.append(result.id)
                print(f"✅ Registered {tool.function.name} (ID: {result.id})")
            except Exception as e:
                print(f"❌ Failed to register {tool.function.name}: {e}")
                
        return tool_ids
    
    async def create_automotive_assistant(self, tool_ids: List[str]) -> str:
        """Create VAPI assistant with all registered tools."""
        try:
            assistant_dto = CreateAssistantDto(
                name="Automotive Dealership Voice Assistant",
                model={
                    "provider": "openai",
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a professional automotive dealership voice assistant. Your role is to help customers with:

1. VEHICLE INVENTORY: Search available vehicles, get pricing, find similar options, check delivery dates, and provide detailed vehicle information.

2. APPOINTMENT SCHEDULING: Book test drives, service appointments, and sales consultations using the integrated calendar system.

3. DEALERSHIP INFORMATION: Provide information about financing options, services offered, current promotions, and company details.

Key Guidelines:
- Always be professional, helpful, and knowledgeable about automotive topics
- Use the available tools to provide accurate, real-time information
- When customers ask about vehicles, use inventory tools to search and provide options
- For appointments, check availability first, then create appointments with proper details
- Explain vehicle features, pricing, and financing options clearly
- If you don't have specific information, use the appropriate tools to fetch current data
- Always confirm important details like appointment times and vehicle specifications

You have access to 13 specialized tools covering inventory management, calendar operations, and knowledge base access. Use them proactively to provide the best customer service experience."""
                        }
                    ]
                },
                voice=ElevenLabsVoice(
                    voice_id="pNInz6obpgDQGcFmaJgB"  # Adam voice ID from 11Labs
                ),
                first_message="Hello! I'm your automotive dealership assistant. I can help you find the perfect vehicle, schedule appointments, and answer questions about our services. How can I help you today?",
                server_url_secret="",  # Not using webhooks - direct tool mapping
                tool_ids=tool_ids,
                end_call_message="Thank you for contacting our dealership. Have a great day!",
                record_call=True,
                interruptions_enabled=True,
                language="en"
            )
            
            result = self.client.assistants.create(**assistant_dto.__dict__)
            print(f"✅ Created automotive assistant (ID: {result.id})")
            return result.id
            
        except Exception as e:
            print(f"❌ Failed to create assistant: {e}")
            raise