"""
Vapi webhook implementation for automotive voice agent.
Single unified webhook endpoint handling all Vapi tool calls.
"""

import asyncio
import json
from typing import Dict, Any, Tuple, Optional, Callable
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

# Vapi SDK imports for proper request/response handling
from vapi.types.server_message_tool_calls import ServerMessageToolCalls
from vapi.types.server_message_response_tool_calls import ServerMessageResponseToolCalls
from vapi.types.tool_call_result import ToolCallResult
from vapi.types.tool_call import ToolCall

# Import existing tool functions (Phase 1: only get_availability)
from calendar_tools.tools.get_availability import get_availability

# Import existing Pydantic models for validation
from .models import GetAvailabilityRequest

# Import logging
from logging_config import logger

# Create router for webhook endpoints
webhook_router = APIRouter(prefix="/webhook")


# =============================================================================
# Vapi Request Wrapper Model
# =============================================================================

class VapiWebhookRequest(BaseModel):
    """Wrapper for Vapi webhook requests using SDK types."""
    message: ServerMessageToolCalls


# =============================================================================
# Tool Registry (Phase 1: Only check_availability)
# =============================================================================

# Tool registry mapping: tool_name -> (function, request_model, config)
TOOL_REGISTRY: Dict[str, Tuple[Callable, Optional[type], Dict[str, Any]]] = {
    "check_availability": (
        get_availability,
        GetAvailabilityRequest,
        {"requires_service": True}
    )
}


# =============================================================================
# Tool Processing Functions
# =============================================================================

async def process_tool_call(request: Request, tool_call: ToolCall) -> ToolCallResult:
    """
    Process a single tool call and return the result.
    
    Args:
        request: FastAPI Request object (for accessing app.state)
        tool_call: ToolCall object from Vapi SDK
        
    Returns:
        ToolCallResult: Result for this specific tool call
    """
    tool_name = tool_call.function.name
    tool_call_id = tool_call.id
    
    try:
        logger.info(f"Processing tool call: {tool_name}", 
                   extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
        
        # Check if tool exists in registry
        if tool_name not in TOOL_REGISTRY:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg, extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
            return ToolCallResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                error=error_msg
            )
        
        # Get tool function, request model, and config from registry
        tool_func, request_model, config = TOOL_REGISTRY[tool_name]
        
        # Parse arguments from JSON string
        try:
            # Parse the arguments JSON string
            arguments = json.loads(tool_call.function.arguments)
            logger.debug(f"Parsed arguments for {tool_name}", 
                        extra={"tool_name": tool_name, "argument_keys": list(arguments.keys())})
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in arguments: {str(e)}"
            logger.error(error_msg, extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
            return ToolCallResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                error=error_msg
            )
        
        # Validate arguments using request model if provided
        tool_kwargs = {}
        if request_model:
            try:
                validated_request = request_model(**arguments)
                tool_kwargs = validated_request.model_dump(exclude_unset=True)
                logger.debug(f"Arguments validated for {tool_name}")
            except Exception as e:
                error_msg = f"Argument validation failed: {str(e)}"
                logger.error(error_msg, extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
                return ToolCallResult(
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    error=error_msg
                )
        else:
            # No validation model, use arguments directly
            tool_kwargs = arguments
        
        # Inject calendar service if required
        if config.get("requires_service", False):
            if not hasattr(request.app.state, 'calendar_service') or request.app.state.calendar_service is None:
                error_msg = "Calendar service not available"
                logger.error(error_msg, extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
                return ToolCallResult(
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    error=error_msg
                )
            tool_kwargs["service"] = request.app.state.calendar_service
            logger.debug(f"Calendar service injected for {tool_name}")
        
        # Execute the tool function
        logger.debug(f"Executing tool function: {tool_name}")
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**tool_kwargs)
        else:
            result = tool_func(**tool_kwargs)
        
        # Serialize result for Vapi response
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, default=str)
        else:
            result_str = str(result)
        
        logger.info(f"Tool {tool_name} executed successfully", 
                   extra={"tool_name": tool_name, "tool_call_id": tool_call_id})
        
        return ToolCallResult(
            tool_call_id=tool_call_id,
            name=tool_name,
            result=result_str
        )
        
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg, 
                    extra={"tool_name": tool_name, "tool_call_id": tool_call_id, "error": str(e)},
                    exc_info=True)
        
        return ToolCallResult(
            tool_call_id=tool_call_id,
            name=tool_name,
            error=error_msg
        )


# =============================================================================
# Main Webhook Handler
# =============================================================================

@webhook_router.post("/vapi")
async def vapi_webhook_handler(request: Request, webhook_request: VapiWebhookRequest) -> ServerMessageResponseToolCalls:
    """
    Main Vapi webhook handler for all tool calls.
    
    Args:
        request: FastAPI Request object
        webhook_request: VapiWebhookRequest containing ServerMessageToolCalls
        
    Returns:
        ServerMessageResponseToolCalls: Response with results for all tool calls
    """
    message = webhook_request.message
    
    try:
        # Log the complete incoming request
        logger.info("Vapi webhook request received", 
                   extra={
                       "complete_request": webhook_request.model_dump(),
                       "request_data": message.model_dump(),
                       "tool_count": len(message.tool_call_list) if message.tool_call_list else 0,
                       "timestamp": message.timestamp,
                       "call_id": message.call.id if message.call else None,
                       "assistant": message.assistant.name if message.assistant else None
                   })
        
        # Check if tool_call_list exists and is not None
        if not message.tool_call_list:
            error_msg = "No tool calls found in request"
            logger.error(error_msg)
            return ServerMessageResponseToolCalls(error=error_msg)
        
        # Log tool details
        tool_names = [tool_call.function.name for tool_call in message.tool_call_list]
        logger.info(f"Processing {len(message.tool_call_list)} tool calls", 
                   extra={"tool_names": tool_names})
        
        # Create tasks for concurrent execution
        tasks = []
        for tool_call in message.tool_call_list:
            task = process_tool_call(request, tool_call)
            tasks.append(task)
        
        # Execute all tool calls concurrently
        logger.debug("Starting concurrent tool execution")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        tool_call_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions from gather
                tool_call = message.tool_call_list[i]
                error_result = ToolCallResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                    error=f"Execution exception: {str(result)}"
                )
                tool_call_results.append(error_result)
                logger.error(f"Exception in tool execution: {result}", 
                           extra={"tool_call_id": tool_call.id, "tool_name": tool_call.function.name})
            else:
                tool_call_results.append(result)
        
        # Create response
        response = ServerMessageResponseToolCalls(results=tool_call_results)
        
        # Log complete response
        logger.info("Vapi webhook response prepared", 
                   extra={
                       "response_data": response.model_dump(),
                       "result_count": len(tool_call_results),
                       "successful_tools": len([r for r in tool_call_results if not r.error])
                   })
        
        return response
        
    except Exception as e:
        # Handle any top-level exceptions
        logger.error("Webhook handler failed", 
                    extra={"error": str(e)},
                    exc_info=True)
        
        # Return error response - still need to return proper Vapi format
        error_response = ServerMessageResponseToolCalls(
            error=f"Webhook processing failed: {str(e)}"
        )
        return error_response