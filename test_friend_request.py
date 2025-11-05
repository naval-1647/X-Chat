#!/usr/bin/env python3
"""
Test script for friend request functionality
Run this after starting the server to test the detailed error messages
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.repositories.friend_request_repository import FriendRequestRepository

async def test_friend_request_validation():
    """Test the friend request validation with various scenarios"""
    print("🧪 Testing Friend Request Validation...")
    print("=" * 50)
    
    repo = FriendRequestRepository()
    
    # Test cases
    test_cases = [
        {
            "name": "Invalid sender ID",
            "sender_id": "invalid_id",
            "receiver_id": "673a578b9aca6ce8b46e8d8a"
        },
        {
            "name": "Invalid receiver ID", 
            "sender_id": "673a578b9aca6ce8b46e8d8a",
            "receiver_id": "invalid_id"
        },
        {
            "name": "Self friend request",
            "sender_id": "673a578b9aca6ce8b46e8d8a",
            "receiver_id": "673a578b9aca6ce8b46e8d8a"
        },
        {
            "name": "Valid IDs (if users exist)",
            "sender_id": "673a578b9aca6ce8b46e8d8a",
            "receiver_id": "673a578b9aca6ce8b46e8d8b"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Sender: {test_case['sender_id']}")
        print(f"   Receiver: {test_case['receiver_id']}")
        
        try:
            result = await repo.can_send_request_detailed(
                test_case["sender_id"], 
                test_case["receiver_id"]
            )
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_friend_request_validation())