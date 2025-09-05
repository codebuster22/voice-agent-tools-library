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
            # 1. Check Vehicle Inventory - ENTRY POINT TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="check_vehicle_inventory",
                    description="🎯 PRIMARY DISCOVERY TOOL - Use this when customers want to explore vehicles or mention ANY vehicle preferences. This is your starting point for vehicle conversations.\n\n⚡ CONVERSATION TRIGGERS:\n• Customer mentions vehicle types: 'I want an SUV', 'Looking for a sedan'\n• Budget discussions: 'Under $30k', 'Between $25k-40k'\n• Feature requests: 'With sunroof', 'AWD preferred'\n• General shopping: 'What do you have?', 'Show me options'\n\n🔗 WORKFLOW CHAIN:\ncheck_inventory → get_vehicle_details (for specifics) → get_prices (for cost) → create_appointment (for test drive)\n\n💡 AGENT STRATEGY: Cast a wide net first, then narrow down. If customer is vague, search broadly and let them refine. Returns vehicle_id needed for all other vehicle tools.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["sedan", "suv", "truck", "coupe"],
                                "description": "Vehicle body type - CUSTOMER INPUT: Listen for 'sedan' (family car needs), 'SUV' (space/versatility), 'truck' (work/hauling), 'coupe' (style/performance). Leave empty if customer hasn't specified."
                            },
                            "model_name": {
                                "type": "string",
                                "description": "Specific model mentioned by customer - EXACT MATCH: Use customer's exact words like 'Camry', 'CR-V', 'F-150'. Don't guess - only use if explicitly mentioned. Partial matches work: 'Ford' finds all Ford models."
                            },
                            "min_price": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Minimum budget - CUSTOMER BUDGET: Use when customer says 'at least $X', 'starting from $X', 'above $X'. Convert monthly payments to rough price (payment × 60 months). Leave empty if no minimum mentioned."
                            },
                            "max_price": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Maximum budget - MOST IMPORTANT FILTER: Use when customer mentions ANY upper limit: 'under $30k', 'max $40k', 'budget is $35k'. Convert monthly payment limits to price estimates. ALWAYS use if budget mentioned."
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Must-have features - CUSTOMER WISHLIST: Include anything customer mentions: 'leather seats', 'sunroof', 'AWD', 'navigation', 'backup camera', 'heated seats', 'apple carplay'. Use customer's exact language. Prioritizes results with these features."
                            },
                            "status": {
                                "type": "string",
                                "enum": ["available", "sold", "reserved", "all"],
                                "default": "available",
                                "description": "Availability filter - DEFAULT 'available': Shows only purchasable vehicles. Use 'all' only if customer specifically asks about sold vehicles or full inventory. Never use 'sold' for shopping customers."
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/check-inventory")
            ),
            
            # 2. Get Vehicle Delivery Dates - TIMING TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_delivery_dates",
                    description="⏰ DELIVERY TIMELINE TOOL - Use when customers ask about timing: 'When can I get it?', 'How soon?', 'When available?'\n\n⚡ CONVERSATION TRIGGERS:\n• Time sensitivity: 'I need it by next month', 'When available?'\n• Purchase decision making: Customer is interested but needs delivery info\n• Comparison shopping: Different models with different timelines\n• Urgency questions: 'Can I get it for my birthday?', 'Before winter?'\n\n🔗 REQUIRES: vehicle_id from check_inventory results\n💡 WORKFLOW: check_inventory → get_vehicle_details → get_delivery_dates → create_appointment (if timeline works)\n\n🎯 AGENT STRATEGY: Use after customer shows genuine interest in specific vehicle. Essential for setting realistic expectations and closing deals.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 PARAMETER SOURCE: Get from check_inventory results → 'vehicle_id' field. REQUIRED - tool fails without valid UUID. Example: 'abc12345-def6-7890-ghij-123456789012'. Each inventory result contains this ID."
                            }
                        },
                        "required": ["vehicle_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-delivery-dates")
            ),
            
            # 3. Get Vehicle Pricing - CRITICAL DECISION TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_pricing",
                    description="💰 PRICING DECISION TOOL - THE MOST IMPORTANT TOOL for purchase decisions. Use whenever price is mentioned or customer shows purchase intent.\n\n⚡ CONVERSATION TRIGGERS:\n• Direct price questions: 'How much?', 'What's the price?', 'Cost?'\n• Budget validation: 'Is this in my budget?', 'Can I afford this?'\n• Feature pricing: 'How much to add leather?', 'Cost with navigation?'\n• Comparison shopping: 'Price difference between models?'\n• Finance discussions: Before discussing loans/payments\n\n🔗 PARAMETER SOURCES:\n• vehicle_id: FROM check_inventory → 'vehicle_id'\n• inventory_id: FROM check_inventory → 'inventory_id' (for exact car on lot)\n\n💡 WORKFLOW CHAIN:\ncheck_inventory → get_pricing → (show options) → create_appointment\n\n🎯 AGENT STRATEGY: ALWAYS get pricing before discussing financing. Use 'specific' for exact vehicles, 'by_features' for estimates.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["specific", "by_features"],
                                "default": "specific",
                                "description": "PRICING MODE - 'specific': Exact pricing for known vehicle (use when you have vehicle_id). 'by_features': Estimated pricing based on desired features (use for general price ranges or feature comparisons)."
                            },
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 FROM check_inventory: Use 'vehicle_id' from inventory results for base model pricing. REQUIRED for specific pricing. Gets base price + available options for this vehicle model."
                            },
                            "inventory_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 FROM check_inventory: Use 'inventory_id' for EXACT car on lot pricing. PREFERRED over vehicle_id when available - gives actual price of specific car including all installed features."
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "ADDITIONAL FEATURES CUSTOMER WANTS: Features to add to base price calculation. Use customer's exact language: 'leather seats', 'sunroof', 'navigation'. For pricing 'what if' scenarios."
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-prices")
            ),
            
            # 4. Find Similar Vehicles - ALTERNATIVE DISCOVERY TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="find_similar_vehicles",
                    description="🔄 ALTERNATIVE EXPLORATION TOOL - Use when customer shows interest in a vehicle but needs alternatives or when you want to expand their options.\n\n⚡ CONVERSATION TRIGGERS:\n• Hesitation: 'I like this but...', 'It's nice, but...'\n• Budget concerns: 'Too expensive', 'Cheaper options?'\n• Feature needs: 'Similar with more features?', 'Without this feature?'\n• Comparison shopping: 'What else is like this?', 'Show me alternatives'\n• Availability issues: 'This one's sold - similar options?'\n• Exploration: 'What else should I consider?'\n\n🔗 REQUIRES: reference_vehicle_id from ANY previous vehicle tool result\n💡 WORKFLOW: check_inventory → [customer interest] → find_similar → get_pricing → compare options\n\n🎯 AGENT STRATEGY: Perfect for keeping customers engaged when first choice isn't perfect. Increases sales opportunities.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "reference_vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 REFERENCE POINT: Use vehicle_id from any previous tool result (check_inventory, get_vehicle_details). This vehicle becomes the similarity baseline. REQUIRED - algorithm needs reference to compare against."
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 20,
                                "default": 5,
                                "description": "RESULTS LIMIT: Use 3-5 for focused options, up to 10 for broader exploration. Too many choices overwhelm customers. Default 5 is optimal for most situations."
                            },
                            "price_tolerance_percent": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 20,
                                "description": "PRICE FLEXIBILITY: 20% = similar price range, 50% = much broader range. CUSTOMER CLUES: 'similar price' = 20%, 'any price range' = 50%, 'cheaper options' = 30% below reference."
                            },
                            "include_unavailable": {
                                "type": "boolean",
                                "default": False,
                                "description": "AVAILABILITY FILTER: Use FALSE for buying customers (default). Use TRUE only if customer specifically asks 'what was similar to the sold one?' or for research purposes."
                            }
                        },
                        "required": ["reference_vehicle_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/inventory/get-similar-vehicles")
            ),
            
            # 5. Get Vehicle Details - INFORMATION DEEP-DIVE TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_vehicle_details",
                    description="📋 DETAILED INFORMATION TOOL - Use when customers want to know specifics about a particular vehicle. Bridge between discovery and purchase decision.\n\n⚡ CONVERSATION TRIGGERS:\n• Specification questions: 'Tell me about this car', 'What are the specs?'\n• Feature inquiries: 'What features does it have?', 'Is it reliable?'\n• Comparison needs: 'How's the fuel economy?', 'Safety ratings?'\n• Purchase interest: Customer focuses on specific vehicle from search results\n• Technical questions: 'Engine size?', 'Transmission type?', 'Warranty?'\n\n🔗 PARAMETER SOURCES:\n• vehicle_id: FROM check_inventory → 'vehicle_id'\n• inventory_id: FROM check_inventory → 'inventory_id' (preferred - gives exact car details)\n\n💡 WORKFLOW CHAIN:\ncheck_inventory → get_vehicle_details → get_pricing → create_appointment\n\n🎯 AGENT STRATEGY: Use when customer narrows focus to specific vehicles. Essential for building confidence and answering objections.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "vehicle_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 FROM check_inventory: Use 'vehicle_id' for general vehicle model information. Gets specifications, features, and general details for this vehicle type."
                            },
                            "inventory_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                                "description": "🔗 FROM check_inventory: Use 'inventory_id' for SPECIFIC car on lot details. PREFERRED - gives exact mileage, condition, history, specific features of the actual car customer can buy."
                            },
                            "include_pricing": {
                                "type": "boolean",
                                "default": True,
                                "description": "INCLUDE PRICING: Default TRUE - most customers want price with details. Set FALSE only if customer specifically doesn't want pricing or already has it."
                            },
                            "include_similar": {
                                "type": "boolean",
                                "default": False,
                                "description": "SHOW ALTERNATIVES: Set TRUE if customer seems uncertain or comparison shopping. FALSE for focused buyers. Adds similar vehicles to response."
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
            # 1. List Available Calendars - CALENDAR DISCOVERY TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="list_available_calendars",
                    description="📅 CALENDAR DISCOVERY TOOL - FIRST STEP for all appointment scheduling. Use this to find the right calendar before checking availability or booking.\n\n⚡ CONVERSATION TRIGGERS:\n• ANY appointment request: 'Book appointment', 'Schedule test drive', 'Set up meeting'\n• Calendar selection needed: 'Which calendar?', 'Available schedules?'\n• Service department booking: 'Service appointment', 'Maintenance scheduling'\n• Sales team booking: 'Meet with salesperson', 'Consultation'\n\n🔗 WORKFLOW CHAIN (REQUIRED SEQUENCE):\nlist_calendars → get_availability → create_appointment\n\n💡 AGENT STRATEGY: ALWAYS start here for appointments. Never assume calendar_id. Get calendar list first, then check availability.\n\n🎯 COMMON PATTERNS:\n• Use 'service' filter for maintenance/repair appointments\n• Use 'sales' filter for test drives/consultations\n• Use no filter to show all available calendars",
                    parameters={
                        "type": "object",
                        "properties": {
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 1000,
                                "default": 100,
                                "description": "RESULTS LIMIT: Default 100 is usually sufficient. Reduce if you want fewer options for customer selection."
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "default": False,
                                "description": "HIDDEN CALENDARS: Keep FALSE (default) - hidden calendars are usually internal/private. Use TRUE only if customer has administrative privileges."
                            },
                            "query_strings": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CALENDAR FILTERS: Use customer context to filter. Examples: ['service'] for maintenance, ['sales', 'test'] for sales appointments, ['manager'] for management meetings. Supports regex patterns."
                            },
                            "query_string_to_include": {
                                "type": "boolean",
                                "default": True,
                                "description": "FILTER MODE: TRUE = include matching calendars (normal), FALSE = exclude matching calendars (use to hide specific calendars from customer selection)."
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/list-calendars")
            ),
            
            # 2. Check Availability - TIME SLOT FINDER
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="check_availability",
                    description="⏰ TIME SLOT FINDER - CRITICAL STEP before booking appointments. Shows exact available time slots within customer's preferred timeframe.\n\n⚡ CONVERSATION TRIGGERS:\n• Time preferences: 'Tomorrow afternoon', 'Next week mornings', 'Friday 2pm'\n• Schedule questions: 'When are you available?', 'Open times?', 'What slots?'\n• Booking progression: After customer shows interest + calendar selected\n• Rescheduling needs: 'Different time?', 'Other options?'\n\n🔗 REQUIRES: calendar_ids from list_calendars results\n💡 WORKFLOW: list_calendars → check_availability → create_appointment\n\n🎯 AGENT STRATEGY: Be generous with time ranges. If customer says 'this week', check entire week. Offer multiple options.\n\n🕐 TIME HANDLING:\n• 'Morning' = 9am-12pm, 'Afternoon' = 1pm-5pm, 'Evening' = 6pm-8pm\n• 'Next week' = add 7 days to current date\n• Always use dealership business hours (9am-5pm default)",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "🔗 FROM list_calendars: Use 'calendarId' field from calendar results. REQUIRED - must have at least one calendar to check. Can check multiple calendars for more availability options."
                            },
                            "start_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "SEARCH START: Use customer's earliest acceptable time. CUSTOMER CLUES: 'tomorrow' = tomorrow 9am, 'next week' = Monday 9am, 'this afternoon' = today 1pm. Format: ISO datetime."
                            },
                            "end_time": {
                                "type": "string", 
                                "format": "date-time",
                                "description": "SEARCH END: Use reasonable end based on customer request. DEFAULT: 1 week from start_time if not specified. 'This week' = Friday 5pm, 'Tomorrow' = tomorrow 5pm."
                            },
                            "time_zone": {
                                "type": "string",
                                "description": "CUSTOMER TIMEZONE: Use customer's local timezone if known, otherwise dealership timezone. Examples: 'America/New_York', 'America/Chicago', 'America/Los_Angeles'. Default: dealership timezone."
                            },
                            "working_hours_start": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 23,
                                "default": 9,
                                "description": "BUSINESS HOURS START: Dealership opening hour in 24-hour format. Default 9 (9am). Adjust for service (may start 8am) vs sales (may start 10am)."
                            },
                            "working_hours_end": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 23,
                                "default": 17,
                                "description": "BUSINESS HOURS END: Dealership closing hour in 24-hour format. Default 17 (5pm). Service may go to 18 (6pm), sales usually 17 (5pm)."
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/webhook/vapi")
            ),
            
            # 3. Get Calendar Events - EXISTING APPOINTMENT LOOKUP
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="get_calendar_events",
                    description="🔍 EXISTING APPOINTMENT LOOKUP - Use to find, verify, or search for existing appointments. NOT for booking new appointments.\n\n⚡ CONVERSATION TRIGGERS:\n• Existing appointment questions: 'What's my appointment?', 'When is my test drive?'\n• Schedule verification: 'Confirm my booking', 'What do I have scheduled?'\n• Customer lookup: 'Find John Smith's appointment', 'Search by customer name'\n• Date range queries: 'What's scheduled tomorrow?', 'This week's appointments'\n• Modification preparation: Before updating/canceling appointments\n\n🔗 PARAMETER SOURCES:\n• calendar_ids: FROM list_calendars results (for searching across calendars)\n• event_id: FROM previous create_appointment results or customer reference\n\n💡 WORKFLOW PATTERNS:\n• Customer inquiry → get_events → (show results)\n• Modification prep → get_events → update_appointment/cancel_appointment\n\n🎯 AGENT STRATEGY: Use broad searches for finding, specific event_id for verification.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "🔗 FROM list_calendars: Calendars to search. Use specific calendars if known ('service' for maintenance, 'sales' for test drives) or multiple calendars for broad search."
                            },
                            "event_id": {
                                "type": "string",
                                "description": "SPECIFIC EVENT LOOKUP: Use when customer references specific appointment or you have event_id from previous booking. Gets exact appointment details."
                            },
                            "time_min": {
                                "type": "string",
                                "format": "date-time",
                                "description": "SEARCH START TIME: Customer context - 'today' = today 12am, 'this week' = Monday 12am, 'tomorrow' = tomorrow 12am. For date range searches."
                            },
                            "time_max": {
                                "type": "string",
                                "format": "date-time", 
                                "description": "SEARCH END TIME: End of search range. 'today' = today 11:59pm, 'this week' = Sunday 11:59pm, 'next month' = end of next month."
                            },
                            "query": {
                                "type": "string",
                                "description": "TEXT SEARCH: Customer name, vehicle model, appointment type. Examples: 'John Smith', 'Honda Civic', 'test drive', 'oil change'. Searches title and description."
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 2500,
                                "default": 250,
                                "description": "RESULTS LIMIT: Use smaller numbers (10-50) for customer-facing results, larger for administrative searches. Default 250 is good for most searches."
                            },
                            "order_by": {
                                "type": "string",
                                "enum": ["startTime", "updated"],
                                "default": "startTime",
                                "description": "SORT ORDER: 'startTime' = chronological (normal), 'updated' = most recently modified first (for finding recent changes)."
                            },
                            "show_deleted": {
                                "type": "boolean",
                                "default": False,
                                "description": "DELETED EVENTS: Keep FALSE (default). Use TRUE only for administrative purposes or when customer asks about canceled appointments."
                            },
                            "time_zone": {
                                "type": "string",
                                "description": "CUSTOMER TIMEZONE: Use customer's timezone for displaying times correctly. Same as used in availability checks."
                            }
                        },
                        "required": []
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/get-events")
            ),
            
            # 4. Create Appointment - FINAL BOOKING TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="create_appointment",
                    description="📝 APPOINTMENT BOOKING TOOL - FINAL STEP in appointment scheduling. Creates confirmed appointments and sends customer notifications.\n\n⚡ CONVERSATION TRIGGERS:\n• Booking confirmation: 'Book it', 'Schedule that time', 'Confirm the appointment'\n• Customer commitment: After time slot selection and customer agreement\n• Completed workflow: After list_calendars → check_availability → customer choice\n• Direct booking: 'Schedule test drive Friday 2pm' (still need availability check first)\n\n🔗 PARAMETER SOURCES:\n• calendar_id: FROM list_calendars → 'calendarId' (customer's chosen calendar)\n• start_time: FROM check_availability → customer's selected time slot\n\n💡 REQUIRED WORKFLOW: \nlist_calendars → check_availability → create_appointment\n\n🎯 AGENT STRATEGY: NEVER create appointments without checking availability first. Always confirm details with customer before booking.\n\n⚠️ CRITICAL: This tool creates REAL appointments and sends notifications. Use only when customer has committed to the booking.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "🔗 FROM list_calendars: Use the 'calendarId' from customer's selected calendar. REQUIRED - must match exact calendar ID from list_calendars results."
                            },
                            "summary": {
                                "type": "string",
                                "description": "APPOINTMENT TITLE: Create descriptive title with key info. PATTERN: '[Type] - [Vehicle/Service] - [Customer Name]'. Examples: 'Test Drive - Honda Civic - John Smith', 'Service Appointment - Oil Change - Jane Doe'."
                            },
                            "description": {
                                "type": "string",
                                "description": "APPOINTMENT DETAILS: Include customer requirements, vehicle specifics, contact info, special requests. TEMPLATE: 'Customer: [name], Phone: [phone], Vehicle Interest: [vehicle], Notes: [any special requirements]'."
                            },
                            "start_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "🔗 FROM check_availability: Use EXACT time from customer's selected available slot. MUST be ISO datetime format. CRITICAL: Must be an available time confirmed by check_availability."
                            },
                            "customer_email": {
                                "type": "string",
                                "format": "email",
                                "description": "CUSTOMER EMAIL: REQUIRED for calendar invite and notifications. Ask customer if not provided. Must be valid email format. This email receives the appointment confirmation."
                            },
                            "location": {
                                "type": "string",
                                "description": "MEETING LOCATION: Specific location for appointment. Examples: 'Dealership Showroom - 123 Main St', 'Service Bay 2', 'Sales Office'. Include address if customer is new."
                            }
                        },
                        "required": ["calendar_id", "summary", "start_time", "customer_email"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/create-event")
            ),
            
            # 5. Update Appointment - MODIFICATION TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="update_appointment",
                    description="✏️ APPOINTMENT MODIFICATION TOOL - Use when customers need to change existing appointments. Handles rescheduling, detail updates, and attendee changes.\n\n⚡ CONVERSATION TRIGGERS:\n• Rescheduling: 'Change my appointment', 'Different time', 'Move to Friday'\n• Detail updates: 'Add phone number', 'Different vehicle', 'Update notes'\n• Attendee changes: 'Add my spouse', 'Remove attendee', 'Change contact'\n• Location changes: 'Different location', 'Service instead of sales'\n• Correction requests: 'Wrong time booked', 'Fix the details'\n\n🔗 PARAMETER SOURCES:\n• calendar_id: FROM get_events results (where appointment was found)\n• event_id: FROM get_events results (specific appointment to modify)\n• start_time: FROM check_availability (if rescheduling to new time)\n\n💡 WORKFLOW: get_events → [check_availability if rescheduling] → update_appointment\n\n🎯 AGENT STRATEGY: Use get_events first to find the appointment, then update only the fields that need changing. Always confirm changes with customer.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "🔗 FROM get_events: Use 'organizer.email' or exact calendar_id where the appointment currently exists. REQUIRED to identify the appointment location."
                            },
                            "event_id": {
                                "type": "string",
                                "description": "🔗 FROM get_events: Use exact 'id' field from the appointment you want to modify. REQUIRED - identifies the specific appointment to update."
                            },
                            "summary": {
                                "type": "string",
                                "description": "NEW TITLE: Only provide if customer wants to change the appointment title. Keep same format: '[Type] - [Vehicle/Service] - [Customer Name]'."
                            },
                            "description": {
                                "type": "string",
                                "description": "NEW DETAILS: Only provide if updating appointment details, adding notes, or changing customer requirements. Preserves existing info unless specifically changed."
                            },
                            "start_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "NEW START TIME: Only for rescheduling. MUST come from check_availability results. Use ISO datetime format. Requires prior availability check."
                            },
                            "end_time": {
                                "type": "string", 
                                "format": "date-time",
                                "description": "NEW END TIME: Usually auto-calculated from start_time. Only specify if customer wants different appointment duration."
                            },
                            "timezone": {
                                "type": "string",
                                "description": "TIMEZONE CHANGE: Only if customer moved locations or wants different timezone. Use same format as other calendar tools."
                            },
                            "location": {
                                "type": "string",
                                "description": "NEW LOCATION: Only if changing meeting location. Examples: moving from 'Sales Office' to 'Service Bay 3', or updating address."
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string", "format": "email"},
                                "description": "ATTENDEE EMAILS: Email addresses for attendee changes. Use with attendee_action to specify what to do with these emails."
                            },
                            "attendee_action": {
                                "type": "string",
                                "enum": ["replace", "add", "remove"],
                                "default": "replace",
                                "description": "ATTENDEE MODIFICATION: 'replace' = new attendee list, 'add' = add to existing, 'remove' = remove specified emails."
                            },
                            "create_google_meet": {
                                "type": "boolean",
                                "description": "VIDEO MEETING: TRUE = add Google Meet link, FALSE = remove Google Meet. Only specify if customer requests video capability change."
                            },
                            "send_notifications": {
                                "type": "string",
                                "enum": ["all", "external_only", "none"],
                                "default": "all",
                                "description": "NOTIFICATIONS: 'all' = notify everyone (default), 'external_only' = only customer, 'none' = silent update. Use 'all' for customer changes."
                            }
                        },
                        "required": ["calendar_id", "event_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/update-event")
            ),
            
            # 6. Cancel Appointment - CANCELLATION TOOL
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="cancel_appointment",
                    description="❌ APPOINTMENT CANCELLATION TOOL - Use when customers need to cancel appointments. Handles clean cancellation with proper notifications.\n\n⚡ CONVERSATION TRIGGERS:\n• Direct cancellation: 'Cancel my appointment', 'Delete the booking', 'I can't make it'\n• Schedule conflicts: 'Something came up', 'Need to cancel Friday's appointment'\n• Rescheduling (part 1): 'Cancel this and book new time' → cancel → create_appointment\n• Emergency cancellation: 'Emergency - cancel everything today'\n• Customer no-show follow-up: Administrative cancellation after missed appointments\n\n🔗 PARAMETER SOURCES:\n• calendar_id: FROM get_events results (where appointment exists)\n• event_id: FROM get_events results (specific appointment to cancel)\n\n💡 WORKFLOW: get_events (to find appointment) → cancel_appointment\n\n🎯 AGENT STRATEGY: Always confirm cancellation details with customer. Ask if they want to reschedule instead of just cancel.\n\n⚠️ CRITICAL: This permanently deletes appointments and notifies attendees. Use only when customer confirms cancellation.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "🔗 FROM get_events: Use exact calendar_id where the appointment exists. REQUIRED to locate the appointment for cancellation."
                            },
                            "event_id": {
                                "type": "string",
                                "description": "🔗 FROM get_events: Use exact 'id' field from the appointment to cancel. REQUIRED - identifies the specific appointment to delete permanently."
                            },
                            "send_notifications": {
                                "type": "boolean",
                                "default": True,
                                "description": "CUSTOMER NOTIFICATION: TRUE = notify customer of cancellation (default - professional). FALSE = silent cancellation (use only for spam/test appointments)."
                            },
                            "force_delete": {
                                "type": "boolean",
                                "default": False,
                                "description": "FORCE DELETION: FALSE = normal cancellation (default). TRUE = force delete even with errors. Use only if normal cancellation fails due to permission issues."
                            }
                        },
                        "required": ["calendar_id", "event_id"]
                    }
                ),
                server=Server(url=f"{self.server_base_url}/api/v1/calendar/delete-event")
            )
        ]
    
    def get_knowledge_base_tools(self) -> List[CreateFunctionToolDto]:
        """Get knowledge base management tools - only sync tool for administrative use."""
        return [
            # Sync Knowledge Base to VAPI - ADMINISTRATIVE TOOL (NOT REGISTERED WITH ASSISTANT)
            CreateFunctionToolDto(
                function=OpenAiFunction(
                    name="sync_knowledge_base_to_vapi",
                    description="🔄 ADMINISTRATIVE SYNC TOOL - Updates VAPI knowledge base files with latest dealership content. Used for content management, not customer interactions.\n\n⚡ ADMINISTRATIVE USE:\n• Content updates: New policies, financing rates, hours\n• Promotional updates: New deals, seasonal offers\n• System maintenance: Knowledge base synchronization\n• Initial setup: Upload knowledge base to VAPI\n\n🔧 TECHNICAL FUNCTION:\n• Fetches latest content from GitHub sources\n• Uploads/updates VAPI knowledge base files\n• Makes content available to voice assistant\n• Maintains content synchronization\n\n⚠️ NOTE: This tool uploads knowledge to VAPI files. The assistant accesses this knowledge directly through VAPI's attached files, not through tool calls.",
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
        """Get all 11 operational automotive tools (inventory + calendar only)."""
        tools = []
        tools.extend(self.get_inventory_tools())  # 5 tools
        tools.extend(self.get_calendar_tools())   # 6 tools
        # Note: Knowledge base tools are for admin use only, not registered with assistant
        return tools
    
    async def register_all_tools(self) -> List[str]:
        """Register all 11 operational tools with VAPI and return list of tool IDs."""
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
                name="Premier Auto Dealership Voice Assistant",
                model={
                    "provider": "openai",
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": """[Role]
You're Alex, an AI assistant for Premier Auto Dealership. Your primary task is to help customers find vehicles, book test drives, schedule service appointments, and provide dealership information.

[Context]
You're engaged with customers calling about automotive needs. Stay focused on vehicle inventory, appointments, and dealership services. You have access to the dealership's complete knowledge base containing information about company history, financing options, services offered, and current promotions. Use this attached knowledge base to answer customer questions. Once connected to a customer, proceed to the Conversation Flow section. Do not invent information not drawn from your knowledge base or tool results. Answer only questions related to automotive services and vehicle inventory.

[Response Handling]
When asking any question from the 'Conversation Flow' section, evaluate the customer's response to determine if it qualifies as a valid answer. Use context awareness to assess relevance and appropriateness. If the response is valid, proceed to the next relevant question or instructions. Avoid infinite loops by moving forward when a clear answer cannot be obtained.

[Warning]
Do not modify or attempt to correct user input parameters or user input. Pass them directly into the available automotive tools as given.

[Response Guidelines]
Keep responses brief.
Ask one question at a time, but combine related questions where appropriate.
Maintain a warm, helpful, and professional tone.
Answer only the question posed by the user.
Begin responses with direct answers, without introducing additional data.
If unsure or data is unavailable, use the appropriate automotive tools instead of guessing.
Present dates in a clear format (e.g., January Twenty Four) and do not mention years in dates.
Present time in a clear format (e.g. Four Thirty PM) like: 2 pm can be spelled: two pee em
Speak dates gently using English words instead of numbers.
Never say the word 'function' nor 'tools' nor the name of the available automotive tools.
Never say ending the call.
If you think you are about to transfer the call, do not send any text response. Simply trigger the appropriate action silently.

[Error Handling]
If the customer's response is unclear, ask clarifying questions. If you encounter any issues, inform the customer politely and ask them to repeat their request.

[Conversation Flow]
1. Greet: "Hi! This is Alex from Premier Auto Dealership. How can I help you today?"
2. Listen for customer intent and proceed to appropriate section:
   - Vehicle shopping keywords ("car", "SUV", "truck", "looking for", "need a vehicle"): Proceed to 'Vehicle Shopping Flow'
   - Test drive keywords ("test drive", "drive the car", "see the vehicle"): Proceed to 'Test Drive Booking'
   - Service keywords ("service", "oil change", "maintenance", "repair"): Proceed to 'Service Appointment Booking'
   - Information keywords ("financing", "hours", "deals", "about your dealership"): Proceed to 'Information Requests'

[Vehicle Shopping Flow]
1. Use 'check_vehicle_inventory' to search available vehicles based on customer preferences
2. Present 2-3 best matches from results
3. Ask: "Would you like more details about any of these vehicles?"
4. If customer shows interest in specific vehicle:
   - Use 'get_vehicle_details' for that vehicle
   - Present key information briefly
5. If customer asks about pricing: Use 'get_vehicle_pricing'
6. Ask: "Would you like to schedule a test drive to see this vehicle in person?"
   - If yes: Proceed to 'Test Drive Booking'
   - If no: Ask if they need anything else

[Test Drive Booking]
1. If vehicle not yet identified, ask: "Which vehicle would you like to test drive?"
   - Use vehicle inventory tools if needed
2. Use 'list_available_calendars' to find sales calendars
3. Ask: "When would you prefer to come in? Morning or afternoon? Which days work best for you?"
4. Use 'check_availability' based on their preferences
5. Present available time slots: "I have appointments available at [times]. Which works best for you?"
6. Ask: "Could you provide your email address for the appointment confirmation?"
7. Use 'create_appointment' with customer details
8. Confirm appointment details
9. Proceed to 'Call Closing'

[Service Appointment Booking]
1. Ask: "What type of service do you need?"
2. Provide service information from your attached knowledge base
3. Use 'list_available_calendars' to find service calendars
4. Ask: "When would you prefer to bring your vehicle in?"
5. Use 'check_availability' for service calendar
6. Present available slots: "I can schedule you for [times]. Which works for you?"
7. Ask: "What's your email address for the confirmation?"
8. Ask: "What's the year, make, and model of your vehicle?"
9. Use 'create_appointment' with service details
10. Confirm appointment details
11. Proceed to 'Call Closing'

[Information Requests]
1. Answer customer questions using your attached knowledge base (dealership info, financing, services, current offers)
2. Provide brief, relevant answer based on customer's question
3. Ask: "Is there anything else you'd like to know about our dealership or services?"
4. If customer has additional questions about vehicles: Proceed to 'Vehicle Shopping Flow'
5. If no additional questions: Proceed to 'Call Closing'

[Call Closing]
Respond: "Is there anything else I can help you with today?" 
- If customer has additional needs: Route to appropriate flow section
- If no additional needs: "Thank you for calling Premier Auto Dealership. Have a great day!"
- End the conversation naturally"""
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