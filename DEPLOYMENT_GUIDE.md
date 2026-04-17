# FairLens Deployment Guide

## 1. Permanent fixes applied (3 problems)

1. SPA refresh 404 on hosted frontend:
- Fixed with Vercel route fallback in frontend/vercel.json.

2. Production frontend calling localhost API:
- Fixed by removing hard localhost fallback in frontend/src/lib/api.ts.
- Frontend now uses VITE_API_URL, with `/api/v1` fallback for proxy-style deployments.

3. Large frontend chunk warning / poor caching:
- Fixed by adding manual vendor chunk splitting in frontend/vite.config.ts.

---

## 2. Vercel-ready frontend config

Files already added:
- frontend/vercel.json
- frontend/.env.example

### Vercel setup steps

1. Import the Git repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variable:
- `VITE_API_URL=https://YOUR_BACKEND_DOMAIN/api/v1`

### Why this works
- `routes` fallback ensures BrowserRouter routes load on refresh.
- frontend/src/lib/api.ts uses `VITE_API_URL` in production.

---

## 3. Backend deployment configs included

### Render (free tier path)
- Config file: render.yaml
- Includes:
  - Web service (FastAPI)
  - Worker service (Celery)
  - Redis service
  - Postgres database

Important environment values to set/update on Render:
- `GROQ_API_KEY` (secret)
- `CORS_ORIGINS` -> set to your Vercel domain(s)
- `ALLOWED_HOSTS` -> set backend host only
- `SECRET_KEY` -> keep generated strong value

---

## 4. Free backend platform suggestions

### 1) Render (recommended)
- Pros: Easiest for FastAPI + Celery + Redis + Postgres in one place.
- Free tier: available with service sleep limits.

### 2) Railway
- Pros: Very fast setup, good DX.
- Trade-off: free credits model may change by region/time.

### 3) Fly.io
- Pros: strong networking/runtime flexibility.
- Trade-off: slightly more infra setup work.

### 4) Koyeb
- Pros: straightforward container deploys.
- Trade-off: fewer integrated examples for Celery workers than Render.

---

## 5. Backend env checklist (production)

Required for production startup:
- `ENVIRONMENT=production`
- `SECRET_KEY=<strong-random>`
- `GROQ_API_KEY=<real-key>`
- `ALLOWED_HOSTS=["your-backend-domain"]`
- `CORS_ORIGINS=["https://your-frontend.vercel.app"]`

The app enforces these constraints at startup.

---

## 6. Google Auth Cloud Console

For local/dev/prod Google OAuth setup, use:
- CLOUD_CONSOLE_CONFIG.md

It includes exact origins, consent-screen settings, per-environment client IDs, and operational checks for all post-login pages.
