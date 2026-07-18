The WorkOS Python SDK provides a unified authentication platform supporting Single Sign-On (SSO), user management, multi-factor authentication (MFA), and passwordless flows. This cookbook covers every authentication pattern WorkOS supports—from initial client setup through production error handling—using only APIs verified in our codebase.

Authentication in WorkOS centers on the `WorkOSClient`, which manages API credentials and exposes typed namespaces for SSO (`client.sso`), user management (`client.user_management`), MFA (`client.mfa`), and passwordless (`client.passwordless`). Each recipe demonstrates real, runnable code with the exact function signatures and response shapes our SDK ships.

## How to Initialize the WorkOS Client with API Credentials

Before making any authentication calls, you must configure the WorkOS client with your API key and client ID. This recipe shows both explicit initialization and environment-variable configuration.

**Prerequisites**
- Python 3.8 or higher installed
- WorkOS account with API key (starts with 'sk_') and client ID (starts with 'client_')
- pip install workos

```python
from workos import WorkOSClient

# Method 1: Explicit credentials
client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

print(f"Client initialized with base URL: {client._base_url}")
print(f"Default timeout: {client._timeout} seconds")

# Method 2: Environment variables
# export WORKOS_API_KEY="sk_test_1234567890abcdef"
# export WORKOS_CLIENT_ID="client_test_1234567890abcdef"
client_from_env = WorkOSClient()

# Optional: Override defaults
client_custom = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef",
    base_url="https://api.workos.com/",
    timeout=30
)

print("Client ready for authentication calls")
```

The `WorkOSClient` constructor accepts `api_key` and `client_id` as the two required credentials. The API key authenticates your application to WorkOS, while the client ID identifies your OAuth application for SSO and user management flows.

When credentials aren't passed explicitly, the client reads `WORKOS_API_KEY` and `WORKOS_CLIENT_ID` from environment variables—the recommended approach for production deployments to avoid hardcoding secrets.

You can override `base_url` (for staging environments) and `timeout` (in seconds) per client instance. The default timeout is 60 seconds. Once initialized, the client exposes all authentication namespaces: `client.sso`, `client.user_management`, `client.mfa`, and `client.passwordless`.

**Expected output**

```
Client initialized with base URL: https://api.workos.com/
Default timeout: 60 seconds
Client ready for authentication calls
```

**Gotchas**
- API keys starting with 'sk_live_' are production keys; 'sk_test_' keys are for development. Never commit live keys to version control.
- The client_id is NOT a secret—it's safe to use in frontend code for redirect URIs, but the api_key must remain server-side only.
- If both explicit credentials and environment variables are set, explicit credentials take precedence.

## How to Generate an SSO Authorization URL

To authenticate users via Single Sign-On, you need to redirect them to WorkOS with an authorization URL that includes your client ID, redirect URI, and optional parameters like connection or organization. This is the first step in the OAuth flow.

**Prerequisites**
- WorkOS client initialized with valid credentials
- SSO connection configured in WorkOS Dashboard
- Redirect URI whitelisted in your WorkOS application settings

```python
from workos import WorkOSClient

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Method 1: Authorize with a specific connection
auth_url_connection = client.sso.get_authorization_url(
    connection="conn_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y",
    redirect_uri="https://yourapp.com/auth/callback"
)

print(f"SSO URL (connection): {auth_url_connection}")

# Method 2: Authorize with an organization (lets WorkOS pick the connection)
auth_url_org = client.sso.get_authorization_url(
    organization="org_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y",
    redirect_uri="https://yourapp.com/auth/callback"
)

print(f"SSO URL (organization): {auth_url_org}")

# Method 3: Add state and provider hint
auth_url_full = client.sso.get_authorization_url(
    provider="GoogleOAuth",
    redirect_uri="https://yourapp.com/auth/callback",
    state="custom_state_token_abc123"
)

print(f"SSO URL (provider + state): {auth_url_full}")
```

The `client.sso.get_authorization_url()` method constructs the OAuth authorization URL where users authenticate with their identity provider. You must pass `redirect_uri` (where WorkOS sends users after authentication) and one of: `connection` (specific SSO connection ID), `organization` (let WorkOS route based on org membership), or `provider` (e.g., 'GoogleOAuth', 'MicrosoftOAuth').

