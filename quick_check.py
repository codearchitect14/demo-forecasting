#!/usr/bin/env python3
import requests

r = requests.post('http://127.0.0.1:7000/api/demand-forecast', json={
    'city_ids': ['1'],
    'store_ids': ['1'],
    'product_ids': [1],
    'forecast_days': 7
})

data = r.json()
print(f"Status: {r.status_code}")
print(f"Demand forecasts: {len(data.get('demand_forecasts', {}))}")
print(f"Inventory status: {len(data.get('inventory_status', []))}")
print(f"Insights: {len(data.get('demand_insights', []))}")

if data.get('demand_forecasts'):
    print("✅ Demand forecasting is working!")
else:
    print("❌ Demand forecasting is not working")

