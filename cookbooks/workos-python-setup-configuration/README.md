The WorkOS Python SDK provides programmatic access to WorkOS APIs for authentication, user management, directory sync, and authorization. This cookbook covers everything you need to install the SDK, configure credentials, initialize clients (both sync and async), customize request behavior, and handle common setup scenarios.

Whether you're integrating Single Sign-On, AuthKit, or Fine-Grained Authorization, proper SDK setup is the foundation. We'll walk through installation, credential management via environment variables or direct instantiation, timeout configuration, custom base URLs for staging environments, and the error handling patterns you'll rely on throughout your integration.

## How to Install the WorkOS Python SDK

You need to add the WorkOS SDK to your Python project to access WorkOS APIs for authentication, user management, or authorization features.

**Prerequisites**
- Python 3.7 or higher installed
- pip package manager available

```bash
# Install the latest stable version
pip install workos

# Or install a specific version to pin your dependency
pip install workos==5.0.0

# For projects using requirements.txt
echo "workos>=5.0.0" >> requirements.txt
pip install -r requirements.txt

# For projects using Poetry
poetry add workos

# For projects using Pipenv
pipenv install workos
```

The WorkOS Python SDK is distributed via PyPI as the `workos` package. The standard `pip install workos` command fetches the latest stable release along with its dependencies: `cryptography`, `httpx`, `pyjwt`, and `typing_extensions`.

For production applications, we recommend pinning to a specific version (e.g., `workos==5.0.0`) to prevent unexpected breaking changes during dependency updates. WorkOS follows semantic versioning, so minor and patch releases are backward-compatible.

The SDK ships with full type annotations (`py.typed` marker) and works out of the box with mypy, pyright, and IDE autocomplete. All models are dataclasses with slots enabled for memory efficiency.

**Expected output**

```
Successfully installed workos-5.0.0
Successfully installed cryptography-41.0.0 httpx-0.25.0 pyjwt-2.8.0 typing-extensions-4.8.0

(Exact dependency versions may vary based on your environment)
```

**Gotchas**
- The SDK requires Python 3.7+. If you're on Python 3.6 or earlier, you'll need to upgrade your runtime.
- If you see SSL certificate errors on older systems, ensure your `cryptography` package is up to date: `pip install --upgrade cryptography`.
- Beta releases are available for testing pre-GA features but may have breaking changes between versions. Pin the exact beta version if using: `pip install workos==5.1.0b1`.

## How to Initialize the WorkOS Client with API Credentials

After installing the SDK, you need to create a client instance with your WorkOS API key and client ID to make authenticated requests.

**Prerequisites**
- WorkOS SDK installed via pip
- WorkOS API key from your dashboard (starts with sk_)
- WorkOS client ID from your dashboard (starts with client_)

```python
from workos import WorkClient

# Direct credential initialization
client = WorkClient(
    api_key="sk_example_1234567890abcdef",
    client_id="client_example_1234567890abcdef"
)

# Verify the client is configured correctly
print(f"Client initialized: {client}")

# Make a test API call to list organizations
try:
    page = client.organizations.list_organizations(limit=5)
    print(f"Found {len(page.data)} organizations")
    for org in page.data:
        print(f"  - {org.name} (ID: {org.id})")
except Exception as e:
    print(f"API call failed: {e}")
```

The `WorkClient` is your main entry point to the SDK. It requires two credentials:

- **api_key**: Your secret API key from the WorkOS dashboard, used to authenticate all API requests. This always starts with `sk_` for production keys or `sk_test_` for test mode.
- **client_id**: Your application's client identifier, required for OAuth flows and some user management operations. This starts with `client_` or `client_test_`.

Passing credentials directly to the constructor is the most explicit approach and works well for quick scripts or when credentials come from a secrets manager. The client instance is thread-safe and should typically be created once at application startup and reused.

The client exposes all WorkOS resources as properties: `client.sso`, `client.organizations`, `client.user_management`, `client.directory_sync`, `client.audit_logs`, `client.authorization`, and more. Each property provides strongly-typed methods for that resource.

**Expected output**

