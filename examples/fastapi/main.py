from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from workos import WorkOSClient
from workos._errors import (
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
)
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WorkOS FastAPI Example")

# Initialize WorkOS client
client = WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID"),
)

REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8000/callback")


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "WorkOS FastAPI Example",
        "endpoints": {
            "/auth/sso": "Start SSO authentication flow",
            "/callback": "OAuth callback endpoint",
            "/organizations": "List organizations",
            "/organizations/{org_id}": "Get organization details",
            "/users": "List users",
            "/users/{user_id}": "Get user details",
        },
    }


@app.get("/auth/sso")
def initiate_sso(organization: str = None, connection: str = None, provider: str = None):
    """Initiate SSO authentication flow."""
    try:
        authorization_url = client.sso.get_authorization_url(
            organization=organization,
            connection=connection,
            provider=provider,
            redirect_uri=REDIRECT_URI,
        )
        return RedirectResponse(url=authorization_url)
    except (BadRequestError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@app.get("/callback")
def auth_callback(code: str):
    """Handle OAuth callback and exchange code for profile."""
    try:
        profile = client.sso.get_profile_and_token(code=code)
        return {
            "profile": {
                "id": profile.profile.id,
                "email": profile.profile.email,
                "first_name": profile.profile.first_name,
                "last_name": profile.profile.last_name,
                "connection_id": profile.profile.connection_id,
                "organization_id": profile.profile.organization_id,
            },
            "access_token": profile.access_token,
        }
    except (AuthenticationError, BadRequestError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@app.get("/organizations")
def list_organizations(limit: int = 10):
    """List all organizations with pagination."""
    try:
        page = client.organizations.list_organizations(limit=limit)
        organizations = [
            {
                "id": org.id,
                "name": org.name,
                "domains": org.domains,
                "created_at": org.created_at,
            }
            for org in page.data
        ]
        return {
            "data": organizations,
            "has_more": page.has_more(),
            "after": page.after,
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e.message))


@app.post("/organizations")
def create_organization(request: dict):
    """Create a new organization."""
    try:
        org = client.organizations.create_organization(
            name=request.get("name"),
            domains=request.get("domains", []),
        )
        return {
            "id": org.id,
            "name": org.name,
            "domains": org.domains,
            "created_at": org.created_at,
        }
    except (BadRequestError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@app.get("/organizations/{org_id}")
def get_organization(org_id: str):
    """Get organization details by ID."""
    try:
        org = client.organizations.get_organization(organization=org_id)
        return {
            "id": org.id,
            "name": org.name,
            "domains": org.domains,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e.message))


@app.get("/users")
def list_users(limit: int = 10, organization_id: str = None):
    """List users with optional organization filter."""
    try:
        page = client.user_management.list_users(
            limit=limit, organization_id=organization_id
        )
        users = [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at,
            }
            for user in page.data
        ]
        return {
            "data": users,
            "has_more": page.has_more(),
            "after": page.after,
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e.message))


@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get user details by ID."""
    try:
        user = client.user_management.get_user(user=user_id)
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": user.email_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e.message))


@app.get("/admin-portal")
def generate_admin_portal_link(organization: str, intent: str = None):
    """Generate an Admin Portal link for an organization."""
    try:
        portal_link = client.admin_portal.generate_link(
            organization=organization,
            intent=intent,
            return_url="http://localhost:8000",
        )
        return {"link": portal_link}
    except (BadRequestError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)