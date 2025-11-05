#!/usr/bin/env python3
"""
Test ChatX full-stack integration
"""
import requests
import json

def test_backend_connectivity():
    """Test that backend is responding"""
    try:
        response = requests.get("http://localhost:8000/docs")
        print(f"✅ Backend API docs accessible: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_user_registration():
    """Test user registration via backend"""
    url = "http://localhost:8000/api/v1/auth/register"
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User2",
        "phone": "1234567890"
    }
    
    try:
        response = requests.post(url, json=user_data)
        if response.status_code in [200, 201]:
            print("✅ User registration working")
            return True
        elif response.status_code == 400:
            error = response.json()
            if "already exists" in str(error):
                print("✅ User registration working (user already exists)")
                return True
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔥 Testing ChatX Full-Stack Integration")
    print("=" * 50)
    
    backend_ok = test_backend_connectivity()
    if backend_ok:
        test_user_registration()
    
    print("\n📋 Test Summary:")
    print("- Backend API: http://localhost:8000")
    print("- Frontend UI: http://localhost:3000")
    print("- Documentation: http://localhost:8000/docs")