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
        page = client.user_management.list_users(limit=10)
        users = []
        for user in page.data:
            users.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
        print(json.dumps({'users': users}))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
