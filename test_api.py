#!/usr/bin/env python3
"""
Test script for the Entity Extraction API
"""

import requests
import json
import time
import sys

def test_health(base_url="http://localhost:8000"):
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Status: {response.json()['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_url_extraction(base_url="http://localhost:8000"):
    """Test URL-based entity extraction"""
    print("\n🌐 Testing URL extraction...")
    
    # Test with a sample image URL
    test_url = "https://picsum.photos/400/300"
    
    try:
        response = requests.post(
            f"{base_url}/extract/url",
            json={"image_url": test_url},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ URL extraction successful")
                entities = result.get("entities", {}).get("entities", [])
                print(f"   Found {len(entities)} entities")
                print(f"   Processing time: {result.get('processing_time_ms', 0):.1f}ms")
                return True
            else:
                print(f"❌ URL extraction failed: {result.get('error')}")
                return False
        else:
            print(f"❌ URL extraction HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL extraction error: {str(e)}")
        return False

def test_batch_extraction(base_url="http://localhost:8000"):
    """Test batch entity extraction"""
    print("\n🔄 Testing batch extraction...")
    
    # Test with multiple sample image URLs
    test_urls = [
        "https://picsum.photos/400/300?random=1",
        "https://picsum.photos/400/300?random=2"
    ]
    
    try:
        response = requests.post(
            f"{base_url}/extract/batch",
            json={"image_urls": test_urls},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch extraction successful")
            print(f"   Total processed: {result.get('total_processed', 0)}")
            print(f"   Successful: {result.get('successful', 0)}")
            print(f"   Failed: {result.get('failed', 0)}")
            return True
        else:
            print(f"❌ Batch extraction HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Batch extraction error: {str(e)}")
        return False

def test_models_endpoint(base_url="http://localhost:8000"):
    """Test the models endpoint"""
    print("\n🤖 Testing models endpoint...")
    
    try:
        response = requests.get(f"{base_url}/models")
        if response.status_code == 200:
            result = response.json()
            print("✅ Models endpoint successful")
            print(f"   Current model: {result.get('current_model')}")
            print(f"   Available models: {len(result.get('available_models', []))}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Entity Extraction API Test Suite")
    print("=" * 40)
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"Testing API at: {base_url}")
    
    # Run tests
    tests = [
        test_health,
        test_models_endpoint,
        test_url_extraction,
        test_batch_extraction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test(base_url):
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 