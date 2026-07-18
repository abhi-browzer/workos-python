WorkOS is an enterprise-ready authentication and user management platform with APIs for SSO, Directory Sync, Audit Logs, and Fine-Grained Authorization.
This cookbook shows you how to integrate WorkOS into your Python application with real, runnable code.

You'll learn how to authenticate users via Single Sign-On, manage organizations and users, sync directory data from identity providers like Okta or Azure AD, verify webhook signatures, and check permissions with Fine-Grained Authorization.
Every recipe uses the official `workos` Python SDK and includes the exact imports, error handling, and output you need to ship production code.

## How to authenticate users with Single Sign-On

You need to let enterprise customers log in through their existing identity provider (Okta, Azure AD, Google Workspace) instead of managing passwords yourself. This is the core SSO authorization flow.

**Prerequisites**
- WorkOS account with SSO configured
- A connection set up in the WorkOS dashboard for your identity provider
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import AuthenticationError, NotFoundError

# Initialize the client
client = WorkOSClient(
    api_key="sk_example_123456789",
    client_id="client_example_123456789"
)

# Step 1: Generate the authorization URL to redirect users to
auth_url = client.sso.get_authorization_url(
    connection="conn_01H5QHGX1Z2R3T4V5W6X7Y8Z9A",
    redirect_uri="https://yourapp.com/auth/callback",
    state="custom_state_value_for_csrf"
)

print(f"Redirect user to: {auth_url}")

# Step 2: After redirect, exchange the authorization code for a profile
# This happens in your callback endpoint
code = "01H5QHGX1Z2R3T4V5W6X7Y8Z9A_code_example"

try:
    profile = client.sso.get_profile_and_token(code=code)
    
    print(f"User authenticated: {profile.profile.email}")
    print(f"User ID: {profile.profile.id}")
    print(f"First name: {profile.profile.first_name}")
    print(f"Last name: {profile.profile.last_name}")
    print(f"Connection ID: {profile.profile.connection_id}")
    print(f"Organization ID: {profile.profile.organization_id}")
    print(f"Access token: {profile.access_token}")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Request ID: {e.request_id}")
except NotFoundError as e:
    print(f"Connection not found: {e.message}")
```

SSO authentication is a two-step OAuth-style flow.

First, you call `client.sso.get_authorization_url()` with a connection ID (which represents the link to an identity provider like Okta), your callback URL, and a state parameter for CSRF protection.
This returns a URL you redirect the user to — they'll authenticate with their identity provider there.

After the user authenticates, WorkOS redirects them back to your `redirect_uri` with a `code` query parameter.
You exchange that code for a user profile by calling `client.sso.get_profile_and_token(code=code)`.

The returned `profile` object contains the user's email, ID, name, and which organization/connection they used.
The `access_token` is a JWT you can use to verify the user's identity in subsequent requests.

Common errors: `AuthenticationError` when the code is invalid or expired, `NotFoundError` when the connection ID doesn't exist.

**Expected output**

```
Redirect user to: https://api.workos.com/sso/authorize?client_id=client_example_123456789&redirect_uri=https%3A%2F%2Fyourapp.com%2Fauth%2Fcallback&response_type=code&state=custom_state_value_for_csrf&connection=conn_01H5QHGX1Z2R3T4V5W6X7Y8Z9A

User authenticated: alice@example.com
User ID: user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
First name: Alice
Last name: Smith
Connection ID: conn_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
Organization ID: org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
Access token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Gotchas**
- The authorization code is single-use and expires quickly (typically 10 minutes) — exchange it immediately.
- Always validate the state parameter when handling the callback to prevent CSRF attacks.
- Connection IDs are specific to each identity provider setup — you need to configure these in the WorkOS dashboard first.
- The access_token is a JWT but WorkOS recommends storing the user_id in your session instead of using it as a session token directly.

## How to create and manage organizations

Your app needs to group users into organizations (companies, teams, tenants) and manage their settings. This is foundational for B2B SaaS multi-tenancy.

**Prerequisites**
- WorkOS account
- API key with organization management permissions
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import ConflictError, NotFoundError

