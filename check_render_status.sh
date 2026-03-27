#!/bin/bash
# Quick script to check Render backend status

echo "=========================================="
echo "Checking Render Backend Status"
echo "=========================================="
echo ""

echo "Testing API endpoint..."
curl -s -o /dev/null -w "Status: %{http_code}\n" https://healthtrace-j1uc.onrender.com/api/screenings/

echo ""
echo "Testing with verbose output..."
curl -v https://healthtrace-j1uc.onrender.com/api/screenings/ 2>&1 | grep -E "(HTTP|Not Found|Connected)"

echo ""
echo "=========================================="
echo "If you see 'Not Found', the backend needs to be redeployed."
echo "Push the fixed requirements.txt to trigger a new deployment."
echo "=========================================="