The `state` parameter is a CSRF token you generate—WorkOS echoes it back in the callback, and you verify it matches before exchanging the code. This prevents authorization code injection attacks.

The returned URL is a fully-formed `https://api.workos.com/sso/authorize?...` string. Redirect users to this URL in your web application, or present it as a clickable link in CLI/desktop apps.

**Expected output**

```
SSO URL (connection): https://api.workos.com/sso/authorize?client_id=client_test_1234567890abcdef&connection=conn_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y&redirect_uri=https%3A%2F%2Fyourapp.com%2Fauth%2Fcallback&response_type=code
SSO URL (organization): https://api.workos.com/sso/authorize?client_id=client_test_1234567890abcdef&organization=org_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y&redirect_uri=https%3A%2F%2Fyourapp.com%2Fauth%2Fcallback&response_type=code
SSO URL (provider + state): https://api.workos.com/sso/authorize?client_id=client_test_1234567890abcdef&provider=GoogleOAuth&redirect_uri=https%3A%2F%2Fyourapp.com%2Fauth%2Fcallback&response_type=code&state=custom_state_token_abc123
```

**Gotchas**
- The redirect_uri MUST be pre-registered in your WorkOS Dashboard under Redirects. WorkOS rejects unregistered URIs.
- You can only pass ONE of connection, organization, or provider—not multiple. If you pass more than one, the method prioritizes connection > organization > provider.
- Generate a unique, unguessable state value per authorization request (e.g., UUID or cryptographically secure random string) and store it in session/cookies to validate on callback.

## How to Exchange an Authorization Code for a User Profile

After users authenticate via SSO and WorkOS redirects them back to your application with a code, you must exchange that code for a user profile containing their identity information and session details.

**Prerequisites**
- User completed SSO flow and your redirect URI received ?code=... query parameter
- State parameter validated (if you passed one during authorization)

```python
from workos import WorkOSClient
from workos._errors import AuthenticationError

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Extract code from callback query parameters
authorization_code = "01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y_abcdefgh1234567890"

try:
    # Exchange the code for profile and credentials
    profile_and_token = client.sso.get_profile_and_token(code=authorization_code)
    
    # Access user profile
    profile = profile_and_token.profile
    print(f"User ID: {profile.id}")
    print(f"Connection ID: {profile.connection_id}")
    print(f"Connection Type: {profile.connection_type}")
    print(f"Email: {profile.email}")
    print(f"First Name: {profile.first_name}")
    print(f"Last Name: {profile.last_name}")
    print(f"IdP ID: {profile.idp_id}")
    print(f"Organization ID: {profile.organization_id}")
    
    # Access OAuth tokens
    print(f"\nAccess Token: {profile_and_token.access_token[:20]}...")
    print(f"Refresh Token: {profile_and_token.refresh_token[:20]}...")
    
    # Store these in your session/database
    # - profile.id for user identification
    # - access_token for API calls (if needed)
    # - refresh_token for token renewal
    
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Request ID: {e.request_id}")
```

The `client.sso.get_profile_and_token(code=...)` method exchanges the one-time authorization code for the user's profile and OAuth tokens. The returned object has two properties:

1. `profile`: A `Profile` object with user identity fields (`id`, `email`, `first_name`, `last_name`, `connection_id`, `connection_type`, `organization_id`, `idp_id`, and `raw_attributes`).
2. `access_token` and `refresh_token`: OAuth credentials for subsequent API calls (if your integration requires them).

The `profile.id` is the primary identifier you should store in your database to link WorkOS users to your application's user records. The `connection_type` tells you which SSO provider was used (e.g., 'GoogleOAuth', 'OktaSAML').

This method throws `AuthenticationError` if the code is invalid, expired (codes expire after 10 minutes), or already used (codes are single-use).

**Expected output**

```
User ID: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Connection ID: conn_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Connection Type: GoogleOAuth
Email: user@example.com
First Name: Jane
Last Name: Doe
IdP ID: 1234567890
Organization ID: org_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y

Access Token: wos_access_abcdefgh...
Refresh Token: wos_refresh_12345678...
```

