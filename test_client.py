#!/usr/bin/env python3
"""
Test client for AI OS development environment
"""

import requests
import time
import sys

API_URL = "http://localhost:5000"

def test_basic_boot():
    """Test basic bootloader functionality"""
    print("Testing basic boot...")
    
    # Read the example bootloader
    with open('examples/minimal_boot.asm', 'r') as f:
        boot_code = f.read()
    
    # Compile and flash
    print("Compiling bootloader...")
    r = requests.post(f"{API_URL}/compile", json={'code': boot_code})
    print(f"Compile: {r.json()}")
    
    print("Flashing and booting...")
    r = requests.post(f"{API_URL}/flash", json={})
    print(f"Flash: {r.json()}")
    
    time.sleep(1)
    
    # Read boot message
    print("Reading serial output...")
    r = requests.get(f"{API_URL}/serial")
    print(f"Boot message: {r.json()['text']}")
    
    # Test ping command
    print("Sending ping...")
    r = requests.post(f"{API_URL}/serial", json={'data': 'p'})
    time.sleep(0.1)
    r = requests.get(f"{API_URL}/serial")
    print(f"Response: {r.json()['text']}")
    
    # Test info command
    print("Sending info request...")
    r = requests.post(f"{API_URL}/serial", json={'data': 'i'})
    time.sleep(0.1)
    r = requests.get(f"{API_URL}/serial")
    print(f"Response: {r.json()['text']}")

if __name__ == '__main__':
    # Check if server is running
    try:
        r = requests.get(f"{API_URL}/status")
        print(f"Server status: {r.json()}")
    except:
        print("Error: Server not running. Start with 'python3 setup.py'")
        sys.exit(1)
    
    test_basic_boot()