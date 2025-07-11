#!/usr/bin/env python3
"""Check API health and verify routes are working."""

import sys
import requests
from loguru import logger

# API endpoints to check
BASE_URL = "http://localhost:8000"
ENDPOINTS = [
    # Basic endpoints
    ("/", "Root endpoint"),
    ("/api/v1/health", "Health check"),
    ("/api/v1/health/db", "Database health"),
    
    # Debug endpoints
    ("/api/v1/debug/info", "Debug info"),
    ("/api/v1/debug/routes", "List all routes"),
    ("/api/v1/debug/test-auth", "Test auth routes"),
    
    # API documentation (if debug mode)
    ("/api/docs", "API documentation"),
    ("/api/openapi.json", "OpenAPI schema"),
]


def check_endpoint(url: str, description: str) -> bool:
    """Check if an endpoint is accessible."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.info(f"✓ {description}: {url} - OK")
            return True
        else:
            logger.warning(f"✗ {description}: {url} - Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ {description}: {url} - Connection refused")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ {description}: {url} - Timeout")
        return False
    except Exception as e:
        logger.error(f"✗ {description}: {url} - Error: {e}")
        return False


def main():
    """Main function to check API health."""
    logger.info("=== API Health Check ===")
    logger.info(f"Checking API at {BASE_URL}")
    
    successful = 0
    failed = 0
    
    for endpoint, description in ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        if check_endpoint(url, description):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"\n=== Summary ===")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    # Try to get route list if debug endpoint is available
    try:
        routes_url = f"{BASE_URL}/api/v1/debug/routes"
        response = requests.get(routes_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"\n=== Registered Routes ({data['total_routes']} total) ===")
            for route in data['routes'][:10]:  # Show first 10 routes
                logger.info(f"  {route['path']} - {route['methods']}")
            if data['total_routes'] > 10:
                logger.info(f"  ... and {data['total_routes'] - 10} more routes")
    except Exception as e:
        logger.warning(f"Could not fetch route list: {e}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())