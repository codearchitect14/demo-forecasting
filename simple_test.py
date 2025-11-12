#!/usr/bin/env python3
import time
import requests

print("Testing with debug logging...")
start = time.time()

r = requests.post('http://127.0.0.1:7000/api/demand-forecast', json={
    'city_ids': ['1'],
    'store_ids': ['1'],
    'product_ids': [1],
    'forecast_days': 7
})

end = time.time()
data = r.json()

print(".2f")
print(f"Status: {r.status_code}")
print(f"Demand forecasts: {len(data.get('demand_forecasts', {}))}")
print(f"Inventory status: {len(data.get('inventory_status', []))}")
print(f"Insights: {len(data.get('demand_insights', []))}")