client = WorkOSClient(api_key="sk_example_123456789")

# Create a new organization
try:
    org = client.organizations.create_organization(
        name="Acme Corporation",
        domain_data=[
            {"domain": "acme.com", "state": "verified"},
            {"domain": "acmecorp.com", "state": "pending"}
        ]
    )
    
    print(f"Created organization: {org.name}")
    print(f"Organization ID: {org.id}")
    print(f"Domains: {[d['domain'] for d in org.domains]}")
    
except ConflictError as e:
    print(f"Organization already exists: {e.message}")

# List all organizations with auto-pagination
print("\nAll organizations:")
for organization in client.organizations.list_organizations().auto_paging_iter():
    print(f"  - {organization.name} ({organization.id})")

# Get a specific organization
try:
    org_id = "org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"
    retrieved_org = client.organizations.get_organization(organization=org_id)
    print(f"\nRetrieved: {retrieved_org.name}")
    print(f"Created at: {retrieved_org.created_at}")
    print(f"Updated at: {retrieved_org.updated_at}")
    
except NotFoundError as e:
    print(f"Organization not found: {e.message}")

# Update organization
updated_org = client.organizations.update_organization(
    organization=org.id,
    name="Acme Corp (updated)"
)
print(f"\nUpdated name to: {updated_org.name}")

# Delete organization
client.organizations.delete_organization(organization=org.id)
print(f"\nDeleted organization: {org.id}")
```

Organizations are the top-level entity in WorkOS — they represent your customers' companies.

`create_organization()` takes a name and optionally a list of domains.
Domains can be verified (users with that email domain auto-join) or pending (waiting for DNS verification).
The method returns an organization object with an `id` you'll use in other API calls.

If you try to create an org with a domain that already exists, you'll get a `ConflictError`.

`list_organizations()` returns a paginated response.
The `.auto_paging_iter()` method automatically fetches all pages behind the scenes — you just iterate over all orgs without manually handling cursors.

`get_organization()` fetches a single org by ID.
Use this to display org details or check settings.

`update_organization()` lets you change the name, add/remove domains, or update other metadata.

`delete_organization()` permanently removes the org and all associated data (users, connections, etc.) — use with caution.

**Expected output**

```
Created organization: Acme Corporation
Organization ID: org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
Domains: ['acme.com', 'acmecorp.com']

All organizations:
  - Acme Corporation (org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A)
  - Beta Industries (org_01H5QHGX1Z2R3T4V5W6X7Y8Z9B)
  - Gamma Ltd (org_01H5QHGX1Z2R3T4V5W6X7Y8Z9C)

Retrieved: Acme Corporation
Created at: 2024-01-15T10:30:00.000Z
Updated at: 2024-01-15T10:30:00.000Z

Updated name to: Acme Corp (updated)

Deleted organization: org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
```

**Gotchas**
- Domain verification requires the customer to add a DNS TXT record — pending domains won't auto-assign users until verified.
- Deleting an organization cascades to all users, connections, and directory syncs — there's no undo.
- Organization IDs are immutable and globally unique — use them as foreign keys in your database.
- auto_paging_iter() fetches all pages lazily — if you have 10,000 orgs it will make many API calls; add limit if you only need the first page.

## How to list and manage users with User Management

You need to fetch, search, and update user profiles in your application, including managing their organization membership and authentication methods.

**Prerequisites**
- WorkOS account with User Management enabled
- At least one organization created
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import NotFoundError

client = WorkOSClient(api_key="sk_example_123456789")

# List users with filters
page = client.user_management.list_users(
    organization_id="org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A",
    limit=10
)

print(f"Found {len(page.data)} users on this page")
for user in page.data:
    print(f"  - {user.email} (ID: {user.id})")
    print(f"    First name: {user.first_name}")
    print(f"    Last name: {user.last_name}")
    print(f"    Email verified: {user.email_verified}")

print(f"\nHas more pages: {page.has_more()}")
if page.has_more():
    print(f"Next page cursor: {page.after}")

# Search users by email
print("\nSearching for users with email containing 'alice':")
for user in client.user_management.list_users(email="alice").auto_paging_iter():
    print(f"  Found: {user.email}")

# Get a specific user
try:
    user_id = "user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"
    user = client.user_management.get_user(user=user_id)
    
    print(f"\nUser details:")
    print(f"  Email: {user.email}")
    print(f"  Name: {user.first_name} {user.last_name}")
    print(f"  Profile picture: {user.profile_picture_url}")
    print(f"  Created at: {user.created_at}")
    print(f"  Updated at: {user.updated_at}")
    
except NotFoundError as e:
    print(f"User not found: {e.message}")

# Update a user
updated_user = client.user_management.update_user(
    user=user_id,
    first_name="Alice",
    last_name="Johnson",
    email_verified=True
)
print(f"\nUpdated user: {updated_user.first_name} {updated_user.last_name}")

# Delete a user
client.user_management.delete_user(user=user_id)
print(f"Deleted user: {user_id}")
```