```
Client initialized: <WorkClient api_key=sk_exa...def client_id=client_exa...def>
Found 3 organizations
  - Acme Corp (ID: org_01H1234567890ABCDEFGHJKMNP)
  - Example Inc (ID: org_01H9876543210ZYXWVUTSRQPON)
  - Demo LLC (ID: org_01HABCDEFGHIJKLMNOPQRSTUVW)
```

**Gotchas**
- Never hardcode production API keys in source code. This example shows the pattern; in production, load from environment variables or a secrets manager.
- Using a test mode key (`sk_test_*`) will only access test mode data. Ensure you're using the correct key for your environment.
- The client constructor validates that api_key and client_id are provided but does NOT make a network request. Authentication errors surface when you make your first API call.

## How to Configure the Client with Environment Variables

You want to keep credentials out of your code and configure the WorkOS client via environment variables for easier deployment across environments.

**Prerequisites**
- WorkOS SDK installed
- Environment variables set in your shell or deployment platform

```python
import os
from workos import WorkClient

# Set environment variables (typically done outside the application)
# export WORKOS_API_KEY="sk_example_1234567890abcdef"
# export WORKOS_CLIENT_ID="client_example_1234567890abcdef"

# The client automatically reads from environment variables
client = WorkClient()

# You can verify which credentials are being used
print(f"Using API key: {os.getenv('WORKOS_API_KEY', 'not set')[:10]}...")
print(f"Using client ID: {os.getenv('WORKOS_CLIENT_ID', 'not set')[:15]}...")

# Make an API call to confirm credentials work
try:
    page = client.organizations.list_organizations(limit=1)
    print(f"✓ Client configured correctly, found {len(page.data)} organization(s)")
except Exception as e:
    print(f"✗ Configuration error: {e}")

# Optional: Override specific environment variables
client_with_override = WorkClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID"),
    # Custom timeout from environment or default to 30 seconds
    request_timeout=int(os.getenv("WORKOS_REQUEST_TIMEOUT", "30"))
)
print(f"Client timeout: {client_with_override._request_timeout}s")
```

The WorkOS client reads credentials from environment variables when not passed explicitly:

- `WORKOS_API_KEY`: Your secret API key
- `WORKOS_CLIENT_ID`: Your application's client ID
- `WORKOS_BASE_URL`: Override the API endpoint (defaults to `https://api.workos.com/`)
- `WORKOS_REQUEST_TIMEOUT`: HTTP timeout in seconds (defaults to 60)

This pattern keeps secrets out of version control and makes it easy to use different credentials across development, staging, and production. In containerized environments like Docker or Kubernetes, these are typically injected at runtime via platform secrets management.

Calling `WorkClient()` with no arguments will raise an error if the required environment variables aren't set, giving you immediate feedback about missing configuration. You can mix explicit parameters with environment variables — explicit arguments always take precedence.

**Expected output**

```
Using API key: sk_example...
Using client ID: client_example...
✓ Client configured correctly, found 1 organization(s)
Client timeout: 30s
```

**Gotchas**
- If WORKOS_API_KEY or WORKOS_CLIENT_ID are not set and you don't pass them explicitly, the client constructor will raise a configuration error immediately.
- Environment variable names are case-sensitive. Use all caps: WORKOS_API_KEY, not workos_api_key.
- When deploying to platforms like Heroku, Vercel, or AWS Lambda, set these as platform environment variables or secrets, not in .env files that might be committed to git.
- The WORKOS_REQUEST_TIMEOUT must be an integer. If you set it to a non-numeric value, you'll get a ValueError when the client initializes.

## How to Use the Async Client for Concurrent Operations

Your application uses async/await patterns (FastAPI, aiohttp, asyncio), and you need a non-blocking WorkOS client to avoid blocking the event loop.

**Prerequisites**
- WorkOS SDK installed
- Python 3.7+ with asyncio support
- Async runtime (e.g., asyncio.run, uvicorn, or FastAPI)