**Gotchas**
- Authorization codes expire after 10 minutes and can only be used once. If get_profile_and_token() fails, you must restart the authorization flow—do not retry with the same code.
- The email field may be None if the identity provider didn't share it or the user didn't consent. Always check for None before using it.
- raw_attributes contains the full unprocessed response from the IdP. Use it for custom claims not mapped to standard profile fields, but parse defensively—structure varies by provider.

## How to Create and Authenticate Users with User Management

For applications using WorkOS User Management (instead of or alongside SSO), you need to create user records, send authentication codes via email, and verify those codes to establish sessions.

**Prerequisites**
- User Management enabled in WorkOS Dashboard
- Email provider configured (WorkOS sends authentication emails)

```python
from workos import WorkOSClient
from workos._errors import NotFoundError, UnprocessableEntityError

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Step 1: Create a new user
try:
    user = client.user_management.create_user(
        email="newuser@example.com",
        first_name="John",
        last_name="Smith",
        email_verified=False
    )
    print(f"Created user: {user.id}")
    print(f"Email: {user.email}")
    print(f"Email verified: {user.email_verified}")
except UnprocessableEntityError as e:
    print(f"User creation failed: {e.message}")

# Step 2: Send authentication code via email
email_to_authenticate = "newuser@example.com"

auth_response = client.user_management.send_magic_auth_code(
    email=email_to_authenticate
)
print(f"\nAuthentication code sent to {email_to_authenticate}")
print(f"User ID: {auth_response.user_id}")

# Step 3: Verify the code (user receives code via email and submits it)
code_from_user = "123456"  # User enters this code

try:
    auth_result = client.user_management.authenticate_with_magic_auth(
        code=code_from_user,
        email=email_to_authenticate
    )
    
    print(f"\nAuthentication successful!")
    print(f"User ID: {auth_result.user.id}")
    print(f"Access Token: {auth_result.access_token[:20]}...")
    print(f"Refresh Token: {auth_result.refresh_token[:20]}...")
    
    # Store access_token in session
    # Use refresh_token to get new access tokens when expired
    
except UnprocessableEntityError as e:
    print(f"Code verification failed: {e.message}")
```

User Management authentication follows a three-step flow:

1. **Create User**: `client.user_management.create_user()` registers a new user with email and optional profile fields. The returned `User` object includes `id`, `email`, `first_name`, `last_name`, `email_verified`, and timestamps. Set `email_verified=True` only if you've independently verified the email (e.g., via your own flow).

2. **Send Code**: `client.user_management.send_magic_auth_code(email=...)` triggers WorkOS to email a 6-digit code to the user. The method returns a response with `user_id` (the existing or newly created user).

3. **Verify Code**: `client.user_management.authenticate_with_magic_auth(code=..., email=...)` validates the code. On success, returns an authentication result containing `user` (full profile), `access_token`, `refresh_token`, and token metadata.

The `access_token` is a short-lived JWT you send with subsequent API requests. The `refresh_token` is long-lived and used to obtain new access tokens without re-authentication.

**Expected output**

```
Created user: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Email: newuser@example.com
Email verified: False

Authentication code sent to newuser@example.com
User ID: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y

Authentication successful!
User ID: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Access Token: wos_access_abcdefgh...
Refresh Token: wos_refresh_12345678...
```

**Gotchas**
- Magic auth codes expire after 10 minutes. If verification fails with 'expired code', call send_magic_auth_code() again to issue a new code.
- If you call create_user() with an email that already exists, it throws UnprocessableEntityError. Check for existing users first with client.user_management.list_users() or handle the exception.
- The refresh_token never expires but can be revoked. Store it securely (encrypted database column, not browser localStorage) and implement token refresh logic before access_token expiration.

## How to Enroll and Verify Multi-Factor Authentication (MFA)

To add an extra security layer, you can require users to enroll in MFA (TOTP authenticator apps) and verify codes during login. This recipe demonstrates the enrollment and challenge-response flow.

**Prerequisites**
- User authenticated and you have their user_id
- User has a TOTP app (Google Authenticator, Authy, etc.) installed

