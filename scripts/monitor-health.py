#!/usr/bin/env python3
"""
Health monitoring script for the Cybersecurity Awareness Platform.

This script can be used by monitoring services like UptimeRobot, Pingdom, etc.
"""

import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple


class HealthMonitor:
    """Monitor the health of the application."""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def check_endpoint(self, endpoint: str, expected_status: int = 200) -> Tuple[bool, str]:
        """Check if an endpoint is responding correctly."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == expected_status:
                return True, f"OK ({response.elapsed.total_seconds():.2f}s)"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.RequestException as e:
            return False, str(e)
    
    def check_basic_health(self) -> Dict[str, Any]:
        """Check basic health endpoint."""
        success, message = self.check_endpoint('/api/v1/monitoring/health')
        
        if success:
            try:
                response = self.session.get(f"{self.base_url}/api/v1/monitoring/health")
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status', 'unknown'),
                    'version': data.get('version', 'unknown'),
                    'message': message
                }
            except:
                pass
        
        return {
            'success': False,
            'status': 'unhealthy',
            'message': message
        }
    
    def check_detailed_health(self) -> Dict[str, Any]:
        """Check detailed health if authenticated."""
        if not self.api_key:
            return {'success': False, 'message': 'API key required for detailed health'}
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/monitoring/health/detailed",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}'
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def check_critical_endpoints(self) -> Dict[str, Any]:
        """Check critical application endpoints."""
        endpoints = [
            ('/', 200, 'Landing Page'),
            ('/api/v1/health', 200, 'API Health'),
            ('/api/v1/monitoring/health', 200, 'Monitoring Health'),
            ('/api/docs', 200, 'API Documentation') if self.api_key else None,
        ]
        
        results = {}
        for endpoint in endpoints:
            if endpoint is None:
                continue
                
            path, expected_status, name = endpoint
            success, message = self.check_endpoint(path, expected_status)
            results[name] = {
                'success': success,
                'message': message,
                'endpoint': path
            }
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'base_url': self.base_url,
            'checks': {}
        }
        
        # Basic health
        report['checks']['basic_health'] = self.check_basic_health()
        
        # Critical endpoints
        report['checks']['endpoints'] = self.check_critical_endpoints()
        
        # Detailed health (if authenticated)
        if self.api_key:
            report['checks']['detailed_health'] = self.check_detailed_health()
        
        # Overall status
        all_checks = []
        all_checks.append(report['checks']['basic_health'].get('success', False))
        all_checks.extend([
            check['success'] 
            for check in report['checks']['endpoints'].values()
        ])
        
        report['overall_status'] = 'healthy' if all(all_checks) else 'unhealthy'
        report['success'] = all(all_checks)
        
        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Monitor health of the Cybersecurity Awareness Platform'
    )
    parser.add_argument(
        'url',
        help='Base URL of the application (e.g., https://bootstrap-awareness.de)'
    )
    parser.add_argument(
        '--api-key',
        help='API key for authenticated checks'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'nagios'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--check',
        choices=['basic', 'detailed', 'endpoints', 'all'],
        default='all',
        help='Type of check to perform'
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = HealthMonitor(args.url, args.api_key)
    
    # Perform checks
    if args.check == 'basic':
        result = monitor.check_basic_health()
    elif args.check == 'detailed':
        result = monitor.check_detailed_health()
    elif args.check == 'endpoints':
        result = monitor.check_critical_endpoints()
    else:
        result = monitor.generate_report()
    
    # Format output
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    elif args.format == 'nagios':
        # Nagios plugin format
        if result.get('success', False) or result.get('overall_status') == 'healthy':
            print(f"OK - All health checks passed")
            sys.exit(0)
        else:
            print(f"CRITICAL - Health check failed")
            sys.exit(2)
    else:
        # Human-readable text format
        print(f"Health Check Report for {args.url}")
        print("=" * 50)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"Overall Status: {result.get('overall_status', 'unknown').upper()}")
        print()
        
        if 'checks' in result:
            for check_name, check_result in result['checks'].items():
                print(f"{check_name.replace('_', ' ').title()}:")
                if isinstance(check_result, dict):
                    for key, value in check_result.items():
                        if key != 'success':
                            print(f"  {key}: {value}")
                else:
                    print(f"  {check_result}")
                print()
    
    # Exit code
    sys.exit(0 if result.get('success', False) else 1)


if __name__ == '__main__':
    main()