#!/usr/bin/env python3
"""
Simple test script to demonstrate the automotive voice agent API server.
Tests basic endpoints and shows the server is working correctly.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_server():
    """Test the server endpoints."""
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("🚗 Testing Automotive Voice Agent API Server")
        print("=" * 50)
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print()
        
        # Test inventory check endpoint
        print("2. Testing inventory check endpoint...")
        inventory_request = {
            "category": "sedan",
            "max_price": 30000,
            "status": "available"
        }
        response = await client.post(f"{base_url}/inventory/check-inventory", json=inventory_request)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Found {data['data']['total_count']} vehicles")
        print(f"   Execution time: {data.get('execution_time_ms', 0):.2f}ms")
        
        # Show first vehicle
        if data['data']['vehicles']:
            vehicle = data['data']['vehicles'][0]
            print(f"   Sample vehicle: {vehicle['brand']} {vehicle['model']} - ${vehicle['price']:,}")
        print()
        
        # Test vehicle details endpoint
        if data['data']['vehicles']:
            print("3. Testing vehicle details endpoint...")
            vehicle_id = data['data']['vehicles'][0]['vehicle_id']
            details_request = {
                "vehicle_id": vehicle_id,
                "include_pricing": True
            }
            response = await client.post(f"{base_url}/inventory/get-vehicle-details", json=details_request)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                details_data = response.json()
                vehicle_data = details_data['data']
                vehicle_info = vehicle_data.get('vehicle', {})
                print(f"   Vehicle: {vehicle_info.get('brand', 'N/A')} {vehicle_info.get('model', 'N/A')}")
                print(f"   Category: {vehicle_info.get('category', 'N/A')}")
                if 'features' in vehicle_data:
                    print(f"   Features: {len(vehicle_data['features'])} features")
                if 'pricing' in vehicle_data:
                    pricing = vehicle_data['pricing']
                    print(f"   Price: ${pricing.get('current_price_dollars', 0):,}")
            else:
                print(f"   Error: {response.text}")
            print()
        
        print("✅ Server test completed successfully!")
        print("📖 View full API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(test_server())
