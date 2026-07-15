import os
from flask import Flask, redirect, request, session, url_for, render_template_string
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize WorkOS client (reads WORKOS_API_KEY and WORKOS_CLIENT_ID from environment)
client = WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID")
)

HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WorkOS Flask Example</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 0 20px; }
        .user-info { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .actions { margin: 20px 0; }
        .actions a { display: inline-block; margin: 5px 10px 5px 0; padding: 10px 15px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; }
        .actions a:hover { background: #0052a3; }
        .orgs, .users { margin: 20px 0; }
        .org-item, .user-item { padding: 10px; border-bottom: 1px solid #ddd; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
    </style>
</head>
<body>
    <h1>WorkOS + Flask Example</h1>
    
    {% if user %}
        <div class="user-info">
            <h3>Logged in as:</h3>
            <p><strong>Email:</strong> {{ user.email }}</p>
            <p><strong>User ID:</strong> {{ user.id }}</p>
            <p><strong>First Name:</strong> {{ user.first_name or 'N/A' }}</p>
            <p><strong>Last Name:</strong> {{ user.last_name or 'N/A' }}</p>
        </div>
        <div class="actions">
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
    {% else %}
        <p>Welcome! Please log in with SSO to continue.</p>
        <div class="actions">
            <a href="{{ url_for('login') }}">Login with SSO</a>
        </div>
    {% endif %}
    
    <h2>Organizations</h2>
    <div class="orgs">
        {% if organizations %}
            {% for org in organizations %}
                <div class="org-item">
                    <strong>{{ org.name }}</strong> ({{ org.id }})
                    {% if org.domains %}
                        <br><small>Domains: {{ org.domains | join(', ') }}</small>
                    {% endif %}
                </div>
            {% endfor %}
        {% else %}
            <p>No organizations found.</p>
        {% endif %}
    </div>
    
    {% if user %}
        <h2>Users</h2>
        <div class="users">
            {% if users %}
                {% for u in users %}
                    <div class="user-item">
                        <strong>{{ u.email }}</strong> ({{ u.id }})
                        {% if u.first_name or u.last_name %}
                            <br><small>{{ u.first_name }} {{ u.last_name }}</small>
                        {% endif %}
                    </div>
                {% endfor %}
            {% else %}
                <p>No users found.</p>
            {% endif %}
        </div>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    """Home page showing user info, organizations, and users."""
    user = None
    users = []
    
    # Check if user is logged in
    if "user_id" in session:
        try:
            user = client.user_management.get_user(session["user_id"])
            # List users (first 10 for demo)
            page = client.user_management.list_users(limit=10)
            users = page.data
        except Exception as e:
            print(f"Error fetching user data: {e}")
            session.clear()
    
    # List organizations (first 10 for demo)
    organizations = []
    try:
        page = client.organizations.list_organizations(limit=10)
        organizations = page.data
    except Exception as e:
        print(f"Error fetching organizations: {e}")
    
    return render_template_string(
        HOME_TEMPLATE,
        user=user,
        users=users,
        organizations=organizations
    )

@app.route("/login")
def login():
    """Initiate SSO authentication."""
    # For demo purposes, we'll use a generic OAuth provider
    # In production, you'd typically select a specific organization or connection
    authorization_url = client.sso.get_authorization_url(
        provider="authkit",
        redirect_uri=url_for("callback", _external=True),
        state="custom_state_value"
    )
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    """Handle SSO callback and authenticate user."""
    code = request.args.get("code")
    
    if not code:
        return "Error: No authorization code received", 400
    
    try:
        # Authenticate with the authorization code
        response = client.user_management.authenticate_with_code(
            code=code,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        # Store user ID in session
        session["user_id"] = response.user.id
        
        return redirect(url_for("index"))
    except Exception as e:
        return f"Authentication error: {str(e)}", 400

@app.route("/logout")
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
