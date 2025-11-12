import time
import requests
import json

def debug_test():
    url = "http://127.0.0.1:7000/api/demand-forecast"
    
    # Test with minimal payload
    payload = {
        "city_ids": ["1"],
        "store_ids": ["1"],
        "product_ids": [1],
        "forecast_days": 7
    }
    
    print(f"Testing minimal 1x1x1 combination...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            print(f"Error: {data.get('error', 'None')}")
            print(f"Forecasts: {len(data.get('demand_forecasts', {}))}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test()

