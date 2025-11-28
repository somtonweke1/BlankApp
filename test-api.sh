#!/bin/bash

# Test script to verify the API is working correctly

API_URL="https://mastery-machine-backend.onrender.com"

echo "================================"
echo "TESTING MASTERY MACHINE API"
echo "================================"
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
HEALTH=$(curl -s $API_URL/)
echo "Response: $HEALTH"
if echo "$HEALTH" | grep -q "online"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test 2: Create user
echo "2. Testing user creation..."
USER_RESPONSE=$(curl -s -X POST $API_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}')
echo "Response: $USER_RESPONSE"
USER_ID=$(echo "$USER_RESPONSE" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$USER_ID" ]; then
    echo "✅ User created: $USER_ID"
else
    echo "❌ User creation failed"
    exit 1
fi
echo ""

echo "================================"
echo "✅ ALL TESTS PASSED"
echo "================================"
echo ""
echo "To test upload:"
echo "1. Go to: https://frontend-ngf4xyfyo-somtonweke1s-projects.vercel.app"
echo "2. Upload any PDF"
echo "3. Check that questions have DIFFERENT answers"
echo ""