```python
import asyncio
from workos import AsyncWorkOSClient

# Initialize the async client (same credential options as sync client)
async_client = AsyncWorkOSClient(
    api_key="sk_example_1234567890abcdef",
    client_id="client_example_1234567890abcdef"
)

async def fetch_organizations():
    """Fetch and display organizations using the async client."""
    print("Fetching organizations asynchronously...")
    
    # All methods are awaitable
    page = await async_client.organizations.list_organizations(limit=5)
    
    print(f"Found {len(page.data)} organizations:")
    for org in page.data:
        print(f"  - {org.name} (ID: {org.id})")
    
    # Auto-pagination with async iteration
    print("\nIterating all organizations with auto-pagination:")
    count = 0
    async for org in page.auto_paging_iter():
        print(f"  {count + 1}. {org.name}")
        count += 1
        if count >= 10:  # Limit for demo purposes
            break
    
    return count

async def concurrent_operations():
    """Demonstrate concurrent API calls."""
    print("\nMaking concurrent API calls...")
    
    # Fire off multiple requests concurrently
    results = await asyncio.gather(
        async_client.organizations.list_organizations(limit=1),
        async_client.user_management.list_users(limit=1),
        return_exceptions=True  # Don't fail all if one fails
    )
    
    print(f"Completed {len(results)} concurrent requests")
    return results

# Run the async functions
if __name__ == "__main__":
    asyncio.run(fetch_organizations())
    asyncio.run(concurrent_operations())
```

`AsyncWorkOSClient` provides the exact same API surface as `WorkOSClient`, but every method returns an awaitable coroutine instead of blocking. This is critical for async web frameworks like FastAPI, aiohttp, or Starlette, where blocking the event loop degrades performance.

The async client uses `httpx`'s async transport under the hood. All pagination helpers work identically: `page.auto_paging_iter()` becomes an async iterator you use with `async for`. The client handles connection pooling and keep-alive automatically.

Credentials and configuration work identically to the sync client — you can pass them explicitly or use environment variables. The async client is also thread-safe and should be instantiated once and reused across requests (e.g., stored as an app-level dependency in FastAPI).

Using `asyncio.gather()` lets you fire multiple WorkOS API calls concurrently, which can significantly reduce latency when you need data from multiple endpoints.

**Expected output**

```
Fetching organizations asynchronously...
Found 5 organizations:
  - Acme Corp (ID: org_01H1234567890ABCDEFGHJKMNP)
  - Example Inc (ID: org_01H9876543210ZYXWVUTSRQPON)
  - Demo LLC (ID: org_01HABCDEFGHIJKLMNOPQRSTUVW)
  - Test Co (ID: org_01HXYZABCDEFGHIJKLMNOPQRST)
  - Beta Industries (ID: org_01H56789ABCDEFGHIJKLMNOPQ)

Iterating all organizations with auto-pagination:
  1. Acme Corp
  2. Example Inc
  3. Demo LLC
  4. Test Co
  5. Beta Industries
  6. Alpha Systems
  7. Gamma Tech
  8. Delta Solutions
  9. Epsilon Group
  10. Zeta Ventures

Making concurrent API calls...
Completed 2 concurrent requests
```

**Gotchas**
- Never use WorkOSClient (sync) in an async function — it will block the event loop. Always use AsyncWorkOSClient in async contexts.
- Don't forget to await every method call. Forgetting await will return a coroutine object instead of the result, which will cause runtime errors.
- If you're using FastAPI or similar frameworks, create the AsyncWorkOSClient once at startup and inject it as a dependency rather than creating new instances per request.
- The async client maintains its own connection pool. Creating many client instances can exhaust file descriptors. Reuse a single instance.

## How to Customize Request Behavior with Per-Request Options

You need to override timeout, retry behavior, add custom headers, or use a different base URL for specific API calls without changing the global client configuration.

**Prerequisites**
- WorkOS SDK installed and client initialized