WorkOS User Management gives you a complete user database with authentication built in.

`list_users()` returns paginated results.
You can filter by `organization_id` to see only users in a specific org, or by `email` to search.
The returned `page.data` is a list of user objects; `page.has_more()` tells you if there are more pages.

For a single page, work with `page.data` directly.
For all users, use `auto_paging_iter()` which automatically fetches subsequent pages as you iterate.

`get_user()` fetches a single user by their WorkOS user ID.
The user object includes email, name, verification status, profile picture URL, and timestamps.

`update_user()` lets you change the user's name, email, verification status, or other fields.
This is useful for admin panels or profile editing features.

`delete_user()` permanently removes the user — they'll no longer be able to authenticate.

**Expected output**

```
Found 10 users on this page
  - alice@example.com (ID: user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A)
    First name: Alice
    Last name: Smith
    Email verified: True
  - bob@example.com (ID: user_01H5QHGX1Z2R3T4V5W6X7Y8Z9B)
    First name: Bob
    Last name: Jones
    Email verified: False
  ...

Has more pages: True
Next page cursor: eyJhZnRlciI6InVzZXJfMDFINVFIR1gxWjJSM1Q0VjVXNlg3WThaOUMifQ==

Searching for users with email containing 'alice':
  Found: alice@example.com
  Found: alice.wonder@example.com

User details:
  Email: alice@example.com
  Name: Alice Smith
  Profile picture: https://api.workos.com/uploads/profile_pictures/abc123.jpg
  Created at: 2024-01-10T09:00:00.000Z
  Updated at: 2024-01-15T14:20:00.000Z

Updated user: Alice Johnson
Deleted user: user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
```

**Gotchas**
- User IDs are different from SSO profile IDs — when a user logs in via SSO, WorkOS creates a user record and links it to the SSO identity.
- Deleting a user doesn't automatically remove them from connected identity providers (Okta, etc.) — they're still managed there.
- Email search is case-insensitive and does substring matching, so 'alice' finds 'alice@example.com' and 'malice@example.com'.
- The email_verified flag doesn't prevent login — it's informational; you enforce verification logic in your app.

## How to sync directory data from identity providers

Enterprise customers use identity providers like Okta or Azure AD as their source of truth for users and groups. You need to automatically sync that data into your application.

**Prerequisites**
- WorkOS account with Directory Sync enabled
- A directory connection set up in the WorkOS dashboard (SCIM or Azure AD)
- Python 3.8 or later