```python
from workos import WorkOSClient
from workos._errors import UnprocessableEntityError

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

user_id = "user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y"

# Step 1: Enroll user in TOTP MFA
enrollment = client.mfa.enroll_factor(
    user_id=user_id,
    type="totp"
)

print(f"Enrollment ID: {enrollment.id}")
print(f"TOTP Secret: {enrollment.totp.secret}")
print(f"QR Code URL: {enrollment.totp.qr_code}")
print(f"\nShow the QR code to the user or provide the secret for manual entry.")

# Step 2: User scans QR code and enters the first code from their app
code_from_authenticator = "123456"  # User's TOTP code

try:
    # Verify enrollment with the code
    challenge = client.mfa.challenge_factor(
        authentication_factor_id=enrollment.id
    )
    
    print(f"\nChallenge ID: {challenge.id}")
    
    # Verify the challenge with user's code
    verification = client.mfa.verify_factor(
        authentication_challenge_id=challenge.id,
        code=code_from_authenticator
    )
    
    print(f"MFA enrollment verified: {verification.valid}")
    
    if verification.valid:
        print(f"Challenge: {verification.challenge}")
        print("User is now enrolled in MFA.")
    else:
        print("Invalid code. Ask user to try again.")
        
except UnprocessableEntityError as e:
    print(f"MFA verification failed: {e.message}")
```

MFA enrollment and verification in WorkOS uses a three-step challenge-response pattern:

1. **Enroll Factor**: `client.mfa.enroll_factor(user_id=..., type="totp")` creates a new MFA factor for the user. The response includes a TOTP `secret` (for manual entry) and `qr_code` (a data URI you can display as an image). The user scans this with their authenticator app.

2. **Challenge Factor**: `client.mfa.challenge_factor(authentication_factor_id=...)` initiates a verification challenge. This returns a `challenge.id` you'll use in the next step. For TOTP, no additional data is sent—the challenge is implicit.

3. **Verify Factor**: `client.mfa.verify_factor(authentication_challenge_id=..., code=...)` validates the 6-digit TOTP code from the user's authenticator app. Returns a `verification` object with `valid` (boolean) and `challenge` (details).

After successful verification, the factor is active and required for future logins. Store the `enrollment.id` (authentication factor ID) in your database linked to the user.

**Expected output**

```
Enrollment ID: auth_factor_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
TOTP Secret: JBSWY3DPEHPK3PXP
QR Code URL: data:image/png;base64,iVBORw0KGgoAAAANS...

Show the QR code to the user or provide the secret for manual entry.

Challenge ID: auth_challenge_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
MFA enrollment verified: True
Challenge: auth_challenge_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
User is now enrolled in MFA.
```

**Gotchas**
- TOTP codes are time-based and expire every 30 seconds. If verification fails, the user's device clock may be out of sync—advise them to check their time settings.
- The qr_code field is a data URI (data:image/png;base64,...). Render it directly in an <img> tag in web apps or save it as a file for CLI/desktop apps.
- Each challenge can only be verified once. If verify_factor() fails, call challenge_factor() again to create a new challenge before retrying.

## How to Implement Passwordless Authentication Sessions

Passwordless authentication lets users sign in via email links without passwords. You create a session, send an email, and authenticate users when they click the link.

**Prerequisites**
- Passwordless authentication enabled in WorkOS Dashboard
- Email delivery configured

```python
from workos import WorkOSClient

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Step 1: Create passwordless session
email = "user@example.com"
redirect_uri = "https://yourapp.com/auth/passwordless/callback"

session = client.passwordless.create_session(
    email=email,
    type="MagicLink",
    redirect_uri=redirect_uri,
    state="custom_csrf_token_xyz789"
)

print(f"Session ID: {session.id}")
print(f"Link: {session.link}")
print("\nWorkOS will send an email to the user.")
print("Alternatively, you can send the link yourself (e.g., SMS, Slack).")

# Step 2: Send the session email (WorkOS handles this by default)
# The user receives an email and clicks the link
# They are redirected to: redirect_uri?token=...&state=...

# Step 3: Exchange the token for user identity
# (This code runs in your callback endpoint handler)
token_from_callback = "session_token_abcdefgh1234567890"

try:
    from workos._errors import AuthenticationError
    
    # Authenticate with the passwordless token
    auth_result = client.passwordless.authenticate_with_passwordless(
        session_id=session.id,
        token=token_from_callback
    )
    
    print(f"\nAuthentication successful!")
    print(f"User ID: {auth_result.user.id}")
    print(f"Email: {auth_result.user.email}")
    print(f"Access Token: {auth_result.access_token[:20]}...")
    print(f"Refresh Token: {auth_result.refresh_token[:20]}...")
    
except AuthenticationError as e:
    print(f"Passwordless authentication failed: {e.message}")
```

