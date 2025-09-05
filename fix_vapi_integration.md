# Vapi Webhook Integration: Complete Implementation Specification

## Executive Summary

We will implement a single unified webhook endpoint (`/webhook/vapi`) to handle all Vapi tool calls, completely replacing the existing 13 REST endpoints. This webhook-first architecture aligns perfectly with Vapi's design and eliminates the architectural mismatch that caused the original integration failure.

## Current State Analysis

### Existing Architecture Problems
- **14 REST Endpoints** under `/api/v1/` expecting traditional Pydantic models
- **Incompatible Request Format**: Our endpoints expect tool-specific request bodies, Vapi sends `toolCallList` array
- **Incompatible Response Format**: We return `ToolResponse` with metadata, Vapi expects simple `results` array
- **No Tool Call ID Handling**: Cannot match responses to requests
- **Architecture Mismatch**: REST pattern vs Vapi's webhook pattern

### Vapi Requirements
- Single webhook endpoint handling all tool calls
- `toolCallList` array with multiple concurrent calls
- `toolCallId` tracking for request/response matching
- Arguments passed as dictionary (not JSON string)
- Results can be any JSON-serializable type

## Implementation Scope

### Dependencies to Add

**Required Python Package:**
- `vapi-server-sdk` (Vapi SDK) - Already installed and added to pyproject.toml
- This provides all the Pydantic models needed for request/response handling

**Note**: This project uses `uv` for Python package management instead of pip or poetry.

### Existing Files to Modify

#### 1. **api/app.py** (Lines: 1-88)
- **Line 84**: Add inclusion of new vapi_webhook router
- **Action**: Import and include the vapi_webhook router module

#### 2. **api/routes.py** (Lines: 1-403)
- **Lines 183-310**: Calendar endpoints to be removed in Phase 4
- **Lines 317-333**: Knowledge Base endpoints to be removed in Phase 4
- **Lines 339-401**: Inventory endpoints to be removed in Phase 4
- **Action**: These endpoints will be deleted only after successful validation of webhook

#### 3. **api/models.py**
- **Existing models**: Keep all existing Pydantic models (they will be reused for validation)
- **Action**: Add new Vapi-specific request/response models

### New Files to Create

#### 1. **api/vapi_webhook.py**
This file will contain the entire webhook implementation including:
- Vapi request/response models
- Tool registry mapping
- Main webhook handler
- Individual tool call processor
- Error handling logic

#### 2. **tests/test_vapi_webhook.py** (Optional - Phase 3)
Test file for webhook functionality (if automated testing is added later)

### Files NOT in Scope (No Changes Required)

