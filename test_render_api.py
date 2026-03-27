#!/usr/bin/env python3
"""
Test script to add dummy data to Render database via API
Tests if the volunteer side can successfully fetch data from Render
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Render API endpoint
API_BASE_URL = "https://healthtrace-j1uc.onrender.com/api"

def test_api_connection():
    """Test if API is accessible"""
    print("Testing API connection...")
    try:
        response = requests.get(f"{API_BASE_URL}/screenings/", timeout=10)
        print(f"API is accessible! Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Cannot connect to API: {e}")
        return False

def create_dummy_screening():
    """Create a dummy screening record"""
    
    # Sample data
    first_names = ['Kwame', 'Abena', 'Kofi', 'Akua', 'Yaw', 'Adjoa', 'Kweku', 'Ama']
    last_names = ['Asante', 'Osei', 'Mensah', 'Adom', 'Boateng', 'Owusu', 'Agyei']
    volunteers = ['Sarah J.', 'Michael K.', 'Grace A.', 'Paul O.']
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # Generate realistic vitals
    age = random.randint(18, 75)
    gender = random.choice(['Male', 'Female'])
    
    # BMI calculation
    height = random.uniform(155, 185)  # cm
    bmi = random.uniform(22, 32)
    weight = bmi * (height/100) ** 2  # kg
    
    # Blood pressure
    systolic = random.randint(110, 160)
    diastolic = random.randint(70, 100)
    
    # Glucose
    glucose = random.uniform(80, 180)
    
    # Heart rate
    heart_rate = random.randint(60, 95)
    
    screening_data = {
        "full_name": f"{first_name} {last_name}",
        "age": age,
        "gender": gender,
        "phone_number": f"+233{random.randint(200000000, 999999999)}",
        "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
        "weight_kg": round(weight, 2),
        "height_cm": round(height, 2),
        "systolic_bp": systolic,
        "diastolic_bp": diastolic,
        "glucose_level": round(glucose, 2),
        "heart_rate": heart_rate,
        "known_conditions": random.choice(['None', 'Hypertension', 'Diabetes Type 2', 'None', 'None']),
        "current_medications": random.choice(['None', 'Metformin', 'Amlodipine', 'None', 'None']),
        "notes": f"Routine health screening. Patient reports {random.choice(['no symptoms', 'occasional headaches', 'good health', 'fatigue'])}.",
        "screened_by": random.choice(volunteers)
    }
    
    return screening_data

def add_screening_via_api(screening_data):
    """Add screening via API POST request"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/screenings/",
            json=screening_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully added: {screening_data['full_name']}")
            print(f"   Response: {response.text[:100]}")
            return True
        else:
            print(f"Failed to add {screening_data['full_name']}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error adding {screening_data['full_name']}: {e}")
        return False

def get_screenings_summary():
    """Get summary statistics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/screenings/summary/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\nDatabase Summary:")
            print(f"   Total Screened: {data.get('total_screened', 0)}")
            print(f"   Today's Count: {data.get('today_count', 0)}")
            print(f"   Pending Consultations: {data.get('pending_consultations', 0)}")
            print(f"   Critical Cases: {data.get('critical_cases', 0)}")
            print(f"   Average BMI: {data.get('avg_bmi', 0)}")
            return True
        else:
            print(f"Failed to get summary: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error getting summary: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Render Database Connection")
    print("=" * 60)
    
    # Test API connection
    if not test_api_connection():
        print("\nCannot connect to Render API. Please check:")
        print("   1. Backend is deployed and running on Render")
        print("   2. API endpoint is correct")
        print("   3. CORS is configured properly")
        return
    
    # Get initial summary
    print("\nInitial database state:")
    get_screenings_summary()
    
    # Add dummy data
    print("\nAdding 10 dummy screening records...")
    success_count = 0
    for i in range(10):
        screening_data = create_dummy_screening()
        if add_screening_via_api(screening_data):
            success_count += 1
    
    print(f"\nSuccessfully added {success_count}/10 records")
    
    # Get final summary
    print("\nFinal database state:")
    get_screenings_summary()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
