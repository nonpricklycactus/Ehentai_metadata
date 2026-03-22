#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Custom Metadata Server Example.

This script demonstrates how to:
1. Start the example server
2. Test the server endpoints
3. Simulate Calibre plugin requests
4. Verify protocol compliance

Usage:
  python test_custom_server.py
"""

import json
import time
import subprocess
import threading
import sys
import os
from typing import Dict, Any

try:
    import requests
except ImportError:
    print("Installing requests library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Server configuration
SERVER_URL = "http://localhost:5000"
METADATA_ENDPOINT = f"{SERVER_URL}/metadata"
HEALTH_ENDPOINT = f"{SERVER_URL}/health"
EXAMPLE_ENDPOINT = f"{SERVER_URL}/example-request"

# Test authentication token (matches server config)
AUTH_TOKEN = "test-token-123"


def wait_for_server(timeout=30, interval=1):
    """Wait for the server to become available."""
    print(f"Waiting for server to start (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            print(f"  Waiting... ({e})")
        
        time.sleep(interval)
    
    print(f"Server did not start within {timeout} seconds")
    return False


def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Testing health endpoint...")
    print("="*60)
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_example_request():
    """Test the example request endpoint."""
    print("\n" + "="*60)
    print("Testing example request endpoint...")
    print("="*60)
    
    try:
        response = requests.get(EXAMPLE_ENDPOINT, timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Example curl command:\n{data.get('curl_command', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_metadata_endpoint_without_auth():
    """Test metadata endpoint without authentication."""
    print("\n" + "="*60)
    print("Testing metadata endpoint WITHOUT authentication...")
    print("="*60)
    
    # Example request matching server's sample data
    request_data = {
        "schema_version": "1.0",
        "search_type": "identify",
        "title": "拘束する部活動",
        "authors": ["すもも堂"],
        "identifiers": {"ehentai": "3852762_f65294d2bb_0"}
    }
    
    try:
        response = requests.post(
            METADATA_ENDPOINT,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check protocol compliance
            if data.get('schema_version') == '1.0':
                print("✓ Protocol version correct")
            else:
                print("✗ Protocol version mismatch")
                
            if 'results' in data:
                print(f"✓ Found {len(data['results'])} results")
                if data['results']:
                    result = data['results'][0]
                    print(f"  First result title: {result.get('title')}")
                    print(f"  First result authors: {result.get('authors')}")
                    print(f"  First result tags: {result.get('tags', [])[:3]}...")
            else:
                print("✗ No 'results' field in response")
                
            if 'error' in data:
                print(f"Error field: {data['error']}")
                
        except json.JSONDecodeError:
            print(f"Response text: {response.text[:500]}...")
            
        return response.status_code in [200, 401]  # 401 is expected when auth is required
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_endpoint_with_auth():
    """Test metadata endpoint with authentication."""
    print("\n" + "="*60)
    print("Testing metadata endpoint WITH authentication...")
    print("="*60)
    
    # Example request matching server's sample data
    request_data = {
        "schema_version": "1.0",
        "search_type": "identify",
        "title": "拘束する部活動",
        "authors": ["すもも堂"],
        "identifiers": {"ehentai": "3852762_f65294d2bb_0"}
    }
    
    try:
        response = requests.post(
            METADATA_ENDPOINT,
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                print("✓ Authentication successful")
                if data.get('results'):
                    print(f"✓ Found {len(data['results'])} metadata results")
                    return True
                else:
                    print("✗ No results found (but authentication worked)")
                    return True
            else:
                print(f"✗ Request failed with status {response.status_code}")
                if 'error' in data:
                    print(f"  Error: {data['error']}")
                return False
                
        except json.JSONDecodeError:
            print(f"Response text: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cover_search():
    """Test cover search functionality."""
    print("\n" + "="*60)
    print("Testing cover search endpoint...")
    print("="*60)
    
    request_data = {
        "schema_version": "1.0",
        "search_type": "cover",
        "title": "イブキとい～っぱいシようねっ♡",
        "authors": ["比宮じょーず"],
        "identifiers": {"ehentai": "1234567_abcdef_0"}
    }
    
    try:
        response = requests.post(
            METADATA_ENDPOINT,
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                print("✓ Cover search successful")
                if data.get('results'):
                    for result in data['results']:
                        if 'cover_url' in result:
                            print(f"  Cover URL: {result['cover_url']}")
                return True
            else:
                print(f"✗ Cover search failed")
                return False
                
        except json.JSONDecodeError:
            print(f"Response text: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_error_cases():
    """Test error cases and validation."""
    print("\n" + "="*60)
    print("Testing error cases...")
    print("="*60)
    
    test_cases = [
        {
            "name": "Missing required field",
            "data": {
                "schema_version": "1.0",
                "search_type": "identify",
                "title": "Test",
                # Missing authors and identifiers
            },
            "expected_error": True
        },
        {
            "name": "Wrong schema version",
            "data": {
                "schema_version": "2.0",  # Wrong version
                "search_type": "identify",
                "title": "Test",
                "authors": ["Author"],
                "identifiers": {}
            },
            "expected_error": True
        },
        {
            "name": "Invalid search type",
            "data": {
                "schema_version": "1.0",
                "search_type": "invalid_type",  # Invalid
                "title": "Test",
                "authors": ["Author"],
                "identifiers": {}
            },
            "expected_error": True
        },
        {
            "name": "Valid request (no match expected)",
            "data": {
                "schema_version": "1.0",
                "search_type": "identify",
                "title": "Non-existent Title 12345",
                "authors": ["Unknown Author"],
                "identifiers": {}
            },
            "expected_error": False  # Valid request, just no results
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Request: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(
                METADATA_ENDPOINT,
                json=test_case['data'],
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {AUTH_TOKEN}"
                },
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            
            try:
                data = response.json()
                if 'error' in data and data['error']:
                    print(f"Error returned: {data['error']}")
                    if test_case['expected_error']:
                        print("✓ Expected error received")
                    else:
                        print("✗ Unexpected error")
                else:
                    print(f"Results: {len(data.get('results', []))}")
                    if not test_case['expected_error']:
                        print("✓ No error (as expected)")
                    else:
                        print("✗ Expected error but got results")
                        
            except json.JSONDecodeError:
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Request failed: {e}")


def simulate_calibre_plugin_request():
    """Simulate a request similar to what the Calibre plugin would send."""
    print("\n" + "="*60)
    print("Simulating Calibre Plugin Request")
    print("="*60)
    
    # This mimics what the CustomMetadataClient in protocol.py sends
    request_data = {
        "schema_version": "1.0",
        "search_type": "identify",
        "title": "Example Manga",
        "authors": ["Sample Artist"],
        "identifiers": {"ehentai": "9999999_xyz_0"}
    }
    
    print("Plugin would send:")
    print(json.dumps(request_data, indent=2))
    
    print("\nPlugin configuration in Calibre:")
    print("  Custom metadata server URL: http://localhost:5000/metadata")
    print(f"  Custom metadata auth token: Bearer {AUTH_TOKEN}")
    
    print("\nTesting the request...")
    try:
        response = requests.post(
            METADATA_ENDPOINT,
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AUTH_TOKEN}"
            },
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nPlugin would receive:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('results'):
                result = data['results'][0]
                print("\nCalibre would display:")
                print(f"  Title: {result.get('title')}")
                print(f"  Authors: {', '.join(result.get('authors', []))}")
                print(f"  Publisher: {result.get('publisher')}")
                print(f"  Rating: {result.get('rating')}")
                print(f"  Tags: {', '.join(result.get('tags', [])[:5])}...")
                print(f"  Cover URL: {result.get('cover_url', 'N/A')}")
                
            return True
        else:
            print(f"Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main test function."""
    print("="*70)
    print("Custom Metadata Server Test Suite")
    print("="*70)
    print("This script tests the example custom metadata server.")
    print("Make sure the server is running before starting tests.")
    print()
    
    # Check if server is running
    if not wait_for_server(timeout=10):
        print("\n" + "!"*60)
        print("WARNING: Server is not running!")
        print("Please start the server first:")
        print("  python custom_metadata_server_example.py")
        print("!"*60)
        print("\nStarting server in background for testing...")
        
        # Try to start server in background
        try:
            server_process = subprocess.Popen(
                [sys.executable, "custom_metadata_server_example.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give server time to start
            time.sleep(3)
            
            if not wait_for_server(timeout=20):
                print("Failed to start server. Exiting.")
                return
            
            print("Server started successfully!")
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            return
    
    # Run tests
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Example Request", test_example_request),
        ("Metadata without Auth", test_metadata_endpoint_without_auth),
        ("Metadata with Auth", test_metadata_endpoint_with_auth),
        ("Cover Search", test_cover_search),
        ("Error Cases", test_error_cases),
        ("Calibre Plugin Simulation", simulate_calibre_plugin_request),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n>>> Running test: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"<<< Test {'PASSED' if success else 'FAILED'}: {test_name}")
        except Exception as e:
            print(f"<<< Test ERROR: {test_name} - {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print()
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*70)
    print("Calibre Plugin Integration Instructions")
    print("="*70)
    print("To use this server with the Ehentai_metadata plugin:")
    print()
    print("1. In Calibre, go to Preferences → Metadata → Metadata sources")
    print("2. Select 'E-hentai Galleries' and click Configure")
    print("3. Set the following options:")
    print("   - Custom metadata server URL: http://localhost:5000/metadata")
    print("   - Custom metadata auth token: Bearer test-token-123")
    print("4. Click OK and restart Calibre if needed")
    print()
    print("The plugin will now send metadata requests to this server")
    print("in addition to searching E-Hentai/ExHentai.")
    print("="*70)
    
    if passed == total:
        print("\n✅ All tests passed! Server is ready for use with Calibre plugin.")
    else:
        print(f"\n⚠️  {passed}/{total} tests passed. Some issues need attention.")


if __name__ == "__main__":
    main()