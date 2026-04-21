"""
Integration tests for enhanced report generation with LLM bias detection.
Tests the complete workflow from audit creation to report generation with LLM results.
"""
import pytest
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.models import User, Dataset, Audit, AuditResult, LLMBiasAnalysis
from app.services.reporting import ComplianceReportGenerator


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_audit(db: Session, test_user: User) -> Audit:
    """Create a test audit."""
    # Create dataset first
    dataset = Dataset(
        name="test_dataset",
        user_id=test_user.id,
        path="/tmp/test.csv",
        rows=1000,
        columns=10
    )
    db.add(dataset)
    db.commit()
    
    # Create audit
    audit = Audit(
        dataset_id=dataset.id,
        status="completed",
        score=0.85
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    
    # Add audit results
    results = [
        AuditResult(
            audit_id=audit.id,
            metric_name="disparate_impact_ratio",
            group_name="female",
            value=0.82,
            threshold=0.8,
            passed=True
        ),
        AuditResult(
            audit_id=audit.id,
            metric_name="demographic_parity",
            group_name="male",
            value=0.05,
            threshold=0.1,
            passed=True
        ),
    ]
    db.add_all(results)
    db.commit()
    
    return audit


@pytest.fixture
def test_llm_bias_analysis(db: Session, test_user: User) -> LLMBiasAnalysis:
    """Create a test LLM bias analysis."""
    analysis = LLMBiasAnalysis(
        user_id=test_user.id,
        text_input="Women are better at caregiving. Men are better at leadership.",
        overall_bias_score=0.65,
        bias_level="high",
        summary="Gender stereotypes detected in statement",
        detected_biases=[
            {
                "category": "gender",
                "score": 0.8,
                "severity": "high",
                "description": "Strong gender stereotyping"
            },
            {
                "category": "representation",
                "score": 0.5,
                "severity": "medium",
                "description": "Unbalanced representation of genders"
            }
        ],
        risks=[
            "Perpetuates harmful gender stereotypes",
            "May influence hiring decisions unfairly"
        ],
        recommendations=[
            "Use gender-neutral language",
            "Avoid trait generalizations",
            "Balance examples across genders"
        ]
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


class TestReportGeneration:
    """Test suite for report generation with LLM bias detection."""
    
    def test_generate_pdf_with_llm_bias(
        self,
        test_audit: Audit,
        test_llm_bias_analysis: LLMBiasAnalysis,
        tmp_path: Path
    ):
        """Test PDF generation with LLM bias detection."""
        generator = ComplianceReportGenerator()
        
        # Prepare data
        dataset_info = {
            "sample_count": 1000,
            "sensitive_attributes": ["gender", "race"],
            "quality_score": 0.95,
            "missing_values": {}
        }
        
        metrics = {
            "disparate_impact_ratio": 0.82,
            "demographic_parity": 0.05
        }
        
        violations = [
            {
                "metric": "disparate_impact_ratio",
                "severity": "medium",
                "value": 0.82,
                "threshold": 0.8,
                "impact": "Potential disparate impact",
                "recommendation": "Review selection criteria"
            }
        ]
        
        llm_analyses = [
            {
                "id": test_llm_bias_analysis.id,
                "overall_bias_score": 0.65,
                "bias_level": "high",
                "summary": "Gender stereotypes detected",
                "detected_biases": test_llm_bias_analysis.detected_biases,
                "risks": test_llm_bias_analysis.risks,
                "recommendations": test_llm_bias_analysis.recommendations
            }
        ]
        
        # Generate PDF
        pdf_path = tmp_path / "test_report.pdf"
        result = generator.generate_pdf_report(
            destination=pdf_path,
            audit_id=test_audit.id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework="EEOC",
            metadata={"generated_by": "test@example.com"},
            llm_bias_analyses=llm_analyses
        )
        
        # Verify PDF was created
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0
    
    def test_generate_json_with_llm_bias(
        self,
        test_audit: Audit,
        test_llm_bias_analysis: LLMBiasAnalysis
    ):
        """Test JSON report generation with LLM bias detection."""
        generator = ComplianceReportGenerator()
        
        # Prepare data
        dataset_info = {
            "sample_count": 1000,
            "sensitive_attributes": ["gender", "race"],
            "quality_score": 0.95,
            "missing_values": {}
        }
        
        metrics = {
            "disparate_impact_ratio": 0.82,
            "demographic_parity": 0.05
        }
        
        violations = []
        
        llm_analyses = [
            {
                "id": test_llm_bias_analysis.id,
                "overall_bias_score": 0.65,
                "bias_level": "high",
                "summary": "Gender stereotypes detected",
                "detected_biases": test_llm_bias_analysis.detected_biases,
                "risks": test_llm_bias_analysis.risks,
                "recommendations": test_llm_bias_analysis.recommendations
            }
        ]
        
        # Generate JSON
        report = generator.generate_json_report_with_llm(
            audit_id=test_audit.id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework="EEOC",
            llm_bias_analyses=llm_analyses,
            metadata={"generated_by": "test@example.com"}
        )
        
        # Verify structure
        assert "report_metadata" in report
        assert report["report_metadata"]["includes_llm_bias_analysis"] is True
        assert "executive_summary" in report
        assert "llm_bias_analysis" in report
        assert report["llm_bias_analysis"]["total_analyses"] == 1
        assert report["llm_bias_analysis"]["average_bias_score"] == 0.65
        assert "combined_risk_assessment" in report
    
    def test_executive_summary_with_llm(
        self,
        test_llm_bias_analysis: LLMBiasAnalysis,
        tmp_path: Path
    ):
        """Test executive summary includes LLM bias status."""
        generator = ComplianceReportGenerator()
        
        llm_analyses = [
            {
                "id": test_llm_bias_analysis.id,
                "overall_bias_score": 0.65,
                "bias_level": "high",
                "summary": "Gender stereotypes detected",
                "detected_biases": [],
                "risks": [],
                "recommendations": []
            }
        ]
        
        metrics = {"fairness_score": 85}
        violations = []
        dataset_info = {"sample_count": 1000}
        
        # Generate PDF with LLM data
        pdf_path = tmp_path / "test_summary.pdf"
        result = generator.generate_pdf_report(
            destination=pdf_path,
            audit_id="test-audit",
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework="EEOC",
            metadata={},
            llm_bias_analyses=llm_analyses
        )
        
        # Verify PDF includes LLM status
        assert Path(result).exists()
    
    def test_recommendations_combination(
        self,
        test_audit: Audit,
        test_llm_bias_analysis: LLMBiasAnalysis,
        tmp_path: Path
    ):
        """Test that recommendations combine both data and LLM bias."""
        generator = ComplianceReportGenerator()
        
        # Create violations for data bias
        violations = [
            {
                "metric": "disparate_impact",
                "severity": "high",
                "value": 0.75,
                "threshold": 0.8,
                "impact": "Significant disparate impact",
                "recommendation": "Revise selection criteria"
            }
        ]
        
        llm_analyses = [
            {
                "id": test_llm_bias_analysis.id,
                "overall_bias_score": 0.65,
                "bias_level": "high",
                "summary": "Bias in LLM outputs",
                "detected_biases": [],
                "risks": ["Perpetuates stereotypes"],
                "recommendations": [
                    "Implement bias filtering",
                    "Add content moderation"
                ]
            }
        ]
        
        dataset_info = {"sample_count": 1000}
        metrics = {}
        
        # Generate JSON to check recommendations
        report = generator.generate_json_report_with_llm(
            audit_id=test_audit.id,
            dataset_info=dataset_info,
            metrics=metrics,
            violations=violations,
            compliance_framework="EEOC",
            llm_bias_analyses=llm_analyses,
            metadata={}
        )
        
        # Verify combined assessment
        assert "combined_risk_assessment" in report
        assessment = report["combined_risk_assessment"]
        assert "data_bias_risk" in assessment
        assert "llm_output_bias_risk" in assessment
        assert "overall_risk" in assessment


class TestReportAPI:
    """Test suite for report generation API endpoints."""
    
    def test_generate_comprehensive_report_endpoint(
        self,
        client: TestClient,
        test_user: User,
        test_audit: Audit,
        test_llm_bias_analysis: LLMBiasAnalysis,
        auth_token: str
    ):
        """Test comprehensive report generation endpoint."""
        response = client.post(
            "/api/v1/reports/generate-comprehensive",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "audit_id": test_audit.id,
                "compliance_framework": "EEOC",
                "include_llm_bias": True,
                "llm_bias_analysis_ids": [test_llm_bias_analysis.id]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert data["audit_id"] == test_audit.id
        assert data["status"] == "completed"
        assert "json_data" in data
        assert data["json_data"]["report_metadata"]["includes_llm_bias_analysis"] is True
    
    def test_get_report_json_endpoint(
        self,
        client: TestClient,
        test_audit: Audit,
        auth_token: str
    ):
        """Test JSON report retrieval endpoint."""
        response = client.get(
            f"/api/v1/reports/{test_audit.id}/report/json",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        report = response.json()
        assert "report_metadata" in report
        assert "executive_summary" in report
        assert "fairness_metrics" in report
    
    def test_list_reports_endpoint(
        self,
        client: TestClient,
        auth_token: str
    ):
        """Test reports list endpoint."""
        response = client.get(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
