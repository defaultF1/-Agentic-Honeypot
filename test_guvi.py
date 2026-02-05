import requests
import json

url = "http://127.0.0.1:8000/api/v1/guvi-honeypot"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-key"
}
payload = {
    "sessionId": "test-session-123",
    "message": {
        "sender": "scammer",
        "text": "Your bank account blocked. Update immediately.",
        "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