```python
from workos import WorkClient

client = WorkClient(
    api_key="sk_example_1234567890abcdef",
    client_id="client_example_1234567890abcdef"
)

# Example 1: Custom timeout for a slow operation
print("Example 1: Custom timeout")
try:
    page = client.organizations.list_organizations(
        request_options={
            "timeout": 10,  # 10-second timeout instead of default 60
        }
    )
    print(f"✓ Fetched {len(page.data)} orgs with 10s timeout")
except Exception as e:
    print(f"✗ Request failed: {e}")

# Example 2: Increased retries for flaky network
print("\nExample 2: Increased retries")
page = client.organizations.list_organizations(
    request_options={
        "max_retries": 5,  # Retry up to 5 times on transient failures
    }
)
print(f"✓ Fetched with max_retries=5")

# Example 3: Custom headers (e.g., for request tracking)
print("\nExample 3: Custom headers")
page = client.organizations.list_organizations(
    request_options={
        "extra_headers": {
            "X-Request-ID": "my-custom-trace-id-12345",
            "X-Client-Version": "1.0.0",
        },
    }
)
print(f"✓ Request sent with custom headers")

# Example 4: Idempotency key for safe retries on mutations
print("\nExample 4: Idempotency key")
import uuid
idempotency_key = str(uuid.uuid4())

org = client.organizations.create_organization(
    name="Test Organization",
    request_options={
        "idempotency_key": idempotency_key,
    }
)
print(f"✓ Created org {org.id} with idempotency key {idempotency_key}")

# Example 5: Override base URL for staging environment
print("\nExample 5: Staging environment")
staging_page = client.organizations.list_organizations(
    request_options={
        "base_url": "https://staging-api.workos.com/",
    }
)
print(f"✓ Fetched from staging: {len(staging_page.data)} orgs")

# Example 6: Combine multiple options
print("\nExample 6: Combined options")
page = client.organizations.list_organizations(
    request_options={
        "timeout": 5,
        "max_retries": 3,
        "extra_headers": {"X-Environment": "production"},
    }
)
print(f"✓ Request with timeout=5, retries=3, and custom header")
```

Every SDK method accepts an optional `request_options` dictionary that overrides client-level configuration for that single request. This is useful when different operations have different requirements:

- **timeout**: HTTP timeout in seconds. Useful for operations that might take longer (large exports) or should fail fast (health checks).
- **max_retries**: How many times to retry on transient failures (network errors, 5xx responses). Default is typically 2.
- **extra_headers**: Dictionary of additional HTTP headers to send with the request. Useful for tracing, client versioning, or custom middleware.
- **idempotency_key**: A unique string to safely retry mutation operations. If a request fails and is retried with the same key, WorkOS ensures the operation only happens once.
- **base_url**: Override the API endpoint. Useful for testing against staging environments or for on-premise deployments.

These options don't modify the client instance — they only affect the single request. You can combine multiple options in the same call. The SDK handles serialization, authentication, and error handling consistently regardless of which options you use.

Idempotency keys are particularly important for `create_*` operations in production. If your application crashes after sending a request but before receiving the response, you can safely retry with the same key without creating duplicates.

**Expected output**

```
Example 1: Custom timeout
✓ Fetched 5 orgs with 10s timeout

Example 2: Increased retries
✓ Fetched with max_retries=5

Example 3: Custom headers
✓ Request sent with custom headers

Example 4: Idempotency key
✓ Created org org_01HABCDEFGHIJKLMNOPQRSTUVW with idempotency key 550e8400-e29b-41d4-a716-446655440000

Example 5: Staging environment
✓ Fetched from staging: 2 orgs

Example 6: Combined options
✓ Request with timeout=5, retries=3, and custom header
```

**Gotchas**
- Timeout values must be integers (seconds). Non-numeric values will raise a TypeError.
- Idempotency keys should be unique per operation, not per request. Use the same key when retrying a failed request, but generate a new key for each distinct operation.
- If you override base_url to point to a non-WorkOS endpoint, authentication and request formats may not work. This option is meant for staging/testing environments running WorkOS-compatible APIs.
- Extra headers are merged with default headers. If you specify a header that the SDK sets automatically (like Authorization), your value will be ignored to prevent authentication bypass.
- Setting max_retries too high can cause long delays on persistent failures. Use exponential backoff defaults by setting a reasonable retry count (2-5).

## How to Handle SDK Errors and Extract Error Details

API calls can fail for various reasons (invalid credentials, resource not found, rate limits), and you need to catch, identify, and respond to specific error types.

**Prerequisites**
- WorkOS SDK installed and client initialized

