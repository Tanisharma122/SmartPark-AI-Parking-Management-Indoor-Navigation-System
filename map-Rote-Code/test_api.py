import requests

BACKEND_URL = "http://127.0.0.1:8000"

# ----- KEYS FOR TESTING -----
ORG_KEY = "sk_org_dashboard_123"
DEV_KEY_VID1 = "sk_dev_vid1_456"
DEV_KEY_VID2 = "sk_dev_vid2_789"

def test_endpoint(name, path, api_key):
    print(f"\n[Testing {name}] {path} ...")
    headers = {"x-api-key": api_key}
    try:
        r = requests.get(f"{BACKEND_URL}{path}", headers=headers, timeout=3)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("✅ Success!")
            data = r.json()
            if "videos" in data:
                print(f"Video Feed Count: {len(data['videos'])}")
                for v in data['videos']:
                    print(f" - {v['video_id']} at {v['latitude']}, {v['longitude']}")
            elif "slots" in data:
                print(f"Total Free Slots: {data['count']}")
                for s in data['slots']:
                    print(f" - Slot {s['slot_id']} (from {s['video_id']})")
            elif "geo_location" in data:
                 print(f"Video Feed Location: {data['geo_location']}")
        else:
            print(f"❌ Error: {r.json()}")
    except Exception as e:
        print(f"🚫 Failed: {e}")

if __name__ == "__main__":
    print("=== VIDEO-CENTRIC API SECURITY TEST ===")
    
    # 1. ORG KEY: Should see ALL videos
    test_endpoint("ORG Overview (All Videos)", "/videos-list", ORG_KEY)
    
    # 2. ORG KEY: Should see ALL free slots across the organization
    test_endpoint("ORG Free Slots (Organization Wide)", "/active-free-slots", ORG_KEY)
    
    # 3. DEVICE KEY (VID_1): Should see its OWN navigation data
    test_endpoint("DEVICE VID_1 (Own Navigation)", "/navigation-data/VID_1", DEV_KEY_VID1)
    
    # 4. DEVICE KEY (VID_1) trying to see VID_2: Should be DENIED
    test_endpoint("DEVICE VID_1 (Cross-Video Denied)", "/navigation-data/VID_2", DEV_KEY_VID1)

    print("\n" + "="*40)