```python
from workos import WorkOSClient

client = WorkOSClient(api_key="sk_example_123456789")

# List all directory connections
print("Directory connections:")
for directory in client.directory_sync.list_directories().auto_paging_iter():
    print(f"  - {directory.name} (ID: {directory.id})")
    print(f"    Type: {directory.type}")
    print(f"    State: {directory.state}")
    print(f"    Organization: {directory.organization_id}")

# Get users from a specific directory
directory_id = "directory_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"
print(f"\nUsers in directory {directory_id}:")

for user in client.directory_sync.list_users(directory=directory_id).auto_paging_iter():
    print(f"  - {user.username} ({user.emails[0]['value'] if user.emails else 'no email'})")
    print(f"    ID: {user.id}")
    print(f"    First name: {user.first_name}")
    print(f"    Last name: {user.last_name}")
    print(f"    State: {user.state}")
    print(f"    Groups: {len(user.groups)}")

# Get groups from a directory
print(f"\nGroups in directory {directory_id}:")
for group in client.directory_sync.list_groups(directory=directory_id).auto_paging_iter():
    print(f"  - {group.name} (ID: {group.id})")

# Get a specific directory user
user_id = "directory_user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"
dir_user = client.directory_sync.get_user(user=user_id)
print(f"\nDirectory user details:")
print(f"  Username: {dir_user.username}")
print(f"  Primary email: {dir_user.emails[0]['value'] if dir_user.emails else 'N/A'}")
print(f"  Job title: {dir_user.job_title}")
print(f"  Raw attributes: {dir_user.raw_attributes}")

# Get a specific group
group_id = "directory_group_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"
dir_group = client.directory_sync.get_group(group=group_id)
print(f"\nGroup details:")
print(f"  Name: {dir_group.name}")
print(f"  Members: {len(dir_group.raw_attributes.get('members', []))}")
```

Directory Sync automatically keeps your app's user/group data in sync with enterprise identity providers.

`list_directories()` shows all configured directory connections.
Each directory has a `type` (azure_scim_v2_0, okta_scim_v2_0, google, etc.), a `state` (linked, unlinked, invalid_credentials), and links to an organization.

`list_users(directory=...)` fetches all users from a specific directory.
Directory users have standard fields like `username`, `first_name`, `last_name`, `emails`, and a `state` (active, inactive, suspended).
The `groups` field shows which directory groups this user belongs to.

`list_groups(directory=...)` gets all groups from the directory.
Groups have a `name` and member list.

`get_user()` and `get_group()` fetch individual records by ID.
The `raw_attributes` field contains the full unmodified data from the identity provider — useful when you need custom attributes the SDK doesn't expose.

Common pattern: listen for `dsync.user.created` and `dsync.user.deleted` webhooks to update your database in real-time instead of polling.

**Expected output**

```
Directory connections:
  - Acme Corp Okta (ID: directory_01H5QHGX1Z2R3T4V5W6X7Y8Z9A)
    Type: okta_scim_v2_0
    State: linked
    Organization: org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
  - Beta Azure AD (ID: directory_01H5QHGX1Z2R3T4V5W6X7Y8Z9B)
    Type: azure_scim_v2_0
    State: linked
    Organization: org_01H5QHGX1Z2R3T4V5W6X7Y8Z9B

Users in directory directory_01H5QHGX1Z2R3T4V5W6X7Y8Z9A:
  - alice.smith (alice.smith@acme.com)
    ID: directory_user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
    First name: Alice
    Last name: Smith
    State: active
    Groups: 2
  - bob.jones (bob.jones@acme.com)
    ID: directory_user_01H5QHGX1Z2R3T4V5W6X7Y8Z9B
    First name: Bob
    Last name: Jones
    State: active
    Groups: 1

Groups in directory directory_01H5QHGX1Z2R3T4V5W6X7Y8Z9A:
  - Engineering (ID: directory_group_01H5QHGX1Z2R3T4V5W6X7Y8Z9A)
  - Marketing (ID: directory_group_01H5QHGX1Z2R3T4V5W6X7Y8Z9B)

Directory user details:
  Username: alice.smith
  Primary email: alice.smith@acme.com
  Job title: Senior Engineer
  Raw attributes: {'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'], ...}

Group details:
  Name: Engineering
  Members: 15
```

**Gotchas**
- Directory users are separate from User Management users — they're a read-only mirror of the identity provider data.
- Sync can take 15-30 minutes after initial setup; use the directory state field to check if it's linked and syncing.
- If a directory shows state 'invalid_credentials', the customer needs to regenerate the SCIM bearer token in their IdP.
- Groups don't automatically map to permissions in your app — you need to build that logic yourself using the group membership data.

## How to verify webhook signatures

