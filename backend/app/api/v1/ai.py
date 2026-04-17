from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import User
from app.services.ai import explain_metric, suggest_fix, summarize_audit


router = APIRouter()


@router.post("/explain")
def explain(payload: dict, _: User = Depends(get_current_user)) -> dict:
    return {
        "message": explain_metric(
            payload.get("metric_name", "metric"),
            float(payload.get("metric_value", 0.0)),
            float(payload.get("threshold", 0.0)),
        )
    }


@router.post("/suggest")
def suggest(payload: dict, _: User = Depends(get_current_user)) -> dict:
    return {"recommendation": suggest_fix(payload)}


@router.post("/summarize")
def summarize(payload: dict, _: User = Depends(get_current_user)) -> dict:
    return {
        "summary": summarize_audit(
            float(payload.get("score", 0.0)),
            payload.get("flagged_metrics", []),
        )
    }
