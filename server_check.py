import requests

# Quick server status check
try:
    response = requests.get("http://localhost:8005/")
    print(f"Server Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Server is running and responding!")
    else:
        print(f"Server response: {response.text}")
except Exception as e:
    print(f"❌ Server not accessible: {e}")