#!/bin/bash

echo "🔑 API KEY TEST - 5 Keys"
echo "========================"
echo ""

# Test 1: brick3_unlimited_master
echo "1️⃣ Testing: brick3_unlimited_master"
RESPONSE=$(curl -s -H "X-API-Key: brick3_unlimited_master" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ SUCCESS"
else
    echo "   ❌ FAILED: $RESPONSE"
fi
echo ""

# Test 2: brick3_monmev_prod
echo "2️⃣ Testing: brick3_monmev_prod"
RESPONSE=$(curl -s -H "X-API-Key: brick3_monmev_prod" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ SUCCESS"
else
    echo "   ❌ FAILED: $RESPONSE"
fi
echo ""

# Test 3: bk3_fastlane_partner
echo "3️⃣ Testing: bk3_fastlane_partner"
RESPONSE=$(curl -s -H "X-API-Key: bk3_fastlane_partner" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ SUCCESS"
else
    echo "   ❌ FAILED: $RESPONSE"
fi
echo ""

# Test 4: bk3_apriori_validator
echo "4️⃣ Testing: bk3_apriori_validator"
RESPONSE=$(curl -s -H "X-API-Key: bk3_apriori_validator" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ SUCCESS"
else
    echo "   ❌ FAILED: $RESPONSE"
fi
echo ""

# Test 5: bk3_kuru_integration
echo "5️⃣ Testing: bk3_kuru_integration"
RESPONSE=$(curl -s -H "X-API-Key: bk3_kuru_integration" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ SUCCESS"
else
    echo "   ❌ FAILED: $RESPONSE"
fi
echo ""

# Test 6: Invalid key
echo "6️⃣ Testing: invalid_key_test (should fail)"
RESPONSE=$(curl -s -H "X-API-Key: invalid_key_test" "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"detail":"Invalid API key'; then
    echo "   ✅ CORRECTLY REJECTED"
else
    echo "   ❌ ERROR: Should reject invalid key"
fi
echo ""

# Test 7: No key
echo "7️⃣ Testing: No key (should fail)"
RESPONSE=$(curl -s "http://localhost:8000/api/v1/opportunities?limit=1")
if echo "$RESPONSE" | grep -q '"detail":"API key required'; then
    echo "   ✅ CORRECTLY REJECTED"
else
    echo "   ❌ ERROR: Should require key"
fi
echo ""

echo "========================"
echo "✅ Test complete!"
