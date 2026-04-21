"""
Production-Ready Report Generation Engine.
Generates comprehensive PDF and JSON compliance reports with audit trails.
"""
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Custom exception for report generation errors."""
    pass


class ComplianceReportGenerator:
    """Production-ready compliance report generator."""
    
    # Compliance frameworks and their audit points
    COMPLIANCE_FRAMEWORKS = {
        "EEOC": {
            "name": "Equal Employment Opportunity Commission",
            "audit_points": [
                "4/5ths Rule (Disparate Impact)",
                "Equal Selection Rates",
                "Neutral Impact Documentation",
                "Business Necessity Justification"
            ],
            "thresholds": {"disparate_impact": 0.8}
        },
        "GDPR": {
            "name": "General Data Protection Regulation (EU)",
            "audit_points": [
                "Automated Decision Making Transparency",
                "Right to Explanation",
                "Bias Impact Assessment",
                "Data Processing Records"
            ],
            "thresholds": {"demographic_parity_diff": 0.1}
        },
        "ECOA": {
            "name": "Equal Credit Opportunity Act",
            "audit_points": [
                "Neutral Credit Scoring",
                "Protected Class Parity",
                "Predictor Validity",
                "Disparate Treatment Prevention"
            ],
            "thresholds": {"disparate_impact": 0.8}
        },
        "Fair_Housing": {
            "name": "Fair Housing Act",
            "audit_points": [
                "Protected Class Non-Discrimination",
                "Housing Accessibility",
                "Credit Neutrality",
                "Lending Parity"
            ],
            "thresholds": {"demographic_parity_diff": 0.1}
        },
        "EU_AI_Act": {
            "name": "EU Artificial Intelligence Act",
            "audit_points": [
                "High-Risk AI Classification",
                "Bias & Discrimination Monitoring",
                "Documentation Requirements",
                "Human Oversight Mechanisms"
            ],
            "thresholds": {"equalized_odds_diff": 0.1}
        }
    }
    
    def __init__(self):
        """Initialize report generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#3d2320'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#875c3c'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ViolationText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.red,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='ComplianceText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.green,
            spaceAfter=6
        ))
    
    def generate_json_report(
        self,
        audit_id: str,
        dataset_info: Dict[str, Any],
        metrics: Dict[str, Any],
        violations: List[Dict[str, Any]],
        compliance_framework: str,
        metadata: Optional[Dict[str, Any]] = None,
        llm_bias_analyses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive JSON compliance report with optional LLM bias data.
        
        Args:
            audit_id: Unique audit identifier
            dataset_info: Information about the dataset
            metrics: Computed fairness metrics
            violations: List of violation findings
            compliance_framework: Which framework (EEOC, GDPR, etc.)
            metadata: Additional metadata
            llm_bias_analyses: Optional list of LLM bias analysis results
            
        Returns:
            Complete JSON report as dict
        """
        try:
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "report_version": "1.0",
                    "audit_id": audit_id,
                    "compliance_framework": compliance_framework,
                    "includes_llm_bias_analysis": llm_bias_analyses is not None and len(llm_bias_analyses) > 0
                },
                "executive_summary": {
                    "total_metrics": len(metrics),
                    "violations_found": len(violations),
                    "compliance_status": "PASS" if len(violations) == 0 else "FAIL",
                    "llm_analyses_count": len(llm_bias_analyses) if llm_bias_analyses else 0,
                    "recommendations_count": len(violations)
                },
                "dataset_analysis": {
                    "samples_analyzed": dataset_info.get("sample_count", 0),
                    "sensitive_attributes": dataset_info.get("sensitive_attributes", []),
                    "data_quality_score": dataset_info.get("quality_score", 1.0),
                    "missing_values": dataset_info.get("missing_values", {})
                },
                "fairness_metrics": {
                    k: float(v) if isinstance(v, (int, float)) else v
                    for k, v in metrics.items()
                },
                "violations": [
                    {
                        "metric": v.get("metric", "unknown"),
                        "severity": v.get("severity", "medium"),
                        "value": float(v.get("value", 0)) if isinstance(v.get("value"), (int, float)) else v.get("value"),
                        "threshold": float(v.get("threshold", 0)) if isinstance(v.get("threshold"), (int, float)) else v.get("threshold"),
                        "impact": v.get("impact", "Unknown"),
                        "recommendation": v.get("recommendation", "")
                    }
                    for v in violations
                ],
                "compliance_checklist": self._generate_compliance_checklist(
                    compliance_framework, metrics, violations
                ),
                "remediation_suggestions": self._generate_remediation_suggestions(violations),
                "audit_trail": {
                    "framework_used": compliance_framework,
                    "thresholds_applied": self.COMPLIANCE_FRAMEWORKS.get(
                        compliance_framework, {}
                    ).get("thresholds", {}),
                    "auditor_notes": metadata.get("notes", "") if metadata else ""
                }
            }
            
            # Add LLM bias analysis if provided
            if llm_bias_analyses:
                total_llm = len(llm_bias_analyses)
                avg_bias = sum(a.get('overall_bias_score', 0) for a in llm_bias_analyses) / total_llm if total_llm > 0 else 0
                
                report["llm_bias_analysis"] = {
                    "total_analyses": total_llm,
                    "average_bias_score": avg_bias,
                    "high_risk_count": sum(1 for a in llm_bias_analyses if a.get('bias_level') in ['high', 'critical']),
                    "critical_count": sum(1 for a in llm_bias_analyses if a.get('bias_level') == 'critical'),
                    "bias_categories_detected": list(set(
                        b.get('category')
                        for a in llm_bias_analyses
                        for b in a.get('detected_biases', [])
                    )),
                    "analyses": [
                        {
                            "id": a.get('id'),
                            "overall_bias_score": a.get('overall_bias_score'),
                            "bias_level": a.get('bias_level'),
                            "summary": a.get('summary'),
                            "risks": a.get('risks', []),
                            "recommendations": a.get('recommendations', []),
                            "detected_biases": [
                                {
                                    "category": b.get('category'),
                                    "score": b.get('score'),
                                    "severity": b.get('severity'),
                                    "description": b.get('description')
                                }
                                for b in a.get('detected_biases', [])
                            ]
                        }
                        for a in llm_bias_analyses[:10]  # Include first 10
                    ]
                }
            
            logger.info(f"JSON report generated for audit {audit_id}")
            return report
            
        except Exception as e:
            logger.error(f"JSON report generation failed: {e}")
            raise ReportGenerationError(f"Failed to generate JSON report: {str(e)}")
    
    def generate_pdf_report(
        self,
        destination: Path,
        audit_id: str,
        dataset_info: Dict[str, Any],
        metrics: Dict[str, Any],
        violations: List[Dict[str, Any]],
        compliance_framework: str,
        metadata: Optional[Dict[str, Any]] = None,
        llm_bias_analyses: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """
        Generate production-quality PDF compliance report with LLM bias detection.
        
        Args:
            destination: Output file path
            audit_id: Unique audit identifier
            dataset_info: Information about the dataset
            metrics: Computed fairness metrics
            violations: List of violation findings
            compliance_framework: Which framework (EEOC, GDPR, etc.)
            metadata: Additional metadata
            llm_bias_analyses: Optional list of LLM bias analysis results
            
        Returns:
            Path to generated PDF
        """
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Create document
            doc = SimpleDocTemplate(
                str(destination),
                pagesize=letter,
                rightMargin=72, leftMargin=72,
                topMargin=72, bottomMargin=18
            )
            
            story = []
            
            # Title page
            story.extend(self._build_title_page(audit_id, compliance_framework))
            story.append(PageBreak())
            
            # Executive Summary
            story.extend(self._build_executive_summary(metrics, violations, llm_bias_analyses))
            story.append(PageBreak())
            
            # Dataset Analysis
            story.extend(self._build_dataset_section(dataset_info))
            story.append(PageBreak())
            
            # Fairness Metrics
            story.extend(self._build_metrics_section(metrics))
            story.append(PageBreak())
            
            # Violations & Findings
            if violations:
                story.extend(self._build_violations_section(violations))
                story.append(PageBreak())
            
            # LLM Bias Detection Section (NEW)
            if llm_bias_analyses:
                story.extend(self._build_llm_bias_section(llm_bias_analyses))
                story.append(PageBreak())
            
            # Compliance Checklist
            story.extend(self._build_compliance_section(
                compliance_framework, metrics, violations
            ))
            story.append(PageBreak())
            
            # Remediation Plan
            story.extend(self._build_remediation_section(violations))
            story.append(PageBreak())
            
            # Comprehensive Recommendations
            story.extend(self._build_comprehensive_recommendations(
                violations, llm_bias_analyses
            ))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated at {destination}")
            return destination
            
        except Exception as e:
            logger.error(f"PDF report generation failed: {e}")
            raise ReportGenerationError(f"Failed to generate PDF: {str(e)}")
    
    def _build_title_page(self, audit_id: str, framework: str) -> List:
        """Build title page sections."""
        story = []
        
        story.append(Spacer(1, 1.5*inch))
        
        title = Paragraph(
            "FairLens Audit Report",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        subtitle = Paragraph(
            f"{self.COMPLIANCE_FRAMEWORKS.get(framework, {}).get('name', framework)} Compliance",
            self.styles['Heading2']
        )
        story.append(subtitle)
        
        story.append(Spacer(1, 1*inch))
        
        info_data = [
            ["Audit ID:", audit_id],
            ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Framework:", framework],
            ["Classification:", "CONFIDENTIAL"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(info_table)
        
        return story
    
    def _build_executive_summary(
        self,
        metrics: Dict,
        violations: List,
        llm_bias_analyses: Optional[List[Dict]] = None
    ) -> List:
        """Build executive summary section with LLM bias data."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        compliance_status = "COMPLIANT ✓" if len(violations) == 0 else "NON-COMPLIANT ✗"
        status_color = colors.green if len(violations) == 0 else colors.red
        
        # Calculate LLM bias status
        llm_bias_status = "SAFE ✓"
        if llm_bias_analyses:
            high_risk = sum(1 for a in llm_bias_analyses if a.get('bias_level') in ['high', 'critical'])
            if high_risk > 0:
                llm_bias_status = f"CONCERNS ({high_risk} high-risk) ⚠"
        
        summary_data = [
            ["Data Fairness Status:", compliance_status],
            ["Metrics Analyzed:", str(len(metrics))],
            ["Data Violations Found:", str(len(violations))],
            ["LLM Bias Status:", llm_bias_status],
        ]
        
        if llm_bias_analyses:
            avg_llm_bias = sum(a.get('overall_bias_score', 0) for a in llm_bias_analyses) / len(llm_bias_analyses)
            summary_data.append(["Average LLM Bias Score:", f"{avg_llm_bias:.1%}"])
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary text
        summary_msg = (
            f"This audit evaluated the fairness and compliance of the analyzed model/system. "
            f"Found <b>{len(violations)}</b> data bias violations and analyzed "
            f"<b>{len(llm_bias_analyses) if llm_bias_analyses else 0}</b> LLM outputs for bias. "
            f"See detailed sections for specific findings and recommendations."
        )
        
        story.append(Paragraph(summary_msg, self.styles['BodyText']))
        
        return story
    
    def _build_dataset_section(self, dataset_info: Dict) -> List:
        """Build dataset analysis section."""
        story = []
        
        story.append(Paragraph("Dataset Analysis", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        data_rows = [
            ["Metric", "Value"],
            ["Samples Analyzed", str(dataset_info.get("sample_count", "Unknown"))],
            ["Features", str(dataset_info.get("feature_count", "Unknown"))],
            ["Data Quality Score", f"{dataset_info.get('quality_score', 0):.1%}"],
            ["Sensitive Attributes", ", ".join(dataset_info.get("sensitive_attributes", []))],
        ]
        
        data_table = Table(data_rows, colWidths=[2.5*inch, 3.5*inch])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#875c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(data_table)
        
        return story
    
    def _build_metrics_section(self, metrics: Dict) -> List:
        """Build fairness metrics section."""
        story = []
        
        story.append(Paragraph("Fairness Metrics", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        metric_rows = [["Metric", "Value", "Status"]]
        
        metric_thresholds = {
            "disparate_impact_ratio": (0.8, ">="),
            "demographic_parity_difference": (0.1, "<="),
            "equalized_odds_difference": (0.1, "<="),
            "predictive_parity_difference": (0.1, "<="),
        }
        
        for metric_name, value in metrics.items():
            if metric_name not in metric_thresholds:
                continue
            
            if isinstance(value, (int, float)):
                threshold, operator = metric_thresholds[metric_name]
                
                passes = (value >= threshold) if operator == ">=" else (value <= threshold)
                status = "✓ PASS" if passes else "✗ FAIL"
                
                metric_rows.append([
                    metric_name.replace("_", " ").title(),
                    f"{value:.4f}",
                    status
                ])
        
        metrics_table = Table(metric_rows, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#875c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(metrics_table)
        
        return story
    
    def _build_violations_section(self, violations: List) -> List:
        """Build violations and findings section."""
        story = []
        
        story.append(Paragraph("Violations & Findings", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        for i, violation in enumerate(violations, 1):
            violation_title = Paragraph(
                f"Finding {i}: {violation.get('metric', 'Unknown').replace('_', ' ').title()}",
                self.styles['Heading3']
            )
            story.append(violation_title)
            
            details = [
                f"<b>Severity:</b> {violation.get('severity', 'Medium').upper()}",
                f"<b>Value:</b> {violation.get('value', 0):.4f}",
                f"<b>Threshold:</b> {violation.get('threshold', 0):.4f}",
                f"<b>Impact:</b> {violation.get('impact', 'Unknown')}",
            ]
            
            for detail in details:
                style = 'ViolationText' if violation.get('severity') == 'high' else 'Normal'
                story.append(Paragraph(detail, self.styles[style]))
            
            if violation.get('recommendation'):
                story.append(Paragraph(
                    f"<b>Recommendation:</b> {violation['recommendation']}",
                    self.styles['Normal']
                ))
            
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _build_compliance_section(
        self,
        framework: str,
        metrics: Dict,
        violations: List
    ) -> List:
        """Build compliance checklist section."""
        story = []
        
        story.append(Paragraph("Compliance Checklist", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        framework_info = self.COMPLIANCE_FRAMEWORKS.get(
            framework, {"audit_points": [], "name": framework}
        )
        
        checklist_rows = [["Requirement", "Status"]]
        
        for point in framework_info.get("audit_points", []):
            status = "✓ PASS" if len(violations) == 0 else "✗ REVIEW"
            checklist_rows.append([point, status])
        
        checklist_table = Table(checklist_rows, colWidths=[4*inch, 2*inch])
        checklist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#875c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(checklist_table)
        
        return story
    
    def _build_remediation_section(self, violations: List) -> List:
        """Build remediation plan section."""
        story = []
        
        story.append(Paragraph("Remediation Plan", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        if not violations:
            story.append(Paragraph(
                "No violations detected. The model appears to be compliant with fairness standards.",
                self.styles['ComplianceText']
            ))
            return story
        
        remediation_steps = [
            "1. <b>Immediate Actions:</b> Address critical severity violations",
            "2. <b>Short-term (1-3 months):</b> Implement fairness constraints and rebalancing",
            "3. <b>Medium-term (3-6 months):</b> Retrain model with fairness objectives",
            "4. <b>Long-term (6+ months):</b> Establish continuous fairness monitoring",
            "5. <b>Ongoing:</b> Regular bias audits and stakeholder engagement"
        ]
        
        for step in remediation_steps:
            story.append(Paragraph(step, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _generate_compliance_checklist(
        self,
        framework: str,
        metrics: Dict,
        violations: List
    ) -> Dict[str, Any]:
        """Generate compliance checklist for JSON report."""
        framework_info = self.COMPLIANCE_FRAMEWORKS.get(
            framework, {"audit_points": [], "name": framework}
        )
        
        return {
            "framework": framework,
            "framework_name": framework_info.get("name", framework),
            "audit_points": [
                {
                    "requirement": point,
                    "status": "PASS" if len(violations) == 0 else "REVIEW",
                    "evidence": "Verified through metrics"
                }
                for point in framework_info.get("audit_points", [])
            ]
        }
    
    def _generate_remediation_suggestions(self, violations: List) -> List[Dict]:
        """Generate remediation suggestions."""
        suggestions = []
        
        for violation in violations:
            suggestion = {
                "metric": violation.get("metric", "unknown"),
                "severity": violation.get("severity", "medium"),
                "immediate_action": self._get_immediate_action(violation),
                "short_term_fixes": self._get_short_term_fixes(violation),
                "long_term_strategy": self._get_long_term_strategy(violation)
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _get_immediate_action(self, violation: Dict) -> str:
        """Get immediate remediation action."""
        metric = violation.get("metric", "")
        
        if "disparate_impact" in metric:
            return "Review selection/approval criteria for protected classes"
        elif "demographic_parity" in metric:
            return "Analyze feature importance by demographic group"
        elif "equalized_odds" in metric:
            return "Investigate false positive/negative rates by group"
        else:
            return "Conduct targeted bias investigation"
    
    def _get_short_term_fixes(self, violation: Dict) -> List[str]:
        """Get short-term remediation fixes."""
        return [
            "Apply fairness constraints (e.g., equalized odds, demographic parity)",
            "Implement threshold adjustments per demographic group",
            "Increase sample collection for underrepresented groups",
            "Conduct stakeholder review and documentation"
        ]
    
    def _get_long_term_strategy(self, violation: Dict) -> str:
        """Get long-term remediation strategy."""
        return (
            "Establish feedback loops with affected communities, "
            "implement continuous fairness monitoring, "
            "retrain model with fairness objectives, "
            "and document all bias mitigation efforts"
        )
    
    def _build_llm_bias_section(self, llm_analyses: List[Dict[str, Any]]) -> List:
        """Build LLM bias detection section (NEW)."""
        story = []
        
        story.append(Paragraph("LLM Output Bias Analysis", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        if not llm_analyses:
            story.append(Paragraph(
                "No LLM bias analyses performed.",
                self.styles['Normal']
            ))
            return story
        
        # Summary statistics
        total_analyses = len(llm_analyses)
        avg_bias_score = sum(a.get('overall_bias_score', 0) for a in llm_analyses) / total_analyses
        high_risk_count = sum(1 for a in llm_analyses if a.get('bias_level') in ['high', 'critical'])
        
        summary_rows = [
            ["Total Analyses", str(total_analyses)],
            ["Average Bias Score", f"{avg_bias_score:.2%}"],
            ["High-Risk Detections", str(high_risk_count)],
            ["Critical Findings", str(sum(1 for a in llm_analyses if a.get('bias_level') == 'critical'))]
        ]
        
        summary_table = Table(summary_rows, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Bias type breakdown
        story.append(Paragraph("Detected Bias Types", self.styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        bias_breakdown = {}
        for analysis in llm_analyses:
            for bias in analysis.get('detected_biases', []):
                category = bias.get('category', 'unknown')
                bias_breakdown[category] = bias_breakdown.get(category, 0) + 1
        
        if bias_breakdown:
            bias_rows = [["Bias Type", "Occurrences"]]
            bias_rows.extend([[k, str(v)] for k, v in bias_breakdown.items()])
            
            bias_table = Table(bias_rows, colWidths=[2.5*inch, 3.5*inch])
            bias_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9534f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(bias_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Detailed findings
        story.append(Paragraph("Detailed Findings", self.styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, analysis in enumerate(llm_analyses[:5], 1):  # Show first 5
            bias_level = analysis.get('bias_level', 'unknown').upper()
            bias_color = {
                'CRITICAL': colors.red,
                'HIGH': colors.orange,
                'MODERATE': colors.yellow,
                'LOW': colors.green,
                'VERY_LOW': colors.lightgreen
            }.get(bias_level, colors.grey)
            
            finding_text = (
                f"<b>Analysis {idx}:</b> {bias_level}<br/>"
                f"Score: {analysis.get('overall_bias_score', 0):.1%}<br/>"
                f"Summary: {analysis.get('summary', 'N/A')}"
            )
            
            story.append(Paragraph(finding_text, self.styles['Normal']))
            
            # Key recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                story.append(Paragraph(
                    f"<b>Recommendations:</b> {'; '.join(recommendations[:2])}",
                    self.styles['Normal']
                ))
            
            story.append(Spacer(1, 0.15*inch))
        
        if len(llm_analyses) > 5:
            story.append(Paragraph(
                f"... and {len(llm_analyses) - 5} more analyses",
                self.styles['Normal']
            ))
        
        return story
    
    def _build_comprehensive_recommendations(
        self,
        violations: List[Dict],
        llm_bias_analyses: Optional[List[Dict]] = None
    ) -> List:
        """Build comprehensive recommendations section combining all findings."""
        story = []
        
        story.append(Paragraph("Comprehensive Recommendations", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        # Collect all recommendations
        data_bias_recs = []
        for violation in violations:
            if violation.get('recommendation'):
                data_bias_recs.append(violation['recommendation'])
        
        llm_bias_recs = []
        if llm_bias_analyses:
            for analysis in llm_bias_analyses:
                llm_bias_recs.extend(analysis.get('recommendations', [])[:2])
        
        # Priority categories
        priority_items = {
            "CRITICAL ACTIONS (Immediate)": [],
            "HIGH PRIORITY (1-2 weeks)": [],
            "MEDIUM PRIORITY (1-4 weeks)": [],
            "ONGOING MONITORING": []
        }
        
        # Categorize data bias recommendations
        critical_keywords = ['critical', 'severe', 'immediate']
        for rec in data_bias_recs:
            if any(kw in rec.lower() for kw in critical_keywords):
                priority_items["CRITICAL ACTIONS (Immediate)"].append(rec)
            else:
                priority_items["HIGH PRIORITY (1-2 weeks)"].append(rec)
        
        # Categorize LLM bias recommendations
        if llm_bias_recs:
            priority_items["MEDIUM PRIORITY (1-4 weeks)"].extend(llm_bias_recs)
        
        priority_items["ONGOING MONITORING"].extend([
            "Establish continuous fairness monitoring dashboard",
            "Schedule monthly bias audit reviews",
            "Maintain bias detection audit trail",
            "Track remediation implementation progress",
            "Engage stakeholders in feedback loops"
        ])
        
        # Build recommendation table
        for priority, recommendations in priority_items.items():
            if not recommendations:
                continue
            
            story.append(Paragraph(priority, self.styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            for i, rec in enumerate(recommendations[:3], 1):  # Show top 3 per category
                rec_text = rec[:100] + "..." if len(rec) > 100 else rec
                story.append(Paragraph(f"{i}. {rec_text}", self.styles['Normal']))
            
            if len(recommendations) > 3:
                story.append(Paragraph(
                    f"... and {len(recommendations) - 3} more items",
                    self.styles['Normal']
                ))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Implementation timeline
        story.append(Paragraph("Implementation Timeline", self.styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        timeline = [
            "<b>Week 1:</b> Executive review and resource allocation",
            "<b>Weeks 2-3:</b> Critical bias fixes and control implementations",
            "<b>Weeks 4-8:</b> Model retraining and fairness constraint deployment",
            "<b>Weeks 8+:</b> Continuous monitoring and performance validation",
            "<b>Ongoing:</b> Quarterly audit and stakeholder engagement"
        ]
        
        for item in timeline:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 0.08*inch))
        
        return story
    
    def generate_json_report_with_llm(
        self,
        audit_id: str,
        dataset_info: Dict[str, Any],
        metrics: Dict[str, Any],
        violations: List[Dict[str, Any]],
        compliance_framework: str,
        llm_bias_analyses: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive JSON report with LLM bias detection results.
        
        Args:
            audit_id: Unique audit identifier
            dataset_info: Information about the dataset
            metrics: Computed fairness metrics
            violations: List of violation findings
            compliance_framework: Which framework (EEOC, GDPR, etc.)
            llm_bias_analyses: Optional list of LLM bias analysis results
            metadata: Additional metadata
            
        Returns:
            Complete JSON report as dict
        """
        # Get base report
        report = self.generate_json_report(
            audit_id, dataset_info, metrics, violations,
            compliance_framework, metadata
        )
        
        # Add LLM bias section
        if llm_bias_analyses:
            total_analyses = len(llm_bias_analyses)
            avg_bias_score = sum(a.get('overall_bias_score', 0) for a in llm_bias_analyses) / total_analyses if total_analyses > 0 else 0
            
            llm_bias_summary = {
                "total_analyses": total_analyses,
                "average_bias_score": avg_bias_score,
                "high_risk_count": sum(1 for a in llm_bias_analyses if a.get('bias_level') in ['high', 'critical']),
                "critical_count": sum(1 for a in llm_bias_analyses if a.get('bias_level') == 'critical'),
                "analysis_details": [
                    {
                        "id": a.get('id'),
                        "bias_score": a.get('overall_bias_score'),
                        "bias_level": a.get('bias_level'),
                        "detected_biases": [
                            {
                                "category": b.get('category'),
                                "score": b.get('score'),
                                "severity": b.get('severity')
                            }
                            for b in a.get('detected_biases', [])
                        ],
                        "summary": a.get('summary'),
                        "recommendations": a.get('recommendations', [])
                    }
                    for a in llm_bias_analyses
                ]
            }
            
            report["llm_bias_detection"] = llm_bias_summary
        
        # Add combined risk assessment
        data_bias_risk = len(violations) > 0
        llm_bias_risk = any(a.get('bias_level') in ['high', 'critical'] for a in (llm_bias_analyses or []))
        
        report["combined_risk_assessment"] = {
            "data_bias_risk": "HIGH" if data_bias_risk else "LOW",
            "llm_output_bias_risk": "HIGH" if llm_bias_risk else "LOW",
            "overall_risk": "HIGH" if (data_bias_risk or llm_bias_risk) else "LOW",
            "requires_immediate_action": data_bias_risk or llm_bias_risk
        }
        
        return report


def generate_report_pdf(destination: Path, title: str, summary: str) -> Path:
    """Legacy compatibility function."""
    generator = ComplianceReportGenerator()
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        doc = SimpleDocTemplate(str(destination), pagesize=letter)
        story = []
        
        story.append(Paragraph(title, generator.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        for line in summary.split("\n"):
            if line.strip():
                story.append(Paragraph(line, generator.styles['Normal']))
        
        doc.build(story)
        return destination
    except Exception as e:
        logger.error(f"Legacy PDF generation failed: {e}")
        raise ReportGenerationError(f"Failed to generate PDF: {str(e)}")
