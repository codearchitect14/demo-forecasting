import time
import requests
import json

def test_small():
    url = "http://127.0.0.1:7000/api/demand-forecast"
    
    # Test with smaller combination first
    payload = {
        "city_ids": ["1", "2"],
        "store_ids": ["1", "2"],
        "product_ids": [1, 2],
        "forecast_days": 7
    }
    
    print(f"Testing 2x2x2 combinations (8 total)...")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            print(f"Forecasts: {len(data.get('demand_forecasts', {}))}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_small()