1. **calendar_tools/** - All calendar tool implementations remain unchanged
2. **kb_tools/** - Knowledge base tools remain unchanged  
3. **inventory/** - Inventory tools remain unchanged
4. **logging_config.py** - Existing logging configuration is sufficient
5. **middleware.py** - No middleware changes needed

## Implementation Rules and Constraints

### Strict Requirements

1. **Tool Functions Must Not Change**
   - Existing tool functions in calendar_tools/, kb_tools/, and inventory/ must remain completely unchanged
   - The webhook acts purely as a translation layer

2. **Model Reuse**
   - Reuse existing Pydantic models from api/models.py for parameter validation
   - Do not duplicate or recreate existing request models

3. **Naming Consistency**
   - Tool names in the registry MUST exactly match Vapi function names
   - Case-sensitive matching is required

4. **Calendar Service Handling**
   - Calendar tools require the calendar service from app.state
   - Service must be injected into tool kwargs when `requires_service` is True

5. **Error Handling**
   - Errors must be returned in the results array, not as HTTP errors
   - Always include toolCallId in error responses
   - Never let exceptions bubble up to HTTP level

6. **Concurrent Execution**
   - Multiple tool calls in a single request must execute concurrently
   - Use asyncio.gather with return_exceptions=True

7. **Backward Compatibility (Phases 1-3)**
   - REST endpoints must remain functional during migration
   - Do not modify existing endpoints until Phase 4

## Detailed Implementation Specifications

### Vapi Request/Response Models

#### Using Vapi SDK Types (No Custom Models Needed)

The Vapi Python SDK provides pre-built Pydantic models that we should use instead of creating custom ones:

**Required Imports from Vapi SDK:**
- `from vapi.types.server_message_tool_calls import ServerMessageToolCalls`
- `from vapi.types.server_message_response_tool_calls import ServerMessageResponseToolCalls`
- `from vapi.types.tool_call_result import ToolCallResult`
- `from vapi.types.tool_call import ToolCall`
- `from vapi.types.tool_call_function import ToolCallFunction`

**Note**: The `vapi-server-sdk` package is already installed using `uv` and available for import.

#### Request Structure:

1. **Webhook Request Wrapper** (Create this one custom model)
   - Name: `VapiWebhookRequest`
   - Single attribute: `message` of type `ServerMessageToolCalls`
   - This wraps the Vapi SDK type for FastAPI endpoint

2. **ServerMessageToolCalls** (from Vapi SDK)
   - Already contains all required fields:
   - `timestamp`: Optional float
   - `type`: Literal "tool-calls"
   - `tool_call_list`: List of ToolCall objects (aliased from toolCallList)
   - `tool_with_tool_call_list`: List with tool definitions (aliased from toolWithToolCallList)
   - `artifact`: Optional Artifact object
   - `assistant`: Optional CreateAssistantDto object
   - `customer`: Optional CreateCustomerDto object
   - `call`: Optional Call object
   - `chat`: Optional Chat object
   - `phone_number`: Optional phone number object

3. **ToolCall** (from Vapi SDK)
   - Structure:
   - `id`: String - unique identifier for the tool call
   - `type`: String - type of tool
   - `function`: ToolCallFunction object containing:
     - `name`: String - the function name to call
     - `arguments`: String - JSON string of arguments (needs parsing!)
     
4. **ToolCallFunction** (from Vapi SDK)
   - `name`: String - function name
   - `arguments`: String - JSON string of parameters
   - **Note**: Vapi docs sometimes use "parameters" instead of "arguments", handle both

#### Response Structure:

1. **ServerMessageResponseToolCalls** (from Vapi SDK)
   - Use this directly as the response type
   - Contains:
   - `results`: Optional List of ToolCallResult objects
   - `error`: Optional error message string

2. **ToolCallResult** (from Vapi SDK)
   - For creating individual results per Vapi's response format
   - Required fields to set:
     - `tool_call_id`: String - Must match the request's tool call ID (aliased to toolCallId)
     - `name`: String - Function name that was called
     - `result`: String - Tool execution result (serialize dicts/lists to JSON string)
   - Optional fields:
     - `error`: String - Set if tool execution failed
     - `message`: Optional message to speak to user
     - `metadata`: Optional dictionary of metadata
   - **Important**: Despite SDK typing, Vapi accepts result as JSON string of any structure

#### Benefits of Using SDK Types:
- No need to maintain custom model definitions
- Automatic updates when Vapi changes their API
- Guaranteed compatibility with Vapi's expectations
- Handles field aliasing (e.g., toolCallList → tool_call_list) automatically
- Includes all optional fields that Vapi might send

### Tool Registry Architecture

#### Registry Structure:
- Dictionary mapping tool names to tuples
- Each tuple contains:
  1. Tool function reference (callable)
  2. Pydantic model class for validation (or None)
  3. Configuration dictionary with metadata

#### Registry Entries (Phase 1 - Start with one):
- Key: "get_availability"
- Value: Tuple containing get_availability function, GetAvailabilityRequest model, and config dict with requires_service=True

#### Registry Entries (Phase 2 - Add two more):
- Add "list_calendars" with corresponding function and model
- Add "check_inventory" with corresponding function and model

#### Registry Entries (Phase 3 - Complete all 13):
Calendar tools (6):
- list_calendars
- get_availability
- get_events
- create_appointment (maps to create_appointment function, not create_event)
- update_event
- delete_event

Knowledge Base tools (2):
- fetch_latest_kb (no request model)
- sync_knowledge_base (no request model)

Inventory tools (5):
- check_inventory
- get_expected_delivery_dates
- get_prices
- get_similar_vehicles
- get_vehicle_details

### Webhook Handler Implementation

#### Main Handler Function: `vapi_webhook_handler`
**Inputs**: 
- FastAPI Request object
- VapiWebhookRequest object (wrapper with message: ServerMessageToolCalls)

**Returns**: ServerMessageResponseToolCalls (from Vapi SDK)

**Logic Steps**:
1. Log the complete incoming request as JSON for debugging
   - Serialize the entire message object using Pydantic's dict() method
   - Include all fields from ServerMessageToolCalls
   - Use logger.info with full request serialization
2. Log specific details: 
   - Tool count from message.tool_call_list
   - Tool names from each ToolCall object
   - Call ID from message.call.id if present
   - Assistant info from message.assistant if present
3. Create list of async tasks for each tool call in message.tool_call_list
4. Execute all tasks concurrently using asyncio.gather with return_exceptions=True
5. Build results list:
   - For each result, check if it's an exception
   - If exception, create ToolCallResult with error in result field
   - If success, create ToolCallResult with actual result
6. Create ServerMessageResponseToolCalls with results list
7. Log the complete response before returning
8. Return ServerMessageResponseToolCalls object

#### Tool Processor Function: `process_tool_call`
**Inputs**:
- FastAPI Request object
- ToolCall object (from Vapi SDK)

**Returns**: ToolCallResult (from Vapi SDK)

**Logic Steps**:
1. Extract tool name from ToolCall.function.name
2. Check if tool name exists in registry, raise error if not
3. Extract tool function, request model, and config from registry
4. Parse arguments from ToolCall.function.arguments:
   - Parse JSON string to get dictionary
   - **Important**: Also check for "parameters" field as fallback (Vapi inconsistency)
   - If request model exists, validate parsed arguments using the model
   - Extract validated dictionary with exclude_unset=True
5. If tool requires service (check config):
   - Get calendar service from request.app.state.calendar_service
   - Add service to kwargs
6. Execute tool function with kwargs (await if async)
7. Create ToolCallResult for success:
   - tool_call_id: Use ToolCall.id from the original request
   - name: Use ToolCall.function.name
   - result: JSON serialize tool's return value if dict/list, else convert to string
8. For exceptions:
   - Log error with tool name, call ID, and full exception
   - Return ToolCallResult with:
     - tool_call_id: Still include the original ID
     - name: Tool function name
     - error: Error message string
     - result: Can be None or error details as JSON string

### Tool Registration Updates for Vapi

When registering tools in Vapi:
- Change server URL from individual endpoints to webhook URL
- Example: From `https://domain.com/api/v1/calendar/get-availability` to `https://domain.com/webhook/vapi`
- Keep the same parameter schemas
- Tool name must match exactly with registry keys

### Expected Request Structure Examples

#### Example 1: Single Tool Call (get_availability)
The webhook will receive a VapiWebhookRequest with message (ServerMessageToolCalls) containing:
- message.timestamp: Unix timestamp (e.g., 1678901234567)
- message.type: "tool-calls"
- message.tool_call_list: List with one ToolCall object
  - id: "toolu_01ABC..." (unique identifier)
  - type: "function"
  - function: ToolCallFunction object with:
    - name: "get_availability"
    - arguments: JSON string like "{\"calendar_ids\": [\"primary\"], \"start_time\": \"2024-01-01T09:00:00Z\"}"
- message.tool_with_tool_call_list: List containing tool definition and server info
- message.artifact: Artifact object with messages list
- message.assistant: CreateAssistantDto with name, description, model, voice
- message.call: Call object with ID, org ID, type
- message.customer: Optional customer information
- message.chat: Optional chat context

#### Example 2: Multiple Concurrent Tool Calls
The webhook may receive multiple tools in a single request:
- message.tool_call_list: List with multiple ToolCall objects
  - First ToolCall: get_availability with its arguments
  - Second ToolCall: check_inventory with its arguments  
  - Each with unique ID for response mapping
- All tools execute concurrently using asyncio.gather
- Response (ServerMessageResponseToolCalls) must include:
  - results: List of ToolCallResult objects
  - Each result must have matching toolCallId from original request

### Logging Requirements

The webhook must log:
1. **Full Request on Receipt**: Serialize entire VapiWebhookRequest to JSON and log at INFO level
2. **Request Metadata**: Log separately - timestamp, call ID, org ID, assistant name
3. **Tool Details**: For each tool - name, ID, argument keys (not values for security)
4. **Execution Status**: Log start/completion for each tool
5. **Full Response**: Log complete response before returning
6. **Errors**: Log with full stack trace and context

## Migration Plan - Phased Approach

### Phase 1: Initial Setup & Single Tool Validation
**Goal**: Validate webhook architecture with one tool (get_availability)

**Implementation Tasks**:
1. Create api/vapi_webhook.py with all models and handlers
2. Add minimal tool registry with only get_availability
3. Deploy webhook endpoint to staging/production
4. Update get_availability in Vapi to use webhook URL
5. Test through Vapi voice interface
6. Monitor logs to verify request/response format

**Validation Criteria**:
- Webhook receives requests correctly
- Arguments are properly extracted and validated
- Calendar service is successfully injected
- Response includes correct toolCallId
- Tool executes successfully

### Phase 2: Expand to 3 Tools
**Goal**: Validate concurrent execution and different tool categories

**Implementation Tasks**:
1. Add list_calendars to tool registry (same category)
2. Add check_inventory to tool registry (different category)
3. Update these tools in Vapi to use webhook URL
4. Test each tool individually
5. Test concurrent tool calls if possible

**Validation Criteria**:
- All 3 tools work independently
- Different tool categories work correctly
- Concurrent execution works if tested
- Error handling works for invalid tool names

### Phase 3: Full Migration
**Goal**: Complete migration of all 13 tools

**Implementation Tasks**:
1. Add remaining 10 tools to registry
2. Ensure all function references are imported
3. Verify all request models are mapped correctly
4. Update all tools in Vapi to use webhook URL
5. Test each tool through voice interface

**Validation Criteria**:
- All 13 tools respond correctly
- Performance remains acceptable
- No memory leaks or resource issues
- Error rates are within acceptable limits

### Phase 4: Cleanup (Optional - After Validation)
**Only execute after successful production validation**

**Tasks**:
1. Delete lines 183-401 from api/routes.py (all tool endpoints)
2. Remove create_tool_response wrapper function
3. Remove unused imports from routes.py
4. Update documentation

## Success Criteria

### Phase 1 Success Metrics:
- get_availability works through Vapi webhook
- Response time < 2 seconds
- Correct toolCallId mapping
- No errors in production logs

### Phase 2 Success Metrics:
- 3 tools working correctly
- Successful concurrent execution
- Error handling validated

### Phase 3 Success Metrics:
- All 13 tools operational
- 95%+ success rate
- Average response time < 2 seconds
- Support for 5+ concurrent tool calls

## Risk Factors & Mitigation

### Technical Risks:
1. **Parameter Validation Failures**
   - Risk: Complex nested parameters may not validate correctly
   - Mitigation: Extensive logging at each validation step

2. **Calendar Service Availability**
   - Risk: Service may not be initialized in app.state
   - Mitigation: Proper error messages and fallback behavior

3. **Tool Name Mismatches**
   - Risk: Registry names don't match Vapi function names
   - Mitigation: Strict validation and clear error messages

### Operational Risks:
1. **Production Disruption**
   - Risk: Breaking existing functionality during migration
   - Mitigation: Phased approach with gradual rollout

2. **Debugging Complexity**
   - Risk: Harder to debug issues with single endpoint
   - Mitigation: Comprehensive logging at every step

## Conclusion

This specification provides a complete blueprint for implementing a Vapi webhook integration through a translation layer. The phased approach minimizes risk while the detailed specifications ensure consistent implementation. No existing tool code needs to change - we're only adding a translation layer that bridges Vapi's webhook format with our existing tool functions.