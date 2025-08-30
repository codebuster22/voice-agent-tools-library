from vapi import AsyncVapi
from dotenv import load_dotenv
load_dotenv()
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.vapi_settings import vapi_settings

async def delete_all_tools():
    """Delete all tools from VAPI."""
    client = AsyncVapi(token=vapi_settings.vapi_api_token)
    tools = await client.tools.list()
    coroutines = [client.tools.delete(tool.id) for tool in tools]
    results = await asyncio.gather(*coroutines)
    print(results)
    print(f"Deleted {len(results)} tools")

if __name__ == "__main__":
    asyncio.run(delete_all_tools())