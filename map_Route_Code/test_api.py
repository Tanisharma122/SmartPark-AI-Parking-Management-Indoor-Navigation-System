import requests

BACKEND_URL = "http://127.0.0.1:8000"
API_KEY = "sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f"
HEADERS = {"X-API-KEY": API_KEY}

def test_endpoint(name, path):
    print(f"\nTesting {name} ({path})...")
    try:
        r = requests.get(f"{BACKEND_URL}{path}", headers=HEADERS, timeout=3)
        if r.status_code == 200:
            print(f"✅ Success! Status: {r.status_code}")
            print("Response Data:", r.json())
        elif r.status_code == 403:
            print(f"❌ AUTH FAILED! Key might be wrong. Status: {r.status_code}")
        else:
            print(f"❓ Unexpected Status: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"🚫 ERROR: Could not connect to backend. Is uvicorn running?\n({e})")

if __name__ == "__main__":
    print("=== API KEY SECURITY TEST ===")
    test_endpoint("Dashboard API", "/active-free-slots")
    test_endpoint("Navigation Data", "/navigation-data/CAM_2")
    print("\n=============================")
