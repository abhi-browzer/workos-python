# WorkOS Python + Next.js Example

A minimal example showing how to use the WorkOS Python SDK with Next.js API routes.

## Features

- User authentication via WorkOS AuthKit
- Organization listing
- User management operations
- Python-powered Next.js API routes

## Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- A WorkOS account with API credentials

### Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Node dependencies:

```bash
npm install
```

3. Configure environment variables:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your WorkOS credentials from the [WorkOS Dashboard](https://dashboard.workos.com).

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

## API Routes

- `GET /api/organizations` - List all organizations
- `POST /api/organizations` - Create a new organization
- `GET /api/users` - List users with pagination
- `GET /api/auth/url` - Get SSO authorization URL

## How It Works

Next.js API routes (`pages/api/*`) execute Python scripts that use the WorkOS SDK. The Python scripts output JSON, which Next.js serves to the frontend.
