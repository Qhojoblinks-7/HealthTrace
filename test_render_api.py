#!/usr/bin/env python3
"""
Test script to verify Render backend API endpoints.
Run this script to check if the backend is responding correctly.
"""

import requests
import sys

BASE_URL = "https://healthtrace-j1uc.onrender.com"

def test_endpoint(endpoint, description):
    """Test a single endpoint and return the status code."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        print(f"[OK] {description}: {status}")
        if status == 200:
            print(f"  Response: {response.json()[:100]}...")
        return status
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {description}: ERROR - {e}")
        return None

def main():
    print("=" * 60)
    print("Testing Render Backend API Endpoints")
    print("=" * 60)
    print()
    
    endpoints = [
        ("/", "Root URL"),
        ("/admin/", "Admin URL"),
        ("/api/screenings/", "Screenings List"),
        ("/api/screenings/summary/", "Screenings Summary"),
        ("/api/screenings/analytics/", "Screenings Analytics"),
        ("/api/screenings/notifications/", "Screenings Notifications"),
    ]
    
    results = []
    for endpoint, description in endpoints:
        status = test_endpoint(endpoint, description)
        results.append((endpoint, status))
    
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    working = sum(1 for _, status in results if status == 200)
    total = len(results)
    
    print(f"Working endpoints: {working}/{total}")
    
    if working == 0:
        print()
        print("WARNING: All endpoints returned 404 or errors!")
        print("This means the backend is not running or has crashed on Render.")
        print()
        print("To fix this:")
        print("1. Go to https://dashboard.render.com")
        print("2. Find your 'healthtrace-j1uc' service")
        print("3. Check if it's running or if there are deployment errors")
        print("4. Redeploy the service if needed")
        print()
        print("The backend needs to be running for the frontend to work.")
    elif working < total:
        print()
        print("WARNING: Some endpoints are not working!")
        print("This could indicate a configuration issue.")
    else:
        print()
        print("All endpoints are working correctly!")
    
    return 0 if working == total else 1

if __name__ == "__main__":
    sys.exit(main())