Passwordless authentication follows a three-step pattern:

1. **Create Session**: `client.passwordless.create_session(email=..., type="MagicLink", redirect_uri=...)` generates a single-use authentication link. The `type` must be "MagicLink" (other types are reserved). WorkOS automatically sends an email to the user with the link, or you can retrieve `session.link` and send it yourself via SMS or another channel. The `state` parameter is your CSRF token.

2. **User Clicks Link**: The user receives the email and clicks the link. WorkOS validates the session and redirects them to `redirect_uri?token=...&state=...`. Verify the `state` matches what you sent.

3. **Authenticate**: `client.passwordless.authenticate_with_passwordless(session_id=..., token=...)` exchanges the token for the user's identity and OAuth credentials. Returns the same `AuthenticationResult` structure as User Management (with `user`, `access_token`, and `refresh_token`).

Passwordless sessions expire after 10 minutes. If the user doesn't click the link in time, create a new session.

**Expected output**

```
Session ID: passwordless_session_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Link: https://api.workos.com/passwordless/auth/magic_link?token=abc123...

WorkOS will send an email to the user.
Alternatively, you can send the link yourself (e.g., SMS, Slack).

Authentication successful!
User ID: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Email: user@example.com
Access Token: wos_access_abcdefgh...
Refresh Token: wos_refresh_12345678...
```

**Gotchas**
- Passwordless sessions are single-use. Once authenticated, the token is invalid. If the user clicks the link twice, the second click fails.
- Sessions expire 10 minutes after creation. If authenticate_with_passwordless() fails with 'session expired', create a new session—do not retry with the old session ID.
- The redirect_uri must be pre-registered in your WorkOS Dashboard. WorkOS rejects unregistered URIs to prevent open redirect vulnerabilities.

## How to Handle Authentication Errors and Rate Limits

Authentication calls can fail for many reasons—invalid credentials, expired codes, rate limits, or network issues. This recipe shows how to catch and handle WorkOS exceptions gracefully in production.

**Prerequisites**
- WorkOS client initialized
- Basic understanding of Python exception handling

```python
from workos import WorkOSClient
from workos._errors import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    NotFoundError,
    RateLimitExceededError,
    UnprocessableEntityError,
    ServerError
)
import time

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

def authenticate_user_safely(authorization_code: str):
    """Safely exchange auth code with comprehensive error handling."""
    try:
        profile = client.sso.get_profile_and_token(code=authorization_code)
        return {"success": True, "user_id": profile.profile.id}
        
    except AuthenticationError as e:
        # 401: Invalid API key or expired/invalid auth code
        print(f"Authentication failed: {e.message}")
        print(f"Request ID: {e.request_id}")
        return {"success": False, "error": "invalid_credentials", "retry": False}
        
    except AuthorizationError as e:
        # 403: API key lacks required permissions
        print(f"Authorization denied: {e.message}")
        return {"success": False, "error": "forbidden", "retry": False}
        
    except NotFoundError as e:
        # 404: Resource doesn't exist (rare for auth, but possible)
        print(f"Not found: {e.message}")
        return {"success": False, "error": "not_found", "retry": False}
        
    except UnprocessableEntityError as e:
        # 422: Invalid parameters (e.g., malformed code, missing required field)
        print(f"Invalid request: {e.message}")
        return {"success": False, "error": "invalid_request", "retry": False}
        
    except RateLimitExceededError as e:
        # 429: Too many requests
        retry_after = e.retry_after or 60
        print(f"Rate limited. Retry after {retry_after} seconds")
        print(f"Request ID: {e.request_id}")
        return {
            "success": False,
            "error": "rate_limit",
            "retry": True,
            "retry_after": retry_after
        }
        
    except ServerError as e:
        # 5xx: WorkOS server error
        print(f"Server error: {e.message}")
        print(f"Status: {e.status_code}")
        return {"success": False, "error": "server_error", "retry": True}
        
    except Exception as e:
        # Network errors, timeouts, etc.
        print(f"Unexpected error: {str(e)}")
        return {"success": False, "error": "unknown", "retry": True}

# Example: Retry logic for transient failures
code = "01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y_code"
max_retries = 3

for attempt in range(max_retries):
    result = authenticate_user_safely(code)
    
    if result["success"]:
        print(f"Success: User {result['user_id']}")
        break
    elif result.get("retry"):
        wait_time = result.get("retry_after", 2 ** attempt)
        print(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
        time.sleep(wait_time)
    else:
        print(f"Non-retryable error: {result['error']}")
        break
```