```python
from workos import WorkClient
from workos._errors import (
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    RateLimitExceededError,
    ServerError,
)
import time

client = WorkClient(
    api_key="sk_example_1234567890abcdef",
    client_id="client_example_1234567890abcdef"
)

# Example 1: Catch specific error types
print("Example 1: Not found error")
try:
    org = client.organizations.get_organization("org_nonexistent12345")
except NotFoundError as e:
    print(f"✗ Organization not found")
    print(f"  Message: {e.message}")
    print(f"  Request ID: {e.request_id}")
    print(f"  Status: {e.status_code}")

# Example 2: Authentication failure
print("\nExample 2: Authentication error")
invalid_client = WorkClient(api_key="sk_invalid", client_id="client_test_123")
try:
    invalid_client.organizations.list_organizations()
except AuthenticationError as e:
    print(f"✗ Authentication failed: {e.message}")
    print(f"  Check your API key is correct and not expired")

# Example 3: Rate limit handling with retry
print("\nExample 3: Rate limit handling")
try:
    # Simulate hitting rate limit
    for i in range(100):
        client.organizations.list_organizations(limit=1)
except RateLimitExceededError as e:
    print(f"✗ Rate limited: {e.message}")
    print(f"  Retry after: {e.retry_after} seconds")
    if e.retry_after:
        print(f"  Waiting {e.retry_after}s before retrying...")
        # time.sleep(e.retry_after)  # Uncomment to actually wait
        # client.organizations.list_organizations(limit=1)

# Example 4: Validation errors
print("\nExample 4: Validation error")
try:
    # Try to create an org with invalid data
    client.organizations.create_organization(
        name="",  # Empty name should fail validation
    )
except (BadRequestError, UnprocessableEntityError) as e:
    print(f"✗ Validation failed: {e.message}")
    print(f"  Fix the request data and try again")

# Example 5: Generic error handling pattern
print("\nExample 5: Generic error handling")
def safe_get_organization(org_id: str):
    """Safely fetch an organization with comprehensive error handling."""
    try:
        return client.organizations.get_organization(org_id)
    except NotFoundError:
        print(f"Organization {org_id} does not exist")
        return None
    except AuthenticationError:
        print("Authentication failed - check API credentials")
        raise  # Re-raise auth errors
    except RateLimitExceededError as e:
        print(f"Rate limited - retry after {e.retry_after}s")
        raise  # Let caller handle rate limits
    except ServerError as e:
        print(f"WorkOS server error: {e.message} (request: {e.request_id})")
        return None  # Treat server errors as temporary
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

result = safe_get_organization("org_01H1234567890ABCDEFGHJKMNP")
if result:
    print(f"✓ Found organization: {result.name}")
else:
    print("Organization not retrieved")
```

The WorkOS SDK maps HTTP error responses to typed exception classes, all inheriting from a base `WorkOSError`. This lets you catch specific failure modes and handle them appropriately:

- **BadRequestError (400)**: Malformed request, missing required parameters
- **AuthenticationError (401)**: Invalid or missing API key
- **AuthorizationError (403)**: Valid API key but insufficient permissions
- **NotFoundError (404)**: Resource doesn't exist
- **ConflictError (409)**: Resource already exists or state conflict
- **UnprocessableEntityError (422)**: Request is well-formed but semantically invalid
- **RateLimitExceededError (429)**: Too many requests, includes `retry_after` seconds
- **ServerError (5xx)**: WorkOS internal error, usually transient

All exceptions expose:
- `message`: Human-readable error description
- `status_code`: HTTP status code
- `request_id`: Unique ID for this request (include this when contacting support)
- `retry_after`: (On RateLimitExceededError) Seconds to wait before retrying

For production applications, catch specific errors you can recover from (NotFoundError, RateLimitExceededError) and let others bubble up to your error tracking system. Always log the `request_id` for debugging — WorkOS support can look up the full request details with this ID.

**Expected output**

```
Example 1: Not found error
✗ Organization not found
  Message: Organization not found
  Request ID: req_01H5TZKQX9J8GYBXNHQE4PQVM7
  Status: 404

Example 2: Authentication error
✗ Authentication failed: Invalid API key
  Check your API key is correct and not expired

Example 3: Rate limit handling
✗ Rate limited: Rate limit exceeded
  Retry after: 60 seconds
  Waiting 60s before retrying...

Example 4: Validation error
✗ Validation failed: Organization name cannot be empty
  Fix the request data and try again

Example 5: Generic error handling
✓ Found organization: Acme Corp
```

