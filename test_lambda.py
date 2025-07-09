#!/usr/bin/env python3
"""
Test script for the DICOM to JPG Lambda function
This script allows you to test the function locally before deployment.
"""

import json
import base64
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler, health_check

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    
    event = {}
    context = {}
    
    response = health_check(event, context)
    
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
    print("-" * 50)

def test_dicom_conversion(test_url: str, storage_type: str = 'auto'):
    """Test DICOM conversion with a sample URL"""
    print(f"Testing DICOM conversion...")
    print(f"URL: {test_url}")
    print(f"Storage type: {storage_type}")
    
    event = {
        'url': test_url,
        'storage_type': storage_type,
        'quality': 85
    }
    
    context = {}
    
    try:
        response = lambda_handler(event, context)
        
        print(f"Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Success: {body['success']}")
            print(f"Message: {body['message']}")
            
            if 'data' in body:
                data = body['data']
                print(f"File size: {data['file_size']} bytes")
                print(f"Format: {data['format']}")
                print(f"Quality: {data['quality']}")
                
                # Save the image to a file for inspection
                if 'image_base64' in data:
                    image_data = base64.b64decode(data['image_base64'])
                    
                    # Create temp folder if it doesn't exist
                    temp_dir = os.path.join(os.getcwd(), 'temp')
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    output_file = os.path.join(temp_dir, f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    
                    with open(output_file, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"Converted image saved to: {output_file}")
        else:
            body = json.loads(response['body'])
            print(f"Error: {body.get('error', 'Unknown error')}")
            print(f"Message: {body.get('message', 'No message')}")
            
    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
    
    print("-" * 50)

def test_invalid_request():
    """Test with invalid request to check error handling"""
    print("Testing invalid request (missing URL)...")
    
    event = {
        'quality': 85
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
    print("-" * 50)

def main():
    """Main test function"""
    print("DICOM to JPG Lambda Function Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    test_health_check()
    
    # Test 2: Invalid request
    test_invalid_request()
    
    # Test 3: DICOM conversion (you need to provide a real DICOM URL)
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        storage_type = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        test_dicom_conversion(test_url, storage_type)
    else:
        print("Skipping DICOM conversion test (no URL provided)")
        print("Usage: python test_lambda.py <dicom_url> [storage_type]")
        print("Example: python test_lambda.py https://example.com/sample.dcm s3")

if __name__ == "__main__":
    main() 