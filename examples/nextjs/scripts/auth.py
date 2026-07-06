#!/usr/bin/env python3
import os
import sys
import json
from workos import WorkOSClient

def main():
    api_key = os.environ.get('WORKOS_API_KEY')
    client_id = os.environ.get('WORKOS_CLIENT_ID')
    
    if not api_key or not client_id:
        print(json.dumps({
            'error': 'WORKOS_API_KEY and WORKOS_CLIENT_ID must be set'
        }))
        sys.exit(1)
    
    client = WorkOSClient(api_key=api_key, client_id=client_id)
    
    try:
        # Generate SSO authorization URL
        # Note: This requires a configured SSO connection in your WorkOS dashboard
        authorization_url = client.sso.get_authorization_url(
            connection_id="conn_01EHQMYV6MBK39QC4MHZXXX",  # Replace with your connection ID
            redirect_uri="http://localhost:3000/api/auth/callback",
        )
        print(json.dumps({'url': authorization_url}))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
