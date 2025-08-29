#!/usr/bin/env python3
"""
Register all 13 automotive tools with VAPI and create voice assistant.
One-time setup script for VAPI integration.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vapi_integration.tool_manager import VapiToolManager
from config.vapi_settings import vapi_settings


async def main():
    """Register all tools and create VAPI assistant."""
    try:
        print("🚀 Starting VAPI integration setup...")
        print(f"📍 Server URL: {vapi_settings.server_base_url}")
        print(f"🔗 Webhook URL: {vapi_settings.webhook_url}")
        
        # Initialize tool manager
        manager = VapiToolManager()
        
        # Register all 13 tools
        print("\n📋 Registering automotive dealership tools...")
        tool_ids = await manager.register_all_tools()
        
        if not tool_ids:
            print("❌ No tools were registered successfully")
            return
        
        print(f"\n✅ Successfully registered {len(tool_ids)} tools with direct endpoint mapping:")
        
        # Show tool mapping summary
        tool_definitions = manager.get_all_tool_definitions()
        for i, (tool_id, tool_def) in enumerate(zip(tool_ids, tool_definitions), 1):
            endpoint = tool_def["server"]["url"].split("/api/v1/")[-1]
            print(f"   {i:2d}. {tool_def['name']} → /api/v1/{endpoint}")
        
        # Create voice assistant
        print("\n🎙️  Creating automotive voice assistant with direct tool access...")
        assistant_id = await manager.create_automotive_assistant(tool_ids)
        
        print(f"\n🎉 VAPI Integration Complete!")
        print(f"🤖 Assistant ID: {assistant_id}")
        print(f"📞 Voice assistant ready with {len(tool_ids)} direct-mapped tools")
        
        # Detailed summary
        print(f"\n📊 Direct Tool Mapping Summary:")
        print(f"   • Inventory Tools: 5 tools → 5 direct endpoints ✅")
        print(f"   • Calendar Tools: 6 tools → 6 direct endpoints ✅") 
        print(f"   • Knowledge Base Tools: 2 tools → 2 direct endpoints ✅")
        print(f"   • Total: {len(tool_ids)}/13 tools with direct FastAPI mapping ✅")
        print(f"   • Voice Assistant: Created with all tools ✅")
        
        print(f"\n🔗 Tool Architecture:")
        print(f"   • Each VAPI tool calls its specific FastAPI endpoint directly")
        print(f"   • No webhook routing layer - clean direct mapping")
        print(f"   • Comprehensive parameter validation with voice optimization")
        print(f"   • Existing business logic unchanged")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Test tools via VAPI dashboard: https://dashboard.vapi.ai")
        print(f"   2. Add ASSISTANT_ID={assistant_id} to your .env file")
        print(f"   3. Configure phone number or web widget for customer access")
        print(f"   4. Test voice interactions with inventory search and appointment booking")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure VAPI_API_TOKEN is set in your environment")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())