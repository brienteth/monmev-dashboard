#!/usr/bin/env python3
"""
API Key Test Script
Starts API in background and tests all 5 keys
"""
import subprocess
import time
import requests
import sys
import signal
import os

API_URL = "http://localhost:8000"
api_process = None

def cleanup(signum=None, frame=None):
    """Kill API process on exit"""
    global api_process
    if api_process:
        print("\n🛑 Stopping API...")
        api_process.terminate()
        api_process.wait()
    sys.exit(0)

# Register cleanup handler
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

try:
    # Start API
    print("🚀 Starting API...")
    api_process = subprocess.Popen(
        ["python", "monmev_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/bl10buer/Desktop/MonMev"
    )
    
    # Wait for API to start
    print("⏳ Waiting for API to start...")
    time.sleep(6)
    
    # Check if API is running
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        print(f"✅ API is running (Health: {health.status_code})\n")
    except:
        print("❌ API failed to start")
        cleanup()
    
    # Test keys
    API_KEYS = {
        "1": {"name": "brick3_unlimited_master", "key": "brick3_unlimited_master"},
        "2": {"name": "brick3_monmev_prod", "key": "brick3_monmev_prod"},
        "3": {"name": "bk3_fastlane_partner", "key": "bk3_fastlane_partner"},
        "4": {"name": "bk3_apriori_validator", "key": "bk3_apriori_validator"},
        "5": {"name": "bk3_kuru_integration", "key": "bk3_kuru_integration"},
    }
    
    print("🔑 API KEY TESTS")
    print("=" * 60)
    print()
    
    # Test valid keys
    for num, key_info in API_KEYS.items():
        print(f"{num}️⃣  {key_info['name']}")
        try:
            response = requests.get(
                f"{API_URL}/api/v1/opportunities",
                headers={"X-API-Key": key_info['key']},
                params={"limit": 1},
                timeout=5
            )
            
            if response.status_code == 200 and response.json().get("success"):
                print(f"    ✅ SUCCESS (200 OK)")
            else:
                print(f"    ❌ FAILED ({response.status_code})")
                print(f"       {response.text[:80]}")
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
        print()
    
    # Test invalid key
    print("6️⃣  invalid_key_test (should reject)")
    try:
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            headers={"X-API-Key": "invalid_key_test"},
            params={"limit": 1},
            timeout=5
        )
        
        if response.status_code == 403:
            print(f"    ✅ CORRECTLY REJECTED (403 Forbidden)")
        else:
            print(f"    ❌ Wrong status: {response.status_code}")
    except Exception as e:
        print(f"    ❌ ERROR: {str(e)}")
    print()
    
    # Test no key
    print("7️⃣  No API Key (should reject)")
    try:
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            params={"limit": 1},
            timeout=5
        )
        
        if response.status_code == 401:
            print(f"    ✅ CORRECTLY REJECTED (401 Unauthorized)")
        else:
            print(f"    ❌ Wrong status: {response.status_code}")
    except Exception as e:
        print(f"    ❌ ERROR: {str(e)}")
    print()
    
    print("=" * 60)
    print("✅ All tests complete!\n")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
finally:
    cleanup()
