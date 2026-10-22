import requests

def send_data(url, payload):
    try:
        requests.post(f"{url}/update-slots", json=payload, timeout=2)
    except:
        pass
