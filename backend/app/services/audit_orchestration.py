"""
Production-Ready Audit Orchestration Service.
Handles the complete audit workflow from data loading to result reporting.
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import Audit, AuditResult, Dataset
from app.services.fairness import run_fairness_pipeline, MetricResult
from app.services.reporting import ComplianceReportGenerator
from app.services.ai import get_ai_service
from app.services.data_pipeline import DataValidator, load_and_validate_data
from app.core.error_handling import APIError, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)


class AuditOrchestrationError(Exception):
    """Exception for audit orchestration errors."""
    pass


class AuditService:
    """Orchestrates the complete fairness audit workflow."""
    
    def __init__(self, db: Session):
        """Initialize audit service."""
        self.db = db
        self.fairness_engine = None  # Lazy load
        self.report_generator = ComplianceReportGenerator()
        self.ai_service = get_ai_service()
        self.data_validator = DataValidator()
    
    def create_audit_from_config(
        self,
        user_id: str,
        dataset_id: str,
        config: Dict[str, Any],
        compliance_framework: str = "EEOC",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Audit:
        """
        Create a new audit from configuration.
        
        Args:
            user_id: User identifier
            dataset_id: Dataset to audit
            config: Audit configuration (thresholds, sensitive attrs, etc.)
            compliance_framework: Compliance framework (EEOC, GDPR, etc.)
            metadata: Additional metadata
            
        Returns:
            Newly created Audit object
        """
        try:
            audit = Audit(
                id=str(uuid4()),
                user_id=user_id,
                dataset_id=dataset_id,
                status="pending",
                compliance_framework=compliance_framework,
                config_json=json.dumps(config),
                metadata_json=json.dumps(metadata or {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(audit)
            self.db.commit()
            self.db.refresh(audit)
            
            logger.info(f"Created audit {audit.id} for user {user_id}")
            return audit
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create audit: {e}")
            raise AuditOrchestrationError(f"Create audit failed: {str(e)}")
    
    def run_audit(
        self,
        audit: Audit,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        sensitive_attributes: List[str],
        y_pred_proba_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the fairness audit on provided data.
        
        Args:
            audit: Audit object
            data: DataFrame to analyze
            y_true_col: Ground truth column name
            y_pred_col: Predictions column name
            sensitive_attributes: List of sensitive attribute columns
            y_pred_proba_col: Optional prediction probability column
            
        Returns:
            Audit results dictionary
        """
        try:
            # Parse config
            config = json.loads(audit.config_json)
            
            # Update audit status
            audit.status = "running"
            audit.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Starting audit {audit.id} with {len(data)} rows")
            
            # Validate data for audit
            is_valid, errors = self.data_validator.validate_for_audit(
                data, y_true_col, y_pred_col, sensitive_attributes[0]
            )
            
            if not is_valid:
                raise AuditOrchestrationError(f"Data validation failed: {'; '.join(errors)}")
            
            # Cldata
            data = self.data_validator.clean_data(data=data, handle_missing="drop")
            
            # Sample if too large
            data = self.data_validator.sample_data(data)
            
            # Compute fairness metrics
            fairness_config = {
                "data": data,
                "y_true_col": y_true_col,
                "y_pred_col": y_pred_col,
                "sensitive_attributes": sensitive_attributes,
                "y_pred_proba_col": y_pred_proba_col,
                "thresholds": config.get("thresholds", {})
            }
            
            score, metric_results = run_fairness_pipeline(fairness_config)
            
            # Store metric results
            for metric in metric_results:
                result = AuditResult(
                    id=str(uuid4()),
                    audit_id=audit.id,
                    metric_name=metric.metric_name,
                    group_name=metric.group_name,
                    value=metric.value,
                    threshold=metric.threshold,
                    passed=metric.passed
                )
                self.db.add(result)
            
            # Identify violations
            violations = [
                {
                    "metric": m.metric_name,
                    "value": m.value,
                    "threshold": m.threshold,
                    "passed": m.passed,
                    "severity": "high" if abs(m.value - m.threshold) / m.threshold > 0.2 else "medium"
                }
                for m in metric_results if not m.passed
            ]
            
            # Get AI-generated summary
            summary = self.ai_service.summarize_audit(
                score=score,
                flagged_metrics=[m.metric_name for m in metric_results if not m.passed],
                dataset_info={"sample_count": len(data)},
                compliance_framework=audit.compliance_framework
            )
            
            # Update audit with results
            audit.status = "completed"
            audit.score = score
            audit.completed_at = datetime.utcnow()
            audit.violations_json = json.dumps(violations)
            audit.summary = summary
            self.db.commit()
            
            logger.info(f"Completed audit {audit.id} with score {score}")
            
            return {
                "audit_id": audit.id,
                "status": "completed",
                "score": score,
                "violations": violations,
                "metrics": [
                    {
                        "metric_name": m.metric_name,
                        "group_name": m.group_name,
                        "value": m.value,
                        "threshold": m.threshold,
                        "passed": m.passed
                    }
                    for m in metric_results
                ],
                "summary": summary
            }
            
        except Exception as e:
            audit.status = "failed"
            audit.error_message = str(e)
            audit.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.error(f"Audit {audit.id} failed: {e}")
            raise AuditOrchestrationError(f"Audit execution failed: {str(e)}")
    
    def generate_audit_report(
        self,
        audit: Audit,
        report_format: str = "pdf"
    ) -> Optional[str]:
        """
        Generate a compliance report for completed audit.
        
        Args:
            audit: Completed audit object
            report_format: Output format (pdf or json)
            
        Returns:
            Report path or JSON string
        """
        try:
            # Get audit results
            results = self.db.query(AuditResult).filter(
                AuditResult.audit_id == audit.id
            ).all()
            
            if not results:
                raise AuditOrchestrationError("No audit results found")
            
            # Prepare data
            metrics = {
                r.metric_name: r.value for r in results
            }
            
            violations_json = audit.violations_json or "[]"
            violations = json.loads(violations_json)
            
            dataset = self.db.query(Dataset).get(audit.dataset_id)
            dataset_info = {
                "sample_count": dataset.row_count if dataset else 0,
                "sensitive_attributes": []
            }
            
            if report_format == "json":
                report = self.report_generator.generate_json_report(
                    audit_id=audit.id,
                    dataset_info=dataset_info,
                    metrics=metrics,
                    violations=violations,
                    compliance_framework=audit.compliance_framework
                )
                return json.dumps(report)
            
            elif report_format == "pdf":
                report_path = f"reports/audit_{audit.id}.pdf"
                import os
                os.makedirs("reports", exist_ok=True)
                
                from pathlib import Path
                self.report_generator.generate_pdf_report(
                    destination=Path(report_path),
                    audit_id=audit.id,
                    dataset_info=dataset_info,
                    metrics=metrics,
                    violations=violations,
                    compliance_framework=audit.compliance_framework
                )
                return report_path
            
            else:
                raise ValueError(f"Unsupported report format: {report_format}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise AuditOrchestrationError(f"Report generation failed: {str(e)}")
    
    def get_audit_insights(self, audit: Audit) -> Dict[str, Any]:
        """
        Get AI-generated insights and recommendations.
        
        Args:
            audit: Audit object
            
        Returns:
            Dictionary of insights and recommendations
        """
        try:
            if audit.status != "completed":
                raise AuditOrchestrationError("Audit must be completed first")
            
            violations_json = audit.violations_json or "[]"
            violations = json.loads(violations_json)
            
            # Get AI suggestions for each violation
            suggestions = []
            for violation in violations:
                suggestion = self.ai_service.suggest_fix(
                    metric_name=violation.get("metric", "unknown"),
                    metric_value=violation.get("value", 0),
                    violation_severity=violation.get("severity", "medium")
                )
                suggestions.append(suggestion)
            
            return {
                "audit_id": audit.id,
                "summary": audit.summary,
                "violations_count": len(violations),
                "remediation_suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            raise AuditOrchestrationError(f"Insights generation failed: {str(e)}")


def get_audit_service(db: Session) -> AuditService:
    """Factory function to get audit service."""
    return AuditService(db)
