"""
Enhanced Report Generation API with LLM Bias Detection
Comprehensive reporting endpoints combining data bias and LLM output bias analysis.
"""
from pathlib import Path
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Audit, AuditResult, Report, User, LLMBiasAnalysis
from app.db.session import get_db
from app.core.config import settings
from app.services.reporting import ComplianceReportGenerator, ReportGenerationError
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateReportRequest(BaseModel):
    """Request for generating comprehensive reports."""
    audit_id: str
    compliance_framework: str = "EEOC"
    include_llm_bias: bool = True
    llm_bias_analysis_ids: Optional[list[str]] = None


class ReportResponse(BaseModel):
    """Response for report generation."""
    report_id: str
    audit_id: str
    status: str
    pdf_path: Optional[str] = None
    json_data: Optional[dict] = None
    generated_at: str


@router.post("/generate-comprehensive", response_model=ReportResponse)
def generate_comprehensive_report(
    request: GenerateReportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Generate comprehensive report combining data bias and LLM output bias analysis.
    
    Args:
        request: Report generation request with audit ID and options
        user: Current authenticated user
        db: Database session
        
    Returns:
        Report metadata with paths/data
    """
    try:
        # Get audit
        audit = db.get(Audit, request.audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        # Get audit results
        audit_results = db.scalars(
            select(AuditResult).where(AuditResult.audit_id == request.audit_id)
        ).all()
        
        # Prepare metrics
        metrics = {}
        violations = []
        
        for result in audit_results:
            metrics[result.metric_name] = result.value
            if not result.passed:
                violations.append({
                    "metric": result.metric_name,
                    "severity": "high" if result.value > result.threshold * 1.5 else "medium",
                    "value": result.value,
                    "threshold": result.threshold,
                    "impact": f"Group '{result.group_name}' shows disparate treatment",
                    "recommendation": f"Review selection criteria for {result.group_name}"
                })
        
        # Prepare dataset info
        dataset_info = {
            "sample_count": 1000,  # Would come from dataset metadata
            "feature_count": 10,
            "quality_score": 0.95,
            "sensitive_attributes": ["gender", "race", "age"]
        }
        
        # Get LLM bias analyses if requested
        llm_bias_analyses = None
        if request.include_llm_bias:
            if request.llm_bias_analysis_ids:
                llm_bias_analyses = db.scalars(
                    select(LLMBiasAnalysis).where(
                        LLMBiasAnalysis.id.in_(request.llm_bias_analysis_ids),
                        LLMBiasAnalysis.user_id == user.id
                    )
                ).all()
            else:
                # Get user's recent LLM bias analyses
                llm_bias_analyses = db.scalars(
                    select(LLMBiasAnalysis).where(
                        LLMBiasAnalysis.user_id == user.id
                    ).order_by(LLMBiasAnalysis.created_at.desc()).limit(10)
                ).all()
            
            # Convert to dictionaries
            if llm_bias_analyses:
                llm_bias_analyses = [
                    {
                        "id": a.id,
                        "overall_bias_score": a.overall_bias_score,
                        "bias_level": a.bias_level,
                        "summary": a.summary,
                        "risks": a.risks,
                        "recommendations": a.recommendations,
                        "detected_biases": a.detected_biases
                    }
                    for a in llm_bias_analyses
                ]
        
        # Generate reports
        generator = ComplianceReportGenerator()
        
        # Generate JSON report
        json_report = generator.generate_json_report_with_llm(
            audit_id=request.audit_id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework=request.compliance_framework,
            llm_bias_analyses=llm_bias_analyses,
            metadata={"generated_by": user.email}
        )
        
        # Generate PDF report
        pdf_path = Path(settings.minio_bucket or "./reports") / f"audit_{request.audit_id}_report.pdf"
        pdf_path = generator.generate_pdf_report(
            destination=pdf_path,
            audit_id=request.audit_id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework=request.compliance_framework,
            metadata={"generated_by": user.email},
            llm_bias_analyses=llm_bias_analyses
        )
        
        # Store report metadata
        report = Report(
            audit_id=request.audit_id,
            pdf_path=str(pdf_path),
            summary_text=json_report.get("executive_summary", {})
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        logger.info(f"Comprehensive report generated for audit {request.audit_id}")
        
        return ReportResponse(
            report_id=report.id,
            audit_id=request.audit_id,
            status="completed",
            pdf_path=str(pdf_path),
            json_data=json_report,
            generated_at=report.created_at.isoformat()
        )
    
    except ReportGenerationError as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/{audit_id}/report/pdf")
def download_report_pdf(
    audit_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Download PDF report for an audit.
    
    Args:
        audit_id: Audit ID
        user: Current authenticated user
        db: Database session
        
    Returns:
        PDF file response
    """
    try:
        # Get report
        report = db.scalar(
            select(Report).where(Report.audit_id == audit_id)
        )
        
        if not report or not report.pdf_path:
            raise HTTPException(status_code=404, detail="Report not found")
        
        pdf_path = Path(report.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            path=pdf_path,
            filename=f"audit_{audit_id}_report.pdf",
            media_type="application/pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download report")


@router.get("/{audit_id}/report/json")
def get_report_json(
    audit_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get JSON report for an audit.
    
    Args:
        audit_id: Audit ID
        user: Current authenticated user
        db: Database session
        
    Returns:
        JSON report data
    """
    try:
        # Get audit
        audit = db.get(Audit, audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        
        # Get audit results
        audit_results = db.scalars(
            select(AuditResult).where(AuditResult.audit_id == audit_id)
        ).all()
        
        # Prepare data
        metrics = {}
        violations = []
        
        for result in audit_results:
            metrics[result.metric_name] = result.value
            if not result.passed:
                violations.append({
                    "metric": result.metric_name,
                    "severity": "high" if result.value > result.threshold * 1.5 else "medium",
                    "value": result.value,
                    "threshold": result.threshold,
                    "impact": f"Group '{result.group_name}' shows disparate treatment",
                    "recommendation": f"Review selection criteria for {result.group_name}"
                })
        
        # Get LLM bias analyses
        llm_analyses = db.scalars(
            select(LLMBiasAnalysis).where(
                LLMBiasAnalysis.user_id == user.id
            ).order_by(LLMBiasAnalysis.created_at.desc()).limit(10)
        ).all()
        
        llm_bias_data = [
            {
                "id": a.id,
                "overall_bias_score": a.overall_bias_score,
                "bias_level": a.bias_level,
                "summary": a.summary,
                "risks": a.risks,
                "recommendations": a.recommendations,
                "detected_biases": a.detected_biases
            }
            for a in llm_analyses
        ] if llm_analyses else None
        
        # Generate JSON report
        generator = ComplianceReportGenerator()
        
        dataset_info = {
            "sample_count": 1000,
            "feature_count": 10,
            "quality_score": 0.95,
            "sensitive_attributes": ["gender", "race", "age"]
        }
        
        report = generator.generate_json_report_with_llm(
            audit_id=audit_id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework="EEOC",
            llm_bias_analyses=llm_bias_data,
            metadata={"generated_by": user.email}
        )
        
        return report
    
    except Exception as e:
        logger.error(f"Error retrieving report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.post("/{audit_id}/report/regenerate")
def regenerate_report(
    audit_id: str,
    compliance_framework: str = Query("EEOC"),
    include_llm_bias: bool = Query(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Regenerate report for an audit with updated options.
    
    Args:
        audit_id: Audit ID
        compliance_framework: Compliance framework to use
        include_llm_bias: Whether to include LLM bias detection
        user: Current authenticated user
        db: Database session
        
    Returns:
        Updated report metadata
    """
    try:
        request = GenerateReportRequest(
            audit_id=audit_id,
            compliance_framework=compliance_framework,
            include_llm_bias=include_llm_bias
        )
        
        return generate_comprehensive_report(request, user, db)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to regenerate report")


@router.get("")
def list_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> list[dict]:
    """
    List all reports accessible to the current user.
    
    Args:
        user: Current authenticated user
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of report summaries
    """
    try:
        # Get user's audits and their reports
        audits = db.scalars(
            select(Audit).offset(skip).limit(limit)
        ).all()
        
        reports = []
        for audit in audits:
            report = db.scalar(
                select(Report).where(Report.audit_id == audit.id)
            )
            
            if report:
                reports.append({
                    "id": report.id,
                    "audit_id": audit.id,
                    "created_at": report.created_at.isoformat(),
                    "pdf_path": report.pdf_path,
                    "summary": report.summary_text
                })
        
        return reports
    
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list reports")