WorkOS sends webhooks when events happen (user created, SSO login, directory sync update). You need to verify that webhook requests actually came from WorkOS and weren't forged.

**Prerequisites**
- WorkOS account with webhooks configured
- Webhook secret from the WorkOS dashboard
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import SignatureVerificationError
import json

client = WorkOSClient(api_key="sk_example_123456789")

# Your webhook endpoint receives these from the HTTP request
request_body = '{"id":"event_01H5QHGX1Z2R3T4V5W6X7Y8Z9A","event":"user.created","data":{"object":"user","id":"user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A","email":"alice@example.com","first_name":"Alice","last_name":"Smith","email_verified":true,"created_at":"2024-01-15T10:00:00.000Z","updated_at":"2024-01-15T10:00:00.000Z"},"created_at":"2024-01-15T10:00:00.000Z"}'
request_signature = "t=1705316400,v1=7a3f5c8e9d2b4a1c6e8f0d3b5a7c9e1f4d6a8c0e2f4b6d8a0c2e4f6a8c0e2f4b"
request_timestamp = "1705316400"
webhook_secret = "wh_secret_example_123456789"

try:
    # Verify the webhook signature
    webhook = client.webhooks.construct_event(
        payload=request_body,
        sig_header=request_signature,
        secret=webhook_secret,
        tolerance=180  # Allow up to 180 seconds clock skew
    )
    
    print("✓ Webhook signature verified")
    print(f"Event ID: {webhook.id}")
    print(f"Event type: {webhook.event}")
    print(f"Created at: {webhook.created_at}")
    
    # Handle different event types
    if webhook.event == "user.created":
        user_data = webhook.data
        print(f"\nNew user created:")
        print(f"  Email: {user_data['email']}")
        print(f"  Name: {user_data['first_name']} {user_data['last_name']}")
        print(f"  User ID: {user_data['id']}")
        # Add user to your database here
        
    elif webhook.event == "user.updated":
        user_data = webhook.data
        print(f"\nUser updated: {user_data['email']}")
        # Update user in your database here
        
    elif webhook.event == "user.deleted":
        user_data = webhook.data
        print(f"\nUser deleted: {user_data['id']}")
        # Delete user from your database here
        
    elif webhook.event == "dsync.user.created":
        dir_user = webhook.data
        print(f"\nDirectory user synced: {dir_user['username']}")
        # Sync directory user to your database
        
    else:
        print(f"\nUnhandled event type: {webhook.event}")
    
except SignatureVerificationError as e:
    print(f"❌ Webhook signature verification failed: {e.message}")
    print("This webhook request did not come from WorkOS.")
    # Return 400 status code to reject the webhook
```

Webhooks let WorkOS notify your application when events happen — without you needing to poll the API.

Every webhook request includes a signature in the `WorkOS-Signature` header (format: `t=timestamp,v1=hash`).
You must verify this signature to ensure the request came from WorkOS and wasn't tampered with.

`client.webhooks.construct_event()` does the verification for you.
Pass in the raw request body (as a string, before JSON parsing), the signature header, and your webhook secret (from the WorkOS dashboard).

The `tolerance` parameter (default 180 seconds) protects against replay attacks — if the timestamp in the signature is more than 180 seconds old, verification fails.
This means both servers need reasonably accurate clocks.

If verification succeeds, you get a webhook object with the event type (`user.created`, `dsync.user.created`, etc.) and the event data.
Handle each event type with specific logic — creating, updating, or deleting records in your database.

If verification fails, you get a `SignatureVerificationError` — return a 4xx status code so WorkOS knows to stop retrying that webhook.

**Expected output**

```
✓ Webhook signature verified
Event ID: event_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
Event type: user.created
Created at: 2024-01-15T10:00:00.000Z

New user created:
  Email: alice@example.com
  Name: Alice Smith
  User ID: user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A
