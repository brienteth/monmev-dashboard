#!/usr/bin/env python3
import requests
import time

API_URL = "http://localhost:8000"

# Test edilecek key'ler
API_KEYS = {
    "1": {"name": "brick3_unlimited_master", "key": "brick3_unlimited_master"},
    "2": {"name": "brick3_monmev_prod", "key": "brick3_monmev_prod"},
    "3": {"name": "bk3_fastlane_partner", "key": "bk3_fastlane_partner"},
    "4": {"name": "bk3_apriori_validator", "key": "bk3_apriori_validator"},
    "5": {"name": "bk3_kuru_integration", "key": "bk3_kuru_integration"},
}

print("🔑 API KEY TEST - 5 Keys")
print("=" * 50)
print()

# Test 1-5: Valid keys
for num, key_info in API_KEYS.items():
    print(f"{num}️⃣ Testing: {key_info['name']}")
    try:
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            headers={"X-API-Key": key_info['key']},
            params={"limit": 1},
            timeout=5
        )
        
        if response.status_code == 200 and response.json().get("success"):
            print(f"   ✅ SUCCESS (Status: {response.status_code})")
        else:
            print(f"   ❌ FAILED (Status: {response.status_code})")
            print(f"      Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    print()

# Test 6: Invalid key
print("6️⃣ Testing: invalid_key_test (should be rejected)")
try:
    response = requests.get(
        f"{API_URL}/api/v1/opportunities",
        headers={"X-API-Key": "invalid_key_test"},
        params={"limit": 1},
        timeout=5
    )
    
    if response.status_code == 403:
        print(f"   ✅ CORRECTLY REJECTED (403 Forbidden)")
    else:
        print(f"   ❌ ERROR: Should return 403, got {response.status_code}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
print()

# Test 7: No key
print("7️⃣ Testing: No API key (should be rejected)")
try:
    response = requests.get(
        f"{API_URL}/api/v1/opportunities",
        params={"limit": 1},
        timeout=5
    )
    
    if response.status_code == 401:
        print(f"   ✅ CORRECTLY REJECTED (401 Unauthorized)")
    else:
        print(f"   ❌ ERROR: Should return 401, got {response.status_code}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
print()

print("=" * 50)
print("✅ Test complete!")