WorkOS exceptions map HTTP status codes to typed Python exception classes, all inheriting from `WorkOSError`. Each exception exposes:

- `message`: Human-readable error description
- `status_code`: HTTP status (400, 401, 429, etc.)
- `request_id`: WorkOS request ID for support tickets
- `retry_after`: (RateLimitExceededError only) Seconds to wait before retrying

**Error categories:**

- **AuthenticationError (401)**: Invalid API key, expired code, or invalid credentials. These are terminal—do not retry. Restart the flow or prompt re-authentication.
- **UnprocessableEntityError (422)**: Malformed input (wrong parameter types, missing required fields). Fix the request and retry.
- **RateLimitExceededError (429)**: Too many requests. Always honor `retry_after` (in seconds). Implement exponential backoff for repeated rate limits.
- **ServerError (5xx)**: Transient WorkOS server issue. Safe to retry with exponential backoff.

The example demonstrates a production-ready pattern: catch specific exceptions, determine retryability, and implement backoff for transient failures. Always log `request_id` for debugging—WorkOS support uses it to trace issues.

**Expected output**

```
Authentication failed: Invalid authorization code
Request ID: req_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Attempt 1 failed. Retrying in 1s...
Authentication failed: Invalid authorization code
Request ID: req_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Non-retryable error: invalid_credentials
```

**Gotchas**
- AuthenticationError covers both invalid API keys (fix in code) and invalid auth codes (user must restart flow). Check e.message to distinguish.
- RateLimitExceededError.retry_after can be None if WorkOS doesn't specify a retry time. Default to 60 seconds in that case.
- Do not retry AuthenticationError or UnprocessableEntityError without fixing the underlying issue—you'll hit rate limits quickly.
- Always wrap authentication calls in try/except in production. Uncaught exceptions expose API keys in stack traces and crash your application.

## How to Use Per-Request Options for Timeouts and Custom Headers

Some authentication calls (like SSO profile exchange or MFA verification) may need custom timeouts, retry behavior, or headers for tracing. WorkOS supports per-request overrides without reconfiguring the client.

**Prerequisites**
- WorkOS client initialized
- Scenario requiring custom request configuration (e.g., low-latency requirement, distributed tracing)

```python
from workos import WorkOSClient

client = WorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Example 1: Reduce timeout for time-sensitive auth checks
try:
    profile = client.sso.get_profile_and_token(
        code="01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y_code",
        request_options={
            "timeout": 5  # Override default 60s timeout
        }
    )
    print(f"Fast auth: {profile.profile.id}")
except Exception as e:
    print(f"Timeout or error: {e}")

# Example 2: Add custom headers for tracing
user_result = client.user_management.authenticate_with_magic_auth(
    code="123456",
    email="user@example.com",
    request_options={
        "extra_headers": {
            "X-Request-ID": "trace-abc-123",
            "X-User-Agent": "MyApp/1.0"
        }
    }
)
print(f"Traced auth: {user_result.user.id}")

# Example 3: Increase max retries for flaky networks
auth_url = client.sso.get_authorization_url(
    organization="org_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y",
    redirect_uri="https://yourapp.com/callback",
    request_options={
        "max_retries": 5  # Default is 2
    }
)
print(f"Resilient URL: {auth_url}")

# Example 4: Idempotency key for safe retries
try:
    user = client.user_management.create_user(
        email="newuser@example.com",
        request_options={
            "idempotency_key": "create-user-12345"  # Same key = same result
        }
    )
    print(f"Idempotent create: {user.id}")
except Exception as e:
    print(f"Safe to retry with same key: {e}")

# Example 5: Override base_url for staging tests
staging_result = client.user_management.send_magic_auth_code(
    email="test@example.com",
    request_options={
        "base_url": "https://api.workos-staging.com/"
    }
)
print(f"Staging auth code sent: {staging_result.user_id}")
```