**Gotchas**
- Don't catch the base Exception for WorkOS calls in production — you'll mask bugs. Catch specific WorkOSError subclasses you know how to handle.
- RateLimitExceededError includes a retry_after hint, but the SDK does NOT automatically retry rate-limited requests. You must implement retry logic yourself or use request_options max_retries.
- request_id is critical for debugging. Always log it when errors occur. Without it, WorkOS support cannot help troubleshoot issues.
- ServerError (5xx) usually indicates a transient WorkOS issue. Implement exponential backoff retry for these, but don't retry indefinitely.
- Authentication and Authorization errors are not retryable — they indicate configuration problems. Log these at ERROR level and alert your team.

## How to Configure Multiple Client Instances for Different Environments

You need separate WorkOS clients for test and production environments, or for different WorkOS projects, each with their own credentials and configuration.

**Prerequisites**
- WorkOS SDK installed
- Multiple sets of credentials (test and production)

```python
from workos import WorkClient, AsyncWorkOSClient
import os

# Production client with explicit credentials
production_client = WorkClient(
    api_key=os.getenv("WORKOS_PROD_API_KEY", "sk_prod_1234567890abcdef"),
    client_id=os.getenv("WORKOS_PROD_CLIENT_ID", "client_prod_1234567890abcdef"),
    request_timeout=30,  # Tighter timeout for production
)
print(f"Production client initialized")

# Test/staging client with different credentials
test_client = WorkClient(
    api_key=os.getenv("WORKOS_TEST_API_KEY", "sk_test_1234567890abcdef"),
    client_id=os.getenv("WORKOS_TEST_CLIENT_ID", "client_test_1234567890abcdef"),
    request_timeout=60,  # Longer timeout for test environment
)
print(f"Test client initialized")

# Development client pointing to staging API
dev_client = WorkClient(
    api_key=os.getenv("WORKOS_DEV_API_KEY", "sk_dev_1234567890abcdef"),
    client_id=os.getenv("WORKOS_DEV_CLIENT_ID", "client_dev_1234567890abcdef"),
)
print(f"Dev client initialized")

# Async client for a specific microservice
service_async_client = AsyncWorkOSClient(
    api_key=os.getenv("WORKOS_SERVICE_API_KEY", "sk_service_1234567890abcdef"),
    client_id=os.getenv("WORKOS_SERVICE_CLIENT_ID", "client_service_1234567890abcdef"),
    request_timeout=15,  # Fast timeout for internal service calls
)
print(f"Service async client initialized")

# Helper to get the right client based on environment
def get_workos_client(environment: str = None) -> WorkClient:
    """Factory function to get the appropriate WorkOS client."""
    if environment is None:
        environment = os.getenv("APP_ENV", "development")
    
    clients = {
        "production": production_client,
        "staging": test_client,
        "development": dev_client,
    }
    
    client = clients.get(environment)
    if not client:
        raise ValueError(f"Unknown environment: {environment}")
    
    return client

# Usage examples
print("\nUsing clients:")

# Use production client
try:
    prod_orgs = production_client.organizations.list_organizations(limit=1)
    print(f"✓ Production: {len(prod_orgs.data)} organizations")
except Exception as e:
    print(f"✗ Production client error: {e}")

# Use test client
try:
    test_orgs = test_client.organizations.list_organizations(limit=1)
    print(f"✓ Test: {len(test_orgs.data)} organizations")
except Exception as e:
    print(f"✗ Test client error: {e}")

# Use factory function
current_client = get_workos_client()  # Uses APP_ENV or defaults to dev
print(f"✓ Current environment client: {current_client}")

# Clean separation for testing
class WorkOSService:
    """Example service class with injectable client."""
    
    def __init__(self, client: WorkClient = None):
        self.client = client or get_workos_client()
    
    def get_organization_count(self) -> int:
        page = self.client.organizations.list_organizations(limit=1)
        return len(page.data)

# In production code
service = WorkOSService(client=production_client)
print(f"\n✓ Service initialized with production client")

# In tests, inject a test client
test_service = WorkOSService(client=test_client)
print(f"✓ Test service initialized with test client")
```

Managing multiple WorkOS clients is common in real applications:

- **Environment separation**: Different credentials for dev, staging, and production
- **Multi-project setups**: One application integrating with multiple WorkOS projects
- **Testing**: Inject test clients with mocked credentials for unit tests
- **Microservices**: Each service might use different WorkOS credentials or configurations

