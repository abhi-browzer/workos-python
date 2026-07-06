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
        if len(sys.argv) > 1 and sys.argv[1] == 'create':
            # Create organization
            org_name = sys.argv[2] if len(sys.argv) > 2 else 'New Organization'
            org = client.organizations.create_organization(name=org_name)
            print(json.dumps({
                'organization': {
                    'id': org.id,
                    'name': org.name,
                    'created_at': org.created_at
                }
            }))
        else:
            # List organizations
            page = client.organizations.list_organizations(limit=10)
            organizations = []
            for org in page.data:
                organizations.append({
                    'id': org.id,
                    'name': org.name,
                    'created_at': org.created_at
                })
            print(json.dumps({'organizations': organizations}))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