```

**Gotchas**
- You must pass the raw request body string to construct_event() — if you JSON-parse it first, signature verification will fail.
- The signature header name is 'WorkOS-Signature' (capital W, capital S) — case-sensitive in most frameworks.
- Webhook secrets are different for each environment (development, production) — don't hardcode them; use environment variables.
- WorkOS retries failed webhooks with exponential backoff; if your endpoint is down for an extended period, you may miss events.
- Webhooks can arrive out of order or be duplicated — use the event ID to deduplicate and the timestamp to order them.

## How to check permissions with Fine-Grained Authorization

You need to control what users can do in your application with role-based or attribute-based permissions. FGA lets you define resources, roles, and permissions, then check if a user has access.

**Prerequisites**
- WorkOS account with Fine-Grained Authorization (FGA) enabled
- At least one resource type and role defined
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import AuthorizationError

client = WorkOSClient(api_key="sk_example_123456789")

# Define resources in your application
# Resources can be anything: projects, documents, organizations, etc.
project_id = "project_123"
user_id = "user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A"

# Check if a user has permission to perform an action
try:
    result = client.authorization.check(
        resource={"resource_type": "project", "resource_id": project_id},
        action="project:edit",
        subject={"subject_type": "user", "subject_id": user_id}
    )
    
    if result.permitted:
        print(f"✓ User {user_id} CAN edit project {project_id}")
        print(f"  Reason: {result.reason}")
        # Allow the user to edit the project
    else:
        print(f"✗ User {user_id} CANNOT edit project {project_id}")
        print(f"  Reason: {result.reason}")
        # Return 403 Forbidden
        
except AuthorizationError as e:
    print(f"Authorization check failed: {e.message}")

# Check multiple permissions at once
print("\nChecking multiple permissions:")
batch_results = client.authorization.batch_check(
    checks=[
        {
            "resource": {"resource_type": "project", "resource_id": project_id},
            "action": "project:edit",
            "subject": {"subject_type": "user", "subject_id": user_id}
        },
        {
            "resource": {"resource_type": "project", "resource_id": project_id},
            "action": "project:delete",
            "subject": {"subject_type": "user", "subject_id": user_id}
        },
        {
            "resource": {"resource_type": "project", "resource_id": project_id},
            "action": "project:view",
            "subject": {"subject_type": "user", "subject_id": user_id}
        }
    ]
)

for idx, check in enumerate(batch_results.checks):
    action = ["edit", "delete", "view"][idx]
    status = "✓ CAN" if check.permitted else "✗ CANNOT"
    print(f"  {status} {action}: {check.reason}")

# Assign a role to a user for a resource
print("\nAssigning role to user:")
role_assignment = client.authorization.create_assignment(
    resource={"resource_type": "project", "resource_id": project_id},
    role="project:editor",
    subject={"subject_type": "user", "subject_id": user_id}
)
print(f"Assigned role: {role_assignment.role}")
print(f"Assignment ID: {role_assignment.id}")

# List a user's roles
print(f"\nUser's roles for project {project_id}:")
for assignment in client.authorization.list_assignments(
    resource={"resource_type": "project", "resource_id": project_id},
    subject={"subject_type": "user", "subject_id": user_id}
).auto_paging_iter():
    print(f"  - {assignment.role}")
```

Fine-Grained Authorization (FGA) is WorkOS's permissions system.

`client.authorization.check()` is the core method — it answers "Can this user do this action on this resource?"
You pass a `resource` (the thing being accessed), an `action` (what they're trying to do), and a `subject` (who's trying to do it).

The result has a `permitted` boolean (True/False) and a `reason` string explaining why.
In production, check `permitted` before allowing access to sensitive operations.

`batch_check()` lets you check multiple permissions in one API call — useful when rendering UI (show/hide edit button, delete button, etc. based on permissions).
It returns a list of results in the same order as your input checks.

`create_assignment()` assigns a role to a user for a specific resource.
Roles define sets of permissions — for example, "project:editor" might grant "project:edit" and "project:view" actions.
You define roles and their permissions in the WorkOS dashboard.

`list_assignments()` shows all roles a user has on a resource.
Use this for displaying user permissions in your UI or auditing access.

FGA uses a Zanzibar-style model: resources, subjects, actions, and relations.

**Expected output**

