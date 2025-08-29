"""
VAPI tool manager for registering automotive dealership tools.
Handles programmatic registration of all 13 tools using VAPI SDK.
"""

import json
from typing import List, Dict, Any, Optional
from vapi import Vapi
from config.vapi_settings import vapi_settings


class VapiToolManager:
    """Manager for registering automotive tools with VAPI."""
    
    def __init__(self, api_token: Optional[str] = None, server_base_url: Optional[str] = None):
        """Initialize VAPI tool manager."""
        self.api_token = api_token or vapi_settings.vapi_api_token
        self.server_base_url = server_base_url or vapi_settings.server_base_url
        self.client = Vapi(token=self.api_token)
    
    def get_inventory_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for all 5 inventory management tools."""
        return [
            {
                "type": "function",
                "name": "check_vehicle_inventory",
                "description": "Search dealership inventory for available vehicles matching customer criteria including category, price range, model, features, and availability status. Perfect for helping customers find vehicles that meet their specific needs and preferences.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/inventory/check-inventory",
                    "method": "POST"
                },
                "parameters": {
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
            },
            {
                "type": "function", 
                "name": "get_vehicle_delivery_dates",
                "description": "Get expected delivery date ranges for a specific vehicle showing earliest and latest availability across all inventory. Provides realistic delivery timelines to help customers plan their purchase and set proper expectations.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/inventory/get-delivery-dates",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vehicle_id": {
                            "type": "string",
                            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                            "description": "Unique vehicle identifier (UUID format) from inventory search results"
                        },
                        "features": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific features customer wants - may affect delivery time if installation is needed"
                        }
                    },
                    "required": ["vehicle_id"]
                }
            },
            {
                "type": "function",
                "name": "get_vehicle_pricing",
                "description": "Get comprehensive pricing information including base price, feature costs, available discounts, and final pricing. Supports both general vehicle pricing and specific inventory item pricing with detailed breakdown.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/inventory/get-prices",
                    "method": "POST"
                },
                "parameters": {
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
            },
            {
                "type": "function",
                "name": "find_similar_vehicles", 
                "description": "Find vehicles similar to a reference vehicle based on category, price range, and features. Great for showing alternatives when the customer's first choice isn't available or for expanding their options.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/inventory/get-similar-vehicles",
                    "method": "POST"
                },
                "parameters": {
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
                            "description": "Price difference tolerance as percentage (e.g., 20 means within 20% of reference price)"
                        },
                        "include_unavailable": {
                            "type": "boolean",
                            "default": false,
                            "description": "Whether to include sold or reserved vehicles in similarity results"
                        }
                    },
                    "required": ["reference_vehicle_id"]
                }
            },
            {
                "type": "function",
                "name": "get_vehicle_details",
                "description": "Get complete vehicle information including detailed specifications, features, availability status, and optional pricing. Perfect for providing comprehensive information when customers want to know everything about a specific vehicle.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/inventory/get-vehicle-details",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vehicle_id": {
                            "type": "string", 
                            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                            "description": "Vehicle ID to get comprehensive details for"
                        },
                        "inventory_id": {
                            "type": "string",
                            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                            "description": "Specific inventory item ID for details about a particular car on the lot"
                        },
                        "include_pricing": {
                            "type": "boolean",
                            "default": true,
                            "description": "Include detailed pricing breakdown in the response"
                        },
                        "include_similar": {
                            "type": "boolean", 
                            "default": false,
                            "description": "Include similar vehicle suggestions in the response"
                        }
                    },
                    "required": []
                }
            }
        ]
    
    def get_calendar_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for all 6 calendar management tools."""
        return [
            {
                "type": "function",
                "name": "list_available_calendars",
                "description": "List all available Google Calendar calendars for scheduling dealership appointments like test drives, service appointments, and consultations. Supports filtering to find specific calendars.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/list-calendars",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address of the staff member or calendar owner for authentication"
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "default": 100,
                            "description": "Maximum number of calendars to return"
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "default": false,
                            "description": "Include hidden calendars in results"
                        },
                        "query_strings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter calendars by name patterns (e.g., ['service', 'sales'] to find service and sales calendars)"
                        },
                        "query_string_to_include": {
                            "type": "boolean",
                            "default": true,
                            "description": "Whether query strings should include (true) or exclude (false) matching calendars"
                        }
                    },
                    "required": ["user_email"]
                }
            },
            {
                "type": "function",
                "name": "check_availability",
                "description": "Check available time slots in dealership calendars for scheduling appointments. Shows free periods within business hours for test drives, consultations, and service appointments.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/get-availability",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address of the staff member for authentication"
                        },
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Calendar IDs to check availability for (from list_available_calendars)"
                        },
                        "start_time": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start date and time for availability check (ISO format)"
                        },
                        "end_time": {
                            "type": "string", 
                            "format": "date-time",
                            "description": "End date and time for availability check (ISO format)"
                        },
                        "working_hours_start": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 23,
                            "default": 9,
                            "description": "Business hours start time in 24-hour format (e.g., 9 for 9 AM)"
                        },
                        "working_hours_end": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 23,
                            "default": 17,
                            "description": "Business hours end time in 24-hour format (e.g., 17 for 5 PM)" 
                        },
                        "working_days": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 6},
                            "description": "Working days of the week (0=Monday, 6=Sunday). Default is Monday-Friday [0,1,2,3,4]"
                        },
                        "time_zone": {
                            "type": "string",
                            "description": "Time zone for the availability check (e.g., 'America/New_York')"
                        }
                    },
                    "required": ["user_email"]
                }
            },
            {
                "type": "function",
                "name": "get_calendar_events",
                "description": "Retrieve scheduled appointments and events from dealership calendars. Can get specific event details or list events within a date range for scheduling coordination.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/get-events",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address for authentication"
                        },
                        "calendar_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Calendar IDs to retrieve events from"
                        },
                        "event_id": {
                            "type": "string",
                            "description": "Specific event ID to retrieve details for"
                        },
                        "time_min": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start date/time for event search (ISO format)"
                        },
                        "time_max": {
                            "type": "string",
                            "format": "date-time",
                            "description": "End date/time for event search (ISO format)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search text to find events by title or description"
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 2500,
                            "default": 250,
                            "description": "Maximum number of events to return"
                        },
                        "order_by": {
                            "type": "string",
                            "enum": ["startTime", "updated"],
                            "default": "startTime",
                            "description": "How to order returned events"
                        },
                        "show_deleted": {
                            "type": "boolean",
                            "default": false,
                            "description": "Include deleted events in results"
                        },
                        "time_zone": {
                            "type": "string",
                            "description": "Time zone for the event times"
                        }
                    },
                    "required": ["user_email"]
                }
            },
            {
                "type": "function",
                "name": "create_appointment",
                "description": "Create a new appointment in the dealership calendar for test drives, consultations, service appointments, or other customer meetings. Supports attendee management and meeting details.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/create-event",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address of staff member for authentication"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID to create the appointment in (from list_available_calendars)"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Appointment title (e.g., 'Test Drive - Toyota Camry', 'Service Consultation')"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Appointment start date and time (ISO format or natural language)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "Appointment end date and time (ISO format or natural language)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Appointment details, notes, or special instructions"
                        },
                        "location": {
                            "type": "string",
                            "description": "Meeting location (dealership address, service bay, showroom, etc.)"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Email addresses of required attendees (customer, sales staff, etc.)"
                        },
                        "optional_attendees": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Email addresses of optional attendees"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Time zone for the appointment"
                        },
                        "all_day": {
                            "type": "boolean",
                            "default": false,
                            "description": "Whether this is an all-day event"
                        },
                        "create_google_meet": {
                            "type": "boolean",
                            "default": false,
                            "description": "Create Google Meet link for virtual consultations"
                        },
                        "send_notifications": {
                            "type": "string",
                            "enum": ["all", "external", "none"],
                            "default": "all",
                            "description": "Send email notifications to attendees"
                        }
                    },
                    "required": ["user_email", "calendar_id", "summary", "start_time", "end_time"]
                }
            },
            {
                "type": "function",
                "name": "update_appointment",
                "description": "Update or reschedule an existing dealership appointment. Can change time, attendees, location, or other details while maintaining appointment history.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/update-event",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address for authentication"
                        },
                        "calendar_id": {
                            "type": "string",
                            "description": "Calendar ID containing the event"
                        },
                        "event_id": {
                            "type": "string",
                            "description": "Event ID to update (from get_calendar_events)"
                        },
                        "summary": {
                            "type": "string",
                            "description": "New appointment title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "New start date and time for rescheduling"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "New end date and time for rescheduling"
                        },
                        "description": {
                            "type": "string",
                            "description": "Updated appointment details or notes"
                        },
                        "location": {
                            "type": "string",
                            "description": "Updated meeting location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Updated list of attendee email addresses"
                        },
                        "attendee_action": {
                            "type": "string",
                            "enum": ["replace", "add", "remove"],
                            "default": "replace",
                            "description": "How to handle attendee list updates"
                        },
                        "send_notifications": {
                            "type": "string",
                            "enum": ["all", "external_only", "none"],
                            "default": "all",
                            "description": "Send update notifications to attendees"
                        }
                    },
                    "required": ["user_email", "calendar_id", "event_id"]
                }
            },
            {
                "type": "function",
                "name": "cancel_appointment",
                "description": "Cancel or delete a dealership appointment from the calendar. Handles notification to attendees and proper cleanup of cancelled appointments.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/calendar/delete-event",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address for authentication"
                        },
                        "calendar_id": {
                            "type": "string",
                            "default": "primary",
                            "description": "Calendar ID containing the event to cancel"
                        },
                        "event_id": {
                            "type": "string",
                            "description": "Event ID to cancel (from get_calendar_events)"
                        },
                        "send_notifications": {
                            "type": "boolean",
                            "default": true,
                            "description": "Send cancellation notifications to attendees"
                        },
                        "force_delete": {
                            "type": "boolean",
                            "default": false,
                            "description": "Force delete even if there are errors"
                        }
                    },
                    "required": ["user_email", "event_id"]
                }
            }
        ]
    
    def get_knowledge_base_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for 2 knowledge base management tools."""
        return [
            {
                "type": "function",
                "name": "fetch_latest_knowledge_base",
                "description": "Fetch the latest dealership knowledge base content from GitHub sources including company information, financing options, services, and current offers. Used to ensure voice assistant has up-to-date dealership information.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/knowledge-base/fetch-latest",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "github_raw_urls": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "uri"
                            },
                            "description": "GitHub raw URLs to fetch knowledge base markdown files from (company info, financing, services, offers)"
                        },
                        "cache_duration_minutes": {
                            "type": "integer",
                            "minimum": 1,
                            "default": 30,
                            "description": "How long to cache fetched content in minutes"
                        },
                        "max_file_size_mb": {
                            "type": "integer",
                            "minimum": 1,
                            "default": 10,
                            "description": "Maximum file size to download in megabytes"
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "minimum": 5,
                            "default": 30,
                            "description": "Request timeout for fetching content"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function", 
                "name": "sync_knowledge_base_to_vapi",
                "description": "Synchronize dealership knowledge base content with VAPI's knowledge base tool. Updates the voice assistant's knowledge with latest dealership information including policies, procedures, and current offerings.",
                "server": {
                    "url": f"{self.server_base_url}/api/v1/knowledge-base/sync",
                    "method": "POST"
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vapi_api_key": {
                            "type": "string",
                            "description": "VAPI API key for authentication"
                        },
                        "knowledge_base_tool_id": {
                            "type": "string",
                            "description": "VAPI knowledge base tool ID to update with new content"
                        },
                        "markdown_files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            },
                            "description": "Markdown files with dealership knowledge to sync"
                        },
                        "file_name_prefix": {
                            "type": "string",
                            "default": "kb_",
                            "description": "Prefix for knowledge base file names in VAPI"
                        },
                        "vapi_base_url": {
                            "type": "string",
                            "format": "uri",
                            "default": "https://api.vapi.ai",
                            "description": "VAPI API base URL"
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "minimum": 5,
                            "default": 30,
                            "description": "Request timeout for VAPI operations"
                        }
                    },
                    "required": ["vapi_api_key", "knowledge_base_tool_id"]
                }
            }
        ]
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all 13 tool definitions for automotive dealership."""
        tools = []
        tools.extend(self.get_inventory_tool_definitions())
        tools.extend(self.get_calendar_tool_definitions())
        tools.extend(self.get_knowledge_base_tool_definitions())
        return tools
    
    async def register_all_tools(self) -> List[str]:
        """Register all 13 automotive tools with VAPI."""
        tool_definitions = self.get_all_tool_definitions()
        tool_ids = []
        
        for tool_def in tool_definitions:
            try:
                response = await self.client.tools.create(**tool_def)
                tool_ids.append(response.id)
                print(f"✅ Registered tool: {tool_def['name']} -> {response.id}")
            except Exception as e:
                print(f"❌ Failed to register {tool_def['name']}: {e}")
                
        return tool_ids
    
    async def create_automotive_assistant(self, tool_ids: List[str]) -> str:
        """Create VAPI assistant with all automotive tools."""
        assistant_config = {
            "name": "Automotive Dealership Assistant",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1,
                "systemMessage": """You are a helpful automotive dealership assistant. You can help customers with:
- Finding vehicles in our inventory based on their preferences
- Scheduling test drives and service appointments  
- Getting pricing information and delivery estimates
- Answering questions about vehicle features and specifications
- Managing calendar appointments

Always be friendly, professional, and focus on helping the customer find the right vehicle for their needs. Ask clarifying questions when needed to provide the best service."""
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "pNInz6obpgDQGcFmaJgB"  # Adam voice
            },
            "tools": [{"id": tool_id} for tool_id in tool_ids],
            "firstMessage": "Hi! I'm your automotive assistant. How can I help you find the perfect car today?",
            "recordingEnabled": True,
            "interruptionsEnabled": True
        }
        
        try:
            response = await self.client.assistants.create(**assistant_config)
            print(f"✅ Created assistant: {response.id}")
            return response.id
        except Exception as e:
            print(f"❌ Failed to create assistant: {e}")
            raise