from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Audit, AuditResult, Report, User, Dataset
from app.db.session import get_db
from app.schemas.audit import AuditCreate, AuditOut
from app.services.ai import summarize_audit
from app.services.reporting import generate_report_pdf
from app.tasks.audit_tasks import execute_audit_job


router = APIRouter()


@router.post("", response_model=dict)
def create_audit(payload: AuditCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    dataset = db.scalar(select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.user_id == user.id))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    config_json = payload.config_json or {}
    if "target" not in config_json:
        config_json["target"] = "approved"

    audit = Audit(dataset_id=dataset.id, model_path=payload.model_path, config_json=config_json)
    db.add(audit)
    db.commit()
    db.refresh(audit)

    try:
        result = execute_audit_job(audit.id)
        db.refresh(audit)
        return {"audit_id": audit.id, "job_id": None, "status": result.get("status", audit.status), "score": audit.score}
    except Exception:
        db.refresh(audit)
        return {"audit_id": audit.id, "job_id": None, "status": audit.status}


@router.get("", response_model=list[AuditOut])
def list_audits(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Audit]:
    return list(db.scalars(select(Audit).order_by(Audit.created_at.desc())).all())


@router.get("/{audit_id}")
def get_audit(audit_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    results = list(db.scalars(select(AuditResult).where(AuditResult.audit_id == audit_id)).all())
    return {
        "id": audit.id,
        "dataset_id": audit.dataset_id,
        "status": audit.status,
        "score": audit.score,
        "created_at": audit.created_at,
        "config": audit.config_json,
        "results": [
            {
                "metric_name": item.metric_name,
                "group_name": item.group_name,
                "value": item.value,
                "threshold": item.threshold,
                "passed": item.passed,
            }
            for item in results
        ],
    }


@router.delete("/{audit_id}")
def delete_audit(audit_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    db.delete(audit)
    db.commit()
    return {"deleted": True}


@router.post("/{audit_id}/remediate")
def remediate(audit_id: str, strategy: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    results = list(db.scalars(select(AuditResult).where(AuditResult.audit_id == audit_id)).all())
    if not results:
        raise HTTPException(status_code=400, detail="Audit has no computed metrics yet")

    flagged = [r.metric_name for r in results if not r.passed]

    return {
        "audit_id": audit_id,
        "strategy": strategy,
        "score_preview": audit.score,
        "flagged_metrics": flagged,
        "recommendation_summary": summarize_audit(audit.score or 0, flagged),
        "metrics": [
            {
                "metric_name": r.metric_name,
                "group_name": r.group_name,
                "value": r.value,
                "threshold": r.threshold,
                "passed": r.passed,
            }
            for r in results
        ],
    }


@router.get("/{audit_id}/report")
def get_report_json(audit_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    results = list(db.scalars(select(AuditResult).where(AuditResult.audit_id == audit_id)).all())
    flagged = [r.metric_name for r in results if not r.passed]
    return {
        "audit_id": audit.id,
        "score": audit.score,
        "summary": summarize_audit(audit.score or 0, flagged),
        "results": [
            {
                "metric_name": r.metric_name,
                "group_name": r.group_name,
                "value": r.value,
                "threshold": r.threshold,
                "passed": r.passed,
            }
            for r in results
        ],
    }


@router.get("/{audit_id}/report/pdf")
def get_report_pdf(audit_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FileResponse:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    report_path = Path("tmp") / f"report-{audit_id}.pdf"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report_pdf(report_path, "FairLens Compliance Report", f"Audit ID: {audit_id}\nGenerated: {datetime.utcnow().isoformat()}Z")
    report = db.scalar(select(Report).where(Report.audit_id == audit_id))
    if not report:
        report = Report(audit_id=audit_id, pdf_path=str(report_path))
        db.add(report)
    else:
        report.pdf_path = str(report_path)
    db.commit()

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"fairlens-report-{audit_id}.pdf",
    )
