import time
import requests
import json

def test_performance():
    url = "http://127.0.0.1:7000/api/demand-forecast"
    
    # Test payload for 7x8x7 combinations (392 total)
    payload = {
        "city_ids": ["1", "2", "3", "4", "5", "6", "7"],
        "store_ids": ["1", "2", "3", "4", "5", "6", "7", "8"],
        "product_ids": [1, 2, 3, 4, 5, 6, 7],
        "forecast_days": 7
    }
    
    print(f"Testing 7x8x7 combinations (392 total)...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            print(f"Forecasts: {len(data.get('demand_forecasts', {}))}")
            print(f"Insights: {len(data.get('demand_insights', []))}")
            print(f"Recommendations: {len(data.get('inventory_recommendations', []))}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_performance()

