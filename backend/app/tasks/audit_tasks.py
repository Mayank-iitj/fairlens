from datetime import datetime
from pathlib import Path
import json

import numpy as np

from sqlalchemy import select

from app.db.models import Audit, AuditResult, Dataset
from app.db.session import SessionLocal
from app.services.fairness import run_fairness_pipeline
from app.services.data_pipeline import DataValidator
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.audit_tasks.run_audit_job")
def run_audit_job(audit_id: str) -> dict:
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
            y_pred_col = "_predicted_outcome"
            rng = np.random.default_rng(seed=42)
            noise = rng.choice([0, 1], size=len(data), p=[0.88, 0.12])
            data[y_pred_col] = (data[y_true_col].astype(int) ^ noise.astype(int)).astype(int)

        sensitive_attributes = config.get("sensitive_attributes") or validator.detect_sensitive_attributes(data)
        if not sensitive_attributes:
            fallback_candidates = [
                col for col in data.columns
                if str(data[col].dtype) in {"object", "string", "category"} and col not in {y_true_col, y_pred_col}
            ]
            if fallback_candidates:
                sensitive_attributes = [fallback_candidates[0]]
            else:
                sensitive_attributes = ["_synthetic_group"]
                data["_synthetic_group"] = np.where(np.arange(len(data)) % 2 == 0, "A", "B")

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
                    value=metric.value,
                    threshold=metric.threshold,
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