```
✓ User user_01H5QHGX1Z2R3T4V5W6X7Y8Z9A CAN edit project project_123
  Reason: Subject has role 'project:editor'

Checking multiple permissions:
  ✓ CAN edit: Subject has role 'project:editor'
  ✗ CANNOT delete: Subject does not have permission 'project:delete'
  ✓ CAN view: Subject has role 'project:editor' which includes 'project:view'

Assigning role to user:
Assigned role: project:editor
Assignment ID: role_assignment_01H5QHGX1Z2R3T4V5W6X7Y8Z9A

User's roles for project project_123:
  - project:editor
```

**Gotchas**
- You must define resource types, actions, and roles in the WorkOS dashboard before checking permissions — the API won't auto-create them.
- The check() method doesn't modify permissions; it only evaluates them — use create_assignment() to grant access.
- Role assignments are scoped to a specific resource — assigning 'editor' on project_123 doesn't grant access to project_456.
- batch_check() is atomic per check but not transactional across all checks — if one fails, others still process.
- FGA checks are eventually consistent (typically < 100ms) — immediately after create_assignment(), check() may still return False.

## How to handle errors and retries

API calls can fail due to network issues, rate limits, or invalid requests. You need to handle errors gracefully and implement retry logic for transient failures.

**Prerequisites**
- WorkOS account
- Python 3.8 or later

```python
from workos import WorkOSClient
from workos._errors import (
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    RateLimitExceededError,
    ServerError,
    WorkOSError
)
import time

client = WorkOSClient(api_key="sk_example_123456789")

# Example 1: Handle specific error types
try:
    org = client.organizations.get_organization(organization="org_nonexistent")
except NotFoundError as e:
    print(f"Organization not found: {e.message}")
    print(f"Status code: {e.status_code}")  # 404
    print(f"Request ID: {e.request_id}")  # For support tickets
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
    # Check your API key configuration
except AuthorizationError as e:
    print(f"Insufficient permissions: {e.message}")
    # This API key doesn't have access to this resource

# Example 2: Handle rate limiting with exponential backoff
def get_organization_with_retry(org_id: str, max_retries: int = 3):
    """Retry with exponential backoff on rate limit errors."""
    for attempt in range(max_retries):
        try:
            return client.organizations.get_organization(organization=org_id)
        except RateLimitExceededError as e:
            if attempt < max_retries - 1:
                retry_after = e.retry_after or (2 ** attempt)  # Exponential backoff
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                print(f"Max retries exceeded: {e.message}")
                raise
        except ServerError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Server error {e.status_code}. Retrying after {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

try:
    org = get_organization_with_retry("org_01H5QHGX1Z2R3T4V5W6X7Y8Z9A")
    print(f"Retrieved: {org.name}")
except WorkOSError as e:
    print(f"Failed after retries: {e.message}")

# Example 3: Validate input to avoid BadRequestError
try:
    # Missing required field
    org = client.organizations.create_organization(name="")  # Empty name
except BadRequestError as e:
    print(f"Validation error: {e.message}")
    # e.message might contain: "name must not be empty"
    
try:
    # Invalid email format
    user = client.user_management.create_user(
        email="not-an-email",
        password="password123"
    )
except UnprocessableEntityError as e:
    print(f"Invalid data: {e.message}")

# Example 4: Per-request configuration for different error scenarios
try:
    # Increase timeout for slow operations
    result = client.organizations.list_organizations(
        request_options={
            "timeout": 120,  # 2 minutes
            "max_retries": 5  # More retries for important operations
        }
    )
except Exception as e:
    print(f"Request failed: {e}")

# Example 5: Catch all WorkOS errors
try:
    org = client.organizations.get_organization(organization="org_123")
except WorkOSError as e:
    # Base class for all WorkOS exceptions
    print(f"WorkOS error: {e.message}")
    print(f"Status: {e.status_code}")
    print(f"Request ID: {e.request_id}")
    # Log to your error tracking system (Sentry, etc.)
except Exception as e:
    # Network errors, parsing errors, etc.
    print(f"Unexpected error: {e}")
```

The WorkOS SDK maps HTTP error codes to specific exception classes, making error handling type-safe.