Each `WorkOSClient` instance is independent and immutable after construction. Create them once at application startup and reuse them. Thread-safe, so you can safely use a single instance across multiple threads or requests.

The factory pattern shown (`get_workos_client()`) is useful for selecting the right client based on an environment variable. This keeps your business logic environment-agnostic — you write `get_workos_client()` everywhere and control the environment via configuration.

For dependency injection frameworks (like FastAPI's `Depends`), create a module-level client instance and inject it into route handlers. This ensures a single client per environment and makes testing easy — just override the dependency with a test client.

Never share clients across environments (e.g., using a prod API key in dev). The SDK doesn't prevent this, so you must organize your configuration carefully. Environment-specific prefixes like `WORKOS_PROD_API_KEY` help avoid accidental credential mixing.

**Expected output**

```
Production client initialized
Test client initialized
Dev client initialized
Service async client initialized

Using clients:
✓ Production: 1 organizations
✓ Test: 1 organizations
✓ Current environment client: <WorkClient api_key=sk_dev...def client_id=client_dev...def>

✓ Service initialized with production client
✓ Test service initialized with test client
```

**Gotchas**
- Each client maintains its own HTTP connection pool. Creating dozens of clients can exhaust file descriptors. Reuse clients where possible.
- If you mix up API keys (use a prod key with a test client_id), you'll get authentication or authorization errors. Always use matching pairs.
- In serverless environments (AWS Lambda, Cloud Functions), create clients outside the handler function to reuse connections across invocations.
- When using async clients, ensure you're running in an async context. You cannot use AsyncWorkOSClient methods in synchronous code without await.
- Test clients should use test mode credentials (sk_test_*, client_test_*). Using production credentials in tests can create real data, charges, or security issues.

## FAQ

### What Python versions does the WorkOS SDK support?

The SDK requires Python 3.7 or higher. We test against Python 3.7, 3.8, 3.9, 3.10, 3.11, and 3.12. If you're on Python 3.6 or earlier, you'll need to upgrade your runtime before installing the SDK.

### Should I use environment variables or pass credentials directly?

Use environment variables (WORKOS_API_KEY, WORKOS_CLIENT_ID) for production deployments. This keeps secrets out of code and version control. Pass credentials directly only for quick scripts, local development, or when loading from a secrets manager. The client reads from environment variables automatically if you don't pass them explicitly.

### When should I use AsyncWorkOSClient instead of WorkClient?

Use AsyncWorkOSClient when your application is built on async frameworks like FastAPI, aiohttp, or Starlette. The async client prevents blocking the event loop during API calls, which is critical for performance in async applications. If you're using Flask, Django (non-async), or standard synchronous code, use the regular WorkClient.

### How do I handle rate limits in production?

Catch RateLimitExceededError and check the retry_after property to see how many seconds to wait. Implement exponential backoff for automatic retries, or use the request_options max_retries parameter for simpler cases. For high-volume applications, implement request queuing or use per-endpoint rate tracking to stay under limits proactively.

### Can I use multiple WorkOS clients in the same application?

Yes. Each WorkClient instance is independent and can have different credentials, timeouts, or configurations. This is useful for multi-tenant applications, environment separation (dev/staging/prod), or integrating with multiple WorkOS projects. Just create separate client instances with the appropriate credentials and use them where needed.

## Key takeaways

- Install the SDK with `pip install workos` and initialize WorkClient with your API key and client ID — credentials can be passed explicitly or via WORKOS_API_KEY and WORKOS_CLIENT_ID environment variables.
- Use AsyncWorkOSClient for async frameworks (FastAPI, aiohttp) to avoid blocking the event loop; the async API is identical to the sync client except every method must be awaited.
- Override timeout, retries, headers, or base URL per-request using the request_options parameter without modifying the global client configuration.
- All API errors map to typed exceptions (NotFoundError, RateLimitExceededError, etc.) with message, status_code, and request_id properties — always log request_id for debugging.
- Create one client instance at startup and reuse it across requests (thread-safe) rather than instantiating new clients repeatedly, which wastes connections.
- For multiple environments, create separate client instances with environment-specific credentials and use a factory function or dependency injection to select the right client at runtime.