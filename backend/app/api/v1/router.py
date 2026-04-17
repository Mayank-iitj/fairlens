from fastapi import APIRouter

from app.api.v1 import ai, audits, auth, datasets, explain, monitors, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(explain.router, prefix="/explain", tags=["explain"])
api_router.include_router(monitors.router, prefix="/monitors", tags=["monitors"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
