#!/usr/bin/env python3
"""
GUVI Agentic Scam HoneyPot - API Test Script
Tests the API endpoints with sample scam messages
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://honeypot-api-blush.vercel.app"
API_KEY = "guvi-hackathon-secret-key"

# Test data - various scam scenarios
TEST_SCENARIOS = [
    {
        "name": "UPI Fraud - Request Money",
        "session_id": f"test-upi-{int(time.time())}",
        "messages": [
            {
                "sender": "scammer",
                "text": "Hello! I accidentally sent you Rs. 5000. Please return it to this UPI ID: refund@phonepe",
                "timestamp": int(time.time() * 1000)
            }
        ]
    },
    {
        "name": "Bank Fraud - Account Blocked",
        "session_id": f"test-bank-{int(time.time())}",
        "messages": [
            {
                "sender": "scammer",
                "text": "Dear Customer, Your SBI account will be blocked today. Click here to verify KYC: http://sbi-verify-fake.com",
                "timestamp": int(time.time() * 1000)
            }
        ]
    },
    {
        "name": "Lottery Scam",
        "session_id": f"test-lottery-{int(time.time())}",
        "messages": [
            {
                "sender": "scammer",
                "text": "Congratulations! You have won Rs. 10,00,000 in Lucky Draw! Call +919876543210 to claim your prize.",
                "timestamp": int(time.time() * 1000)
            }
        ]
    },
    {
        "name": "OTP Harvesting",
        "session_id": f"test-otp-{int(time.time())}",
        "messages": [
            {
                "sender": "scammer",
                "text": "Urgent! Your Paytm account will be suspended. Share the OTP you just received to verify your identity.",
                "timestamp": int(time.time() * 1000)
            }
        ]
    },
    {
        "name": "Phishing Link",
        "session_id": f"test-phish-{int(time.time())}",
        "messages": [
            {
                "sender": "scammer",
                "text": "Your package delivery failed. Update your address here: http://fake-delivery-tracking.com/update",
                "timestamp": int(time.time() * 1000)
            }
        ]
    }
]


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scam_detection():
    """Test scam detection endpoint with various scenarios"""
    print("\n" + "="*60)
    print("TEST 2: Scam Detection")
    print("="*60)
    
    results = []
    
    for scenario in TEST_SCENARIOS:
        print(f"\n--- Testing: {scenario['name']} ---")
        print(f"Session ID: {scenario['session_id']}")
        print(f"Message: {scenario['messages'][0]['text'][:60]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/scam-detection",
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "sessionId": scenario['session_id'],
                    "message": scenario['messages'][0],
                    "conversationHistory": [],
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
            )
            
            result = response.json()
            results.append({
                "name": scenario['name'],
                "result": result
            })
            
            print(f"✅ Status: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return results


def test_multi_turn_conversation():
    """Test multi-turn conversation"""
    print("\n" + "="*60)
    print("TEST 3: Multi-Turn Conversation")
    print("="*60)
    
    session_id = f"test-multi-{int(time.time())}"
    
    conversation_turns = [
        {
            "sender": "scammer",
            "text": "Hello! You have won Rs. 5,00,000 in our lucky draw!",
            "timestamp": int(time.time() * 1000)
        },
        {
            "sender": "scammer",
            "text": "To claim your prize, please send a processing fee of Rs. 5000 to UPI ID: luckywinner@paytm",
            "timestamp": int(time.time() * 1000) + 1000
        },
        {
            "sender": "scammer",
            "text": "Hurry up! This offer expires in 10 minutes!",
            "timestamp": int(time.time() * 1000) + 2000
        }
    ]
    
    history = []
    
    for i, message in enumerate(conversation_turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Scammer: {message['text'][:50]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/scam-detection",
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "sessionId": session_id,
                    "message": message,
                    "conversationHistory": history,
                    "metadata": {
                        "channel": "SMS",
                        "language": "English",
                        "locale": "IN"
                    }
                }
            )
            
            result = response.json()
            print(f"Agent: {result.get('reply', 'No response')[:80]}...")
            
            # Add to history
            history.append(message)
            if result.get('reply'):
                history.append({
                    "sender": "agent",
                    "text": result['reply'],
                    "timestamp": int(time.time() * 1000)
                })
            
            # Small delay between turns
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Check session state
    print(f"\n--- Checking Session State ---")
    try:
        response = requests.get(
            f"{BASE_URL}/api/session/{session_id}",
            headers={"x-api-key": API_KEY}
        )
        session_data = response.json()
        print(f"Session: {json.dumps(session_data, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_authentication():
    """Test API key authentication"""
    print("\n" + "="*60)
    print("TEST 4: Authentication")
    print("="*60)
    
    # Test without API key
    print("\n--- Without API Key ---")
    try:
        response = requests.post(
            f"{BASE_URL}/api/scam-detection",
            json={
                "sessionId": "test-auth",
                "message": {"sender": "scammer", "text": "Test"}
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with wrong API key
    print("\n--- With Wrong API Key ---")
    try:
        response = requests.post(
            f"{BASE_URL}/api/scam-detection",
            headers={"x-api-key": "wrong-key"},
            json={
                "sessionId": "test-auth",
                "message": {"sender": "scammer", "text": "Test"}
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with correct API key
    print("\n--- With Correct API Key ---")
    try:
        response = requests.post(
            f"{BASE_URL}/api/scam-detection",
            headers={"x-api-key": API_KEY},
            json={
                "sessionId": "test-auth",
                "message": {"sender": "scammer", "text": "Test"}
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if not results:
        print("No results to summarize")
        return
    
    scam_detected = sum(1 for r in results if r["result"].get("reply") and r["result"]["reply"] != "Thank you for the information. I'll look into this.")
    
    print(f"\nTotal Scenarios Tested: {len(results)}")
    print(f"Agent Engaged: {scam_detected}")
    
    print("\nResults by Scenario:")
    for r in results:
        reply_preview = r["result"].get("reply", "No response")[:50]
        print(f"  - {r['name']}: {reply_preview}...")


def main():
    """Run all tests"""
    print("🚀 GUVI Agentic Scam HoneyPot - API Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Please start the server first:")
        print("  python -m app.main")
        sys.exit(1)
    
    # Run tests
    test_health()
    results = test_scam_detection()
    test_multi_turn_conversation()
    test_authentication()
    
    # Print summary
    if results:
        print_summary(results)
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
