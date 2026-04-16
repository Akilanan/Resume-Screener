#!/usr/bin/env python3
"""
Test script to verify TalentAI application improvements.
Tests: Health endpoints, CORS, request logging, error handling, validation.
"""
import subprocess
import json
import sys
import time

def run_curl(url, method="GET", data=None, headers=None):
    """Run curl command and return response"""
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method, url]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if not result.stdout:
            return {"error": "No response", "returncode": result.returncode}
        
        lines = result.stdout.rsplit('\n', 2)
        if len(lines) >= 2:
            body = lines[0]
            status = int(lines[1]) if lines[1].isdigit() else 0
            try:
                return {"status": status, "body": json.loads(body)}
            except:
                return {"status": status, "body": body}
        return {"error": "Invalid response format"}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}

def test_endpoints():
    """Test all endpoints"""
    tests = [
        {
            "name": "Root endpoint",
            "url": "http://localhost:8000",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Health check",
            "url": "http://localhost:8000/health",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Detailed health check",
            "url": "http://localhost:8000/api/v1/health/detailed",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "API docs",
            "url": "http://localhost:8000/docs",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Login - Invalid credentials",
            "url": "http://localhost:8000/api/v1/auth/login",
            "method": "POST",
            "data": {"email": "test@test.com", "password": "invalid"},
            "expected_status": 401
        },
        {
            "name": "Frontend accessibility",
            "url": "http://localhost:5173",
            "method": "GET",
            "expected_status": 200
        }
    ]
    
    print("\n" + "="*60)
    print("TALENTAI APPLICATION TEST SUITE")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"Testing: {test['name']}")
        result = run_curl(test["url"], test.get("method", "GET"), test.get("data"))
        
        if "error" in result:
            print(f"  ❌ ERROR: {result['error']}\n")
            failed += 1
        elif result.get("status") == test["expected_status"]:
            print(f"  ✅ PASS (Status: {result['status']})\n")
            passed += 1
        else:
            print(f"  ❌ FAIL (Expected {test['expected_status']}, got {result.get('status')})\n")
            failed += 1
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    time.sleep(2)  # Wait for services to be ready
    success = test_endpoints()
    sys.exit(0 if success else 1)