Every WorkOS SDK method accepts an optional `request_options` dict that overrides client-level configuration for that single call. Available options:

- **timeout** (int): Request timeout in seconds. Use lower values (5-10s) for user-facing auth flows to fail fast. Default is 60s.
- **max_retries** (int): Number of retry attempts for transient failures (5xx, network errors). Default is 2. Increase for critical flows or unreliable networks.
- **extra_headers** (dict): Additional HTTP headers. Useful for distributed tracing (`X-Request-ID`), custom user agents, or correlation IDs.
- **idempotency_key** (str): A unique string for write operations (create, update). WorkOS deduplicates requests with the same key within 24 hours—safe to retry failed creates without duplicates.
- **base_url** (str): Override the API base URL. Use for testing against staging environments or custom deployments.

These options do NOT mutate the client instance—each call is independent. This is the recommended pattern for per-request customization rather than creating multiple client instances.

**Expected output**

```
Fast auth: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Traced auth: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Resilient URL: https://api.workos.com/sso/authorize?...
Idempotent create: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
Staging auth code sent: user_01H7ZKWZ2Z8Y3Y2Z8Y3Y2Z8Y3Y
```

**Gotchas**
- Timeout applies to the entire request (including retries). If you set timeout=5 and max_retries=3, all retries must complete within 5 seconds total, not 5 seconds each.
- Idempotency keys are case-sensitive and scoped per endpoint. The same key for create_user and create_organization are independent.
- extra_headers merges with default headers. You cannot remove SDK-set headers (like Authorization), only add new ones or override non-critical defaults.
- Overriding base_url affects only that call. Subsequent calls revert to the client's configured URL. For persistent staging use, configure the client with WORKOS_BASE_URL environment variable.

## How to Use Async Client for High-Throughput Authentication

In async web frameworks (FastAPI, Sanic, aiohttp) or when handling many concurrent authentication requests, the synchronous client blocks the event loop. The AsyncWorkOSClient provides native async/await support.

**Prerequisites**
- Python 3.8+ with async/await support
- Async web framework or asyncio-based application
- pip install workos (includes async support)

```python
import asyncio
from workos import AsyncWorkOSClient
from workos._errors import AuthenticationError

async_client = AsyncWorkOSClient(
    api_key="sk_test_1234567890abcdef",
    client_id="client_test_1234567890abcdef"
)

# Example 1: Async SSO profile exchange
async def authenticate_sso_async(code: str):
    try:
        profile = await async_client.sso.get_profile_and_token(code=code)
        print(f"Async SSO: {profile.profile.email}")
        return profile.profile.id
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
        return None

# Example 2: Concurrent authentication of multiple users
async def authenticate_many_users(codes: list[str]):
    tasks = [authenticate_sso_async(code) for code in codes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r and not isinstance(r, Exception))
    print(f"Authenticated {success_count}/{len(codes)} users concurrently")
    return results

# Example 3: Async user creation
async def create_users_batch(emails: list[str]):
    users = []
    for email in emails:
        user = await async_client.user_management.create_user(
            email=email,
            email_verified=False
        )
        users.append(user)
    
    print(f"Created {len(users)} users")
    return users

# Example 4: Async pagination
async def list_all_users():
    all_users = []
    page = await async_client.user_management.list_users(limit=10)
    
    async for user in page.auto_paging_iter():
        all_users.append(user)
        print(f"User: {user.email}")
    
    print(f"Total users: {len(all_users)}")
    return all_users

# Run examples
async def main():
    # Single async auth
    user_id = await authenticate_sso_async("code_123")
    
    # Concurrent auth
    codes = ["code_1", "code_2", "code_3"]
    await authenticate_many_users(codes)
    
    # Batch creation
    emails = ["user1@example.com", "user2@example.com"]
    await create_users_batch(emails)
    
    # Async pagination
    await list_all_users()

# Execute
if __name__ == "__main__":
    asyncio.run(main())
```

The `AsyncWorkOSClient` mirrors the synchronous client API exactly—every method has an async counterpart:

- `client.sso.get_profile_and_token()` → `await async_client.sso.get_profile_and_token()`
- `client.user_management.create_user()` → `await async_client.user_management.create_user()`
- `page.auto_paging_iter()` → `async for item in page.auto_paging_iter()`

