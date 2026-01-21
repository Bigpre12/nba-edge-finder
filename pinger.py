"""
Simple pinger script to keep the website active.
Run this every 13 minutes using a cron job or external service.

Usage:
    python pinger.py <your_website_url>
    
Example:
    python pinger.py https://your-app.onrender.com/ping
"""

import sys
import requests
import time
from datetime import datetime

def ping_website(url, timeout=10):
    """
    Ping a website endpoint.
    
    Args:
        url: Full URL to ping (e.g., https://your-app.onrender.com/ping)
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✓ Ping successful: {response.status_code}")
            return True
        else:
            print(f"[{datetime.now()}] ✗ Ping failed: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ✗ Ping error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python pinger.py <your_website_url>")
        print("Example: python pinger.py https://your-app.onrender.com/ping")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Ensure URL ends with /ping or /health
    if not url.endswith('/ping') and not url.endswith('/health'):
        if url.endswith('/'):
            url = url.rstrip('/')
        url = url + '/ping'
    
    print(f"Pinging: {url}")
    success = ping_website(url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
