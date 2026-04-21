from datetime import datetime
import json
from pathlib import Path

from sqlalchemy import select

from app.db.models import Audit, AuditResult, Dataset
from app.db.session import SessionLocal
from app.services.data_pipeline import DataValidator
from app.services.fairness import run_fairness_pipeline
from app.tasks.celery_app import celery_app


def execute_audit_job(audit_id: str) -> dict:
    db = SessionLocal()
    try:
        audit = db.get(Audit, audit_id)
        if not audit:
            return {"error": "audit_not_found"}

        audit.status = "running"
        db.commit()

        dataset = db.get(Dataset, audit.dataset_id)
        if not dataset:
            audit.status = "failed"
            db.commit()
            return {"error": "dataset_not_found", "audit_id": audit_id}

        file_path = Path(dataset.file_path)
        if not file_path.exists():
            audit.status = "failed"
            db.commit()
            return {"error": "dataset_file_missing", "audit_id": audit_id}

        config = audit.config_json if isinstance(audit.config_json, dict) else json.loads(audit.config_json or "{}")

        validator = DataValidator()
        with file_path.open("rb") as handle:
            data = validator.load_data(handle, file_path.name)

        data = validator.clean_data(data)
        data = validator.sample_data(data)

        y_true_col = config.get("target") or config.get("y_true_col") or validator.detect_target_variable(data)
        if not y_true_col or y_true_col not in data.columns:
            audit.status = "failed"
            db.commit()
            return {"error": "target_column_not_found", "audit_id": audit_id}

        y_pred_col = config.get("y_pred_col") or config.get("prediction_column")
        if not y_pred_col or y_pred_col not in data.columns:
            audit.status = "failed"
            db.commit()
            return {
                "error": "prediction_column_not_found",
                "audit_id": audit_id,
                "required_config": "y_pred_col",
            }

        sensitive_attributes = config.get("sensitive_attributes") or validator.detect_sensitive_attributes(data)
        if not sensitive_attributes:
            audit.status = "failed"
            db.commit()
            return {
                "error": "sensitive_attributes_not_found",
                "audit_id": audit_id,
                "required_config": "sensitive_attributes",
            }

        score, metrics = run_fairness_pipeline(
            {
                "data": data,
                "y_true_col": y_true_col,
                "y_pred_col": y_pred_col,
                "sensitive_attributes": sensitive_attributes,
                "thresholds": config.get("thresholds", {}),
            }
        )

        existing = list(db.scalars(select(AuditResult).where(AuditResult.audit_id == audit_id)).all())
        for item in existing:
            db.delete(item)

        for metric in metrics:
            db.add(
                AuditResult(
                    audit_id=audit_id,
                    metric_name=metric.metric_name,
                    group_name=metric.group_name,
                    value=float(metric.value),
                    threshold=float(metric.threshold),
                    passed=metric.passed,
                )
            )

        audit.score = score
        audit.status = "completed"
        audit.completed_at = datetime.utcnow()
        db.commit()
        return {"audit_id": audit_id, "score": score, "status": "completed"}
    finally:
        db.close()


@celery_app.task(name="app.tasks.audit_tasks.run_audit_job")
def run_audit_job(audit_id: str) -> dict:
    return execute_audit_job(audit_id)