`NotFoundError` (404) means the resource doesn't exist — check the ID or create it first.
`AuthenticationError` (401) means your API key is invalid or missing.
`AuthorizationError` (403) means your API key doesn't have permission for this operation.
`BadRequestError` (400) means you passed invalid parameters — check required fields and formats.
`UnprocessableEntityError` (422) means the data is invalid (bad email format, etc.).

`RateLimitExceededError` (429) means you hit WorkOS's rate limits.
The exception includes a `retry_after` property telling you how many seconds to wait.
Implement exponential backoff: wait 1s, then 2s, then 4s, etc.

`ServerError` (5xx) means WorkOS had an internal error — these are rare and usually transient.
Retry with exponential backoff; most resolve within seconds.

Every exception has a `request_id` — include this in support tickets for faster debugging.

The SDK automatically retries failed requests (configurable with `max_retries`), but you may want additional application-level retry logic for critical operations.

All WorkOS exceptions inherit from `WorkOSError`, so you can catch that as a fallback.

**Expected output**

```
Organization not found: The organization with id 'org_nonexistent' was not found.
Status code: 404
Request ID: req_01H5QHGX1Z2R3T4V5W6X7Y8Z9A

Rate limited. Retrying after 1 seconds...
Retrieved: Acme Corporation

Validation error: name must not be empty

Invalid data: email must be a valid email address
```

**Gotchas**
- Rate limits are per API key and per endpoint — different endpoints have different limits.
- RateLimitExceededError.retry_after is in seconds (integer), not milliseconds.
- Retrying on 5xx errors is safe (they're idempotent), but retrying on 4xx errors (except 429) usually doesn't help — fix the request instead.
- The SDK's automatic retry logic applies to network errors and 5xx, not 4xx — handle 4xx explicitly.
- request_id is only present for errors that made it to WorkOS's servers — connection timeouts won't have one.

## FAQ

### Do I need both api_key and client_id to use WorkOS?

It depends on which features you use. SSO authorization requires client_id (it's part of the OAuth flow). Most other operations (organizations, users, directory sync) only need api_key. If you're unsure, set both — the SDK will use whichever is needed.

### What's the difference between User Management users and Directory Sync users?

User Management users are managed by WorkOS and live in your WorkOS account — you create/update/delete them. Directory Sync users are read-only mirrors of users in a customer's identity provider (Okta, Azure AD) — they update automatically when the customer changes them in their IdP.

### How do I test webhooks locally without deploying?

Use a tool like ngrok to expose your local server to the internet, then configure that URL in the WorkOS dashboard. WorkOS will send webhooks to your ngrok URL, which forwards them to localhost. Always verify the webhook signature even in development.

### Can I use the async client in a sync codebase (or vice versa)?

No, WorkOSClient and AsyncWorkOSClient are separate. Use AsyncWorkOSClient in async/await codebases (FastAPI, aiohttp, asyncio apps). Use WorkOSClient in sync codebases (Flask, Django, scripts). You can't mix them in the same request.

### What happens if I delete an organization that has active SSO connections?

Deleting an organization cascades — it removes all associated SSO connections, directory syncs, users, and other data. Users from that org won't be able to log in afterward. This is permanent and can't be undone, so add a confirmation step before deletion.

## Key takeaways

- WorkOS provides enterprise-ready authentication (SSO, Directory Sync) and authorization (FGA) as simple Python APIs — no need to integrate with each identity provider separately.
- The SDK is fully typed with dataclasses and works with mypy/pyright — use IDE autocomplete to discover available methods and fields.
- Use auto_paging_iter() on list methods to iterate through all results without manual cursor handling; it fetches pages lazily as you iterate.
- Always verify webhook signatures with client.webhooks.construct_event() to prevent forged requests — pass the raw request body, not the parsed JSON.
- Handle RateLimitExceededError with exponential backoff and use the retry_after property to avoid getting rate-limited repeatedly.
- SSO, User Management, and Directory Sync work together: users authenticate via SSO, their profiles live in User Management, and Directory Sync keeps enterprise data in sync automatically.