import requests
import json

user_data = {
    "username": "Naval12", 
    "email": "naval@gmail.com",
    "password": "12345678",
    "first_name": "naval",
    "last_name": "jha", 
    "phone": "9508154648"
}

try:
    response = requests.post("http://localhost:8005/api/v1/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")