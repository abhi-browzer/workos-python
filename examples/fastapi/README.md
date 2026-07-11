# WorkOS Python SDK + FastAPI Example

A minimal FastAPI application demonstrating WorkOS authentication, user management, and organization handling.

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**

Copy `.env.example` to `.env` and fill in your WorkOS credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- `WORKOS_API_KEY`: Your WorkOS API key from the [WorkOS Dashboard](https://dashboard.workos.com/api-keys)
- `WORKOS_CLIENT_ID`: Your WorkOS Client ID from the [WorkOS Dashboard](https://dashboard.workos.com/configuration)
- `WORKOS_REDIRECT_URI`: OAuth callback URL (default: `http://localhost:8000/callback`)

## Run

Start the FastAPI server:

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API docs are at `http://localhost:8000/docs`

## Available Endpoints

- `GET /` - API information and endpoint list
- `GET /auth/sso` - Initiate SSO authentication flow
- `GET /callback` - OAuth callback endpoint
- `GET /organizations` - List organizations
- `POST /organizations` - Create a new organization
- `GET /organizations/{org_id}` - Get organization details
- `GET /users` - List users
- `GET /users/{user_id}` - Get user details
- `GET /admin-portal` - Generate Admin Portal link

## Example Usage

### List Organizations

```bash
curl http://localhost:8000/organizations
```

### Create Organization

```bash
curl -X POST http://localhost:8000/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "domains": ["acme.com"]}'
```

### Initiate SSO

Navigate to:
```
http://localhost:8000/auth/sso?organization=org_123456
```

## Learn More

- [WorkOS Documentation](https://workos.com/docs)
- [WorkOS Python SDK](https://github.com/workos/workos-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)