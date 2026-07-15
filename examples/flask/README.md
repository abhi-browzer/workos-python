# WorkOS + Flask Example

A minimal Flask web application demonstrating WorkOS SSO authentication, organization management, and user listing.

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
   - `WORKOS_API_KEY`: Your WorkOS API key (starts with `sk_`)
   - `WORKOS_CLIENT_ID`: Your WorkOS client ID (starts with `client_`)
   - `FLASK_SECRET_KEY`: A random secret key for Flask sessions

   Get your API credentials from the [WorkOS Dashboard](https://dashboard.workos.com/).

3. **Run the application:**

   ```bash
   python app.py
   ```

   The app will start at `http://localhost:5000`

## What It Does

- **Home page (`/`)**: Lists all organizations and (if logged in) all users
- **Login (`/login`)**: Initiates SSO authentication flow via WorkOS
- **Callback (`/callback`)**: Handles SSO callback and creates a session
- **Logout (`/logout`)**: Clears the user session

The example demonstrates:
- Initializing the WorkOS client with environment variables
- SSO authentication with `get_authorization_url()` and `authenticate_with_code()`
- Organization listing with `list_organizations()`
- User retrieval with `get_user()` and `list_users()`
- Flask session management for authenticated users

## Production Notes

- Replace the generic `provider="authkit"` with your actual SSO connection or organization
- Set a strong `FLASK_SECRET_KEY` in production
- Enable HTTPS and configure proper redirect URIs in the WorkOS Dashboard
- Add error handling and logging appropriate for your environment
