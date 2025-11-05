#!/usr/bin/env python3
"""
Test script for ChatX user registration
"""
import requests
import json

def test_user_registration():
    """Test user registration endpoint"""
    url = "http://localhost:8005/api/v1/auth/register"
    
    # Test data provided by the user
    user_data = {
        "username": "Naval12",
        "email": "naval@gmail.com", 
        "password": "12345678",
        "first_name": "naval",
        "last_name": "jha",
        "phone": "9508154648"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Testing user registration...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(user_data, indent=2)}")
        print("-" * 50)
        
        response = requests.post(url, json=user_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Registration successful!")
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        else:
            print("❌ Registration failed!")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to server. Make sure the server is running on http://localhost:8005")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_user_registration()