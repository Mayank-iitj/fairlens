# FairLens Backend

## Run locally

1. Create environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure environment variables:

```powershell
Copy-Item .env.example .env
```

Set secrets only in `.env` (never in `.env.example`).

```powershell
# Example: set Groq key in private env file
(Get-Content .env) -replace '^GROQ_API_KEY=.*$', 'GROQ_API_KEY=YOUR_REAL_KEY' | Set-Content .env
```

For deployment, keep `ENVIRONMENT=production`, use a strong `SECRET_KEY`, and set restrictive `ALLOWED_HOSTS`.

3. Run migrations:

```powershell
alembic upgrade head
```

4. Start API:

```powershell
uvicorn app.main:app --reload --port 8000
```

5. Start worker:

```powershell
celery -A app.tasks.celery_app.celery_app worker --loglevel=info -Q audits
```

## API

Primary routes are exposed under `/api/v1` and include auth, users, audits, datasets, explainability, AI helper endpoints, and monitoring schedules.

## Security Notes

- `.env` is treated as secret and should not be committed.
- Production startup fails fast if `SECRET_KEY` is default, `GROQ_API_KEY` is empty, or `ALLOWED_HOSTS` is wildcard.
- Docker compose files load `backend/.env` for secret values.
