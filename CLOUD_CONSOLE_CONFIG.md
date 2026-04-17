# FairLens Google Cloud Console Config

This file provides the exact Google Cloud OAuth setup for FairLens across local, dev, and production.
Domain target: fairlens.mayyanks.app

## 1. Prerequisites

- Frontend production URL: https://fairlens.mayyanks.app
- Frontend dev URL: https://dev.fairlens.mayyanks.app
- Backend production URL: https://api.fairlens.mayyanks.app
- Backend dev URL: https://api-dev.fairlens.mayyanks.app
- Local frontend URL: http://localhost:5174
- Local backend URL: http://localhost:8001

If your backend hostnames are different, update all env files accordingly.

## 2. OAuth Consent Screen

In Google Cloud Console:

1. APIs & Services > OAuth consent screen
2. App type: External
3. App name: FairLens
4. User support email: your support email
5. Developer contact email: your dev email
6. Authorized domains:
   - mayyanks.app
7. Scopes:
   - openid
   - email
   - profile
8. Test users:
   - add QA/admin users while in Testing mode

When ready for public users, submit for verification if required by your scope policy.

## 3. Create 3 OAuth Web Client IDs

Create one Web application client per environment under:
APIs & Services > Credentials > Create credentials > OAuth client ID

### 3.1 Local client

- Name: fairlens-web-local
- Authorized JavaScript origins:
  - http://localhost:5174
  - http://127.0.0.1:5174
- Authorized redirect URIs: leave empty for popup GIS flow

### 3.2 Dev client

- Name: fairlens-web-dev
- Authorized JavaScript origins:
  - https://dev.fairlens.mayyanks.app
- Authorized redirect URIs: leave empty for popup GIS flow

### 3.3 Production client

- Name: fairlens-web-prod
- Authorized JavaScript origins:
  - https://fairlens.mayyanks.app
  - https://www.fairlens.mayyanks.app
- Authorized redirect URIs: leave empty for popup GIS flow

## 4. Backend environment mapping

Use these templates:

- backend/.env.local.example
- backend/.env.dev.example
- backend/.env.prod.example

Set:

- GOOGLE_CLIENT_ID to the primary client id for that environment
- GOOGLE_CLIENT_IDS to a JSON list of valid client IDs accepted by backend

Recommended values:

- local backend:
  - GOOGLE_CLIENT_ID=<local-client-id>
  - GOOGLE_CLIENT_IDS=["<local-client-id>"]
- dev backend:
  - GOOGLE_CLIENT_ID=<dev-client-id>
  - GOOGLE_CLIENT_IDS=["<dev-client-id>"]
- prod backend:
  - GOOGLE_CLIENT_ID=<prod-client-id>
  - GOOGLE_CLIENT_IDS=["<prod-client-id>"]

For shared backend serving multiple frontends, include all allowed audiences in GOOGLE_CLIENT_IDS.

## 5. Frontend environment mapping

Use these templates:

- frontend/.env.local.example
- frontend/.env.dev.example
- frontend/.env.prod.example

Set VITE_GOOGLE_CLIENT_ID to the matching client ID for that frontend host.

## 6. CORS and host allowlist

Backend must allow frontend origins and backend hostnames.

Set in backend env:

- ALLOWED_HOSTS:
  - local: ["localhost","127.0.0.1"]
  - dev: ["api-dev.fairlens.mayyanks.app"]
  - prod: ["api.fairlens.mayyanks.app"]
- CORS_ORIGINS:
  - local: ["http://localhost:5174","http://127.0.0.1:5174"]
  - dev: ["https://dev.fairlens.mayyanks.app"]
  - prod: ["https://fairlens.mayyanks.app","https://www.fairlens.mayyanks.app"]

## 7. Operational checks (must pass)

Run after deploy:

1. Open /login on each environment.
2. Confirm Google button renders.
3. Sign in with a Google account.
4. Confirm backend /api/v1/auth/google returns token pair.
5. Confirm app redirects to /dashboard.
6. Navigate all post-login routes:
   - /dashboard
   - /audit/new
   - /audit/:id
   - /reports
   - /monitor
   - /settings
7. Hard-refresh each route and ensure hosting fallback still serves SPA.
8. Confirm /api/v1/auth/login and /api/v1/auth/register return 403.

## 8. Required DNS/HTTPS

Ensure TLS and DNS are active for:

- fairlens.mayyanks.app
- www.fairlens.mayyanks.app
- dev.fairlens.mayyanks.app
- api.fairlens.mayyanks.app
- api-dev.fairlens.mayyanks.app

Google OAuth web origins require exact scheme and host.

## 9. Current auth mode

This codebase is configured for Google-only auth.
Password login/register endpoints are intentionally disabled.
