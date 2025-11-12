#!/usr/bin/env python3
"""
Debug performance script to identify bottlenecks
"""
import time
import requests
import json

def debug_performance():
    """Debug performance by testing different endpoints and sizes"""

    url = "http://127.0.0.1:7000/api/demand-forecast"

    test_cases = [
        ("1x1x1", ["1"], ["1"], [1]),
        ("2x2x2", ["1", "2"], ["1", "2"], [1, 2]),
        ("3x3x3", ["1", "2", "3"], ["1", "2", "3"], [1, 2, 3]),
    ]

    print("🔍 Performance Debug Results")
    print("=" * 50)

    for name, cities, stores, products in test_cases:
        print(f"\n📊 Testing {name} ({len(cities)}×{len(stores)}×{len(products)} = {len(cities)*len(stores)*len(products)} combos)")

        payload = {
            "city_ids": cities,
            "store_ids": stores,
            "product_ids": products,
            "forecast_days": 7
        }

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=60)
            end_time = time.time()

            total_time = end_time - start_time

            if response.status_code == 200:
                data = response.json()
                combos_returned = len(data.get('demand_forecasts', {}))
                insights = len(data.get('demand_insights', []))
                recommendations = len(data.get('inventory_recommendations', []))

                print(f"   ⏱️  Total time: {total_time:.2f}s")
                print(f"   📦 Combinations: {combos_returned}")
                print(f"   📋 Insights: {insights}")
                print(f"   💡 Recommendations: {recommendations}")

                # Calculate per-combo time
                if combos_returned > 0:
                    per_combo_time = total_time / combos_returned
                    print(f"   ⚡ Per combo: {per_combo_time:.3f}s")
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")

        except Exception as e:
            print(f"💥 ERROR: {e}")

    print("\n" + "=" * 50)
    print("📈 Analysis:")
    print("   - Look for non-linear scaling (time per combo increases)")
    print("   - Check if inventory vs forecasting is the bottleneck")
    print("   - Compare with original 242s for 5x5x5")

if __name__ == "__main__":
    debug_performance()