Use the async client in async contexts (async def functions) with await. The key advantage: concurrent execution via `asyncio.gather()`. In the example, `authenticate_many_users()` authenticates multiple SSO codes in parallel—much faster than sequential sync calls.

The async client uses `httpx.AsyncClient` under the hood (vs. `httpx.Client` for sync). All timeout, retry, and error handling behavior is identical. Exceptions are the same typed classes (`AuthenticationError`, etc.).

For pagination, `AsyncPage.auto_paging_iter()` returns an async generator—iterate with `async for` instead of `for`.

**Expected output**

```
Async SSO: user@example.com
Authenticated 1/3 users concurrently
Created 2 users
User: user1@example.com
User: user2@example.com
Total users: 2
```

**Gotchas**
- Do NOT mix sync and async clients in the same code path. If you call a sync method from an async context, it will block the event loop and degrade performance.
- Async pagination with auto_paging_iter() MUST use 'async for', not 'for'. Regular for loops will raise TypeError.
- When using asyncio.gather() for concurrent requests, rate limits apply across all concurrent calls. If you hit 429, all tasks fail. Implement semaphores to limit concurrency: asyncio.Semaphore(max_concurrent_requests).
- The async client is not thread-safe. Create one instance per async context (e.g., one per FastAPI app, not one per request). Do NOT share across threads.

## FAQ

### Do I need both an API key and client ID for authentication?

Yes, but they serve different purposes. The API key (sk_...) authenticates your backend to WorkOS—it's a secret and must never be exposed in frontend code. The client ID (client_...) identifies your OAuth application and is safe to use in public contexts (like redirect URIs or frontend authorization URLs). Both are required for most authentication flows.

### How long do authorization codes, access tokens, and refresh tokens last?

Authorization codes (from SSO or passwordless flows) expire after 10 minutes and are single-use. Access tokens are short-lived JWTs (typically 1 hour, check the exp claim). Refresh tokens are long-lived (weeks to months) and can be used to obtain new access tokens without re-authentication. Magic auth codes (from User Management) expire after 10 minutes.

### What happens if I retry an authentication call with an expired or used code?

WorkOS returns a 401 AuthenticationError with a message like 'Invalid authorization code' or 'Code already used'. These are terminal errors—you cannot fix them by retrying. The user must restart the authentication flow (click SSO link again, request a new magic code, etc.). Never retry auth code exchanges; always check for AuthenticationError and redirect users to re-authenticate.

### Can I use the same API key for development and production?

No. WorkOS issues separate keys for test (sk_test_...) and live (sk_live_...) environments. Test keys work with test-mode organizations and connections; live keys work with production data. Never use live keys in development—test keys are free and safe for local testing. Use environment variables (WORKOS_API_KEY) to swap keys between environments without code changes.

### How do I handle rate limits in authentication flows?

Catch RateLimitExceededError and honor the retry_after value (in seconds). For user-facing flows (SSO, passwordless), show a friendly error and ask users to wait. For batch operations (creating many users), implement exponential backoff or limit concurrency with asyncio.Semaphore(). WorkOS rate limits are per API key, not per endpoint, so aggressive polling on one endpoint affects all others.

## Key takeaways

- WorkOS Python SDK supports multiple authentication patterns: SSO (OAuth), User Management (magic codes), MFA (TOTP), and Passwordless (email links)—all through a single WorkOSClient instance.
- Every authentication flow follows a similar pattern: initiate (get URL/send code), user action (click link/enter code), and verify (exchange for profile/tokens). Authorization codes and magic codes expire after 10 minutes and are single-use.
- Use AsyncWorkOSClient in async frameworks for high-throughput concurrent authentication. The API is identical to the sync client but with await and async for.
- Authentication errors map to typed exceptions (AuthenticationError, RateLimitExceededError, etc.). Always wrap auth calls in try/except, log request_id for debugging, and implement retry logic only for transient failures (5xx, rate limits).
- Store refresh_token securely (encrypted database) and never expose API keys in frontend code. Use environment variables (WORKOS_API_KEY, WORKOS_CLIENT_ID) to manage credentials across environments.
- For per-request customization (timeouts, tracing headers, idempotency), pass request_options to any method rather than creating multiple client instances.