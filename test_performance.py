#!/usr/bin/env python3
"""
Quick performance test for demand/inventory optimization
"""
import asyncio
import time
import json
import requests

async def test_demand_forecast_performance():
    """Test the demand forecast endpoint performance"""
    url = "http://127.0.0.1:7000/api/demand-forecast"

    # 5x5x5 test payload
    payload = {
        "city_ids": ["1", "2", "3", "4", "5"],
        "store_ids": ["1", "2", "3", "4", "5"],
        "product_ids": [1, 2, 3, 4, 5],
        "forecast_days": 30
    }

    print(f"Testing {len(payload['city_ids'])}×{len(payload['store_ids'])}×{len(payload['product_ids'])} = {len(payload['city_ids']) * len(payload['store_ids']) * len(payload['product_ids'])} combinations")

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, timeout=300)  # 5 minute timeout

        end_time = time.time()
        total_time = end_time - start_time

        print(".3f"
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Request successful!")
            print(f"📊 Response size: {len(json.dumps(data))} characters")
            print(f"🔢 Combinations returned: {len(data.get('demand_forecasts', {}))}")
            print(f"📋 Insights generated: {len(data.get('demand_insights', []))}")
            print(f"💡 Recommendations: {len(data.get('inventory_recommendations', []))}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 300 seconds")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection failed - make sure server is running on http://localhost:7000")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_demand_forecast_performance())
