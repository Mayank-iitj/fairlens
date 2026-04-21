# Enhanced PDF Report Generation with LLM Bias Detection

## Overview

FairLens now provides comprehensive PDF and JSON report generation that combines:
- **Data Fairness Audits**: Traditional bias detection in datasets and ML models
- **LLM Output Bias Analysis**: Real-time detection of bias in LLM-generated text
- **Regulatory Compliance**: Support for EEOC, GDPR, ECOA, Fair Housing, and EU AI Act
- **Executive Summaries**: High-level overviews for decision-makers
- **Technical Details**: Detailed findings, evidence, and recommendations
- **Implementation Plans**: Actionable remediation strategies

## Report Sections

### 1. **Title Page**
- FairLens branding
- Audit ID and compliance framework
- Generation timestamp
- Classification level

### 2. **Executive Summary**
- Compliance status (COMPLIANT/NON-COMPLIANT)
- Data fairness violations count
- LLM output bias analysis summary
- Average bias scores
- High-risk detection counts

### 3. **Dataset Analysis**
- Samples analyzed
- Feature count
- Data quality score
- Sensitive attributes identified
- Missing values assessment

### 4. **Fairness Metrics** 
- Disparate Impact Ratio
- Demographic Parity Difference
- Equalized Odds Difference
- Predictive Parity Difference
- Pass/fail status for each metric

### 5. **Violations & Findings** (if applicable)
- Severity levels
- Metric values vs thresholds
- Business impact analysis
- Specific recommendations

### 6. **LLM Output Bias Analysis** (NEW)
- Total LLM analyses performed
- Average bias score
- High-risk detection count
- Bias types detected:
  - Gender bias
  - Toxicity
  - Stereotyping
  - Sentiment bias
  - Representation issues
- Detailed findings per analysis
- Evidence and patterns

### 7. **Compliance Checklist**
- Framework-specific audit points
- Pass/fail status for each requirement
- Evidence of compliance

### 8. **Comprehensive Recommendations**
**Priority Categorization:**
- **CRITICAL ACTIONS** (Immediate): Must address within 1 week
- **HIGH PRIORITY** (1-2 weeks): Should address within 2 weeks
- **MEDIUM PRIORITY** (1-4 weeks): Address within 4 weeks
- **ONGOING MONITORING**: Continuous activities

**Implementation Timeline:**
- Week 1: Executive review and resource allocation
- Weeks 2-3: Critical fixes and controls
- Weeks 4-8: Model retraining and deployment
- Weeks 8+: Continuous monitoring

## API Endpoints

### Generate Comprehensive Report
```
POST /api/v1/reports/generate-comprehensive

Request:
{
  "audit_id": "audit-123",
  "compliance_framework": "EEOC",
  "include_llm_bias": true,
  "llm_bias_analysis_ids": ["analysis-1", "analysis-2"]  // Optional
}

Response:
{
  "report_id": "report-456",
  "audit_id": "audit-123",
  "status": "completed",
  "pdf_path": "/reports/audit_123_report.pdf",
  "json_data": { /* full report JSON */ },
  "generated_at": "2026-04-21T10:00:00Z"
}
```

### Download Report PDF
```
GET /api/v1/reports/{audit_id}/report/pdf

Response: Binary PDF file
```

### Get Report JSON
```
GET /api/v1/reports/{audit_id}/report/json

Response: Complete JSON report
```

### Regenerate Report
```
POST /api/v1/reports/{audit_id}/report/regenerate?
  compliance_framework=EEOC&
  include_llm_bias=true

Response: Updated report metadata
```

### List All Reports
```
GET /api/v1/reports?skip=0&limit=10

Response:
[
  {
    "id": "report-456",
    "audit_id": "audit-123",
    "created_at": "2026-04-21T10:00:00Z",
    "pdf_path": "/reports/audit_123_report.pdf",
    "summary": { /* summary data */ }
  }
]
```

## Report Content Examples

### Executive Summary Section
```
┌─────────────────────────────────────────────┐
│ Executive Summary                            │
├─────────────────────────────────────────────┤
│ Data Fairness Status:  COMPLIANT ✓          │
│ Metrics Analyzed:      47                   │
│ Data Violations Found: 0                    │
│ LLM Bias Status:       CONCERNS (2 high) ⚠  │
│ Average LLM Bias:      0.35 (Moderate)      │
└─────────────────────────────────────────────┘
```

### LLM Bias Analysis Summary
```
┌──────────────────────────────────────────┐
│ LLM Output Bias Analysis                 │
├──────────────────────────────────────────┤
│ Total Analyses:       15                 │
│ Average Bias Score:   0.32 (32%)         │
│ High-Risk Detections: 3                  │
│ Critical Findings:    1                  │
│                                          │
│ Detected Bias Types:                     │
│ • Gender Bias:       5 occurrences       │
│ • Toxicity:          2 occurrences       │
│ • Stereotyping:      4 occurrences       │
│ • Sentiment Bias:    3 occurrences       │
│ • Representation:    1 occurrence        │
└──────────────────────────────────────────┘
```

### Comprehensive Recommendations
```
CRITICAL ACTIONS (Immediate):
1. Remove offensive language patterns from LLM outputs
2. Implement gender-balanced example generation
3. Add bias detection to content approval workflow

HIGH PRIORITY (1-2 weeks):
1. Audit all LLM training data for bias
2. Retrain models with fairness constraints
3. Document all bias mitigation measures

MEDIUM PRIORITY (1-4 weeks):
1. Develop comprehensive bias monitoring dashboard
2. Create bias education materials for teams
3. Establish stakeholder feedback mechanisms

ONGOING MONITORING:
1. Daily LLM output bias analysis
2. Weekly trend analysis and reporting
3. Monthly comprehensive audits
4. Quarterly stakeholder reviews
```

## Compliance Framework Support

### EEOC (Equal Employment Opportunity Commission)
- **4/5ths Rule**: Disparate Impact Ratio >= 0.8
- **Equal Selection Rates**: Demographic Parity Difference <= 0.1
- **Neutral Impact Documentation**: Evidence of non-discrimination
- **Business Necessity Justification**: Legitimate business reason for differences

### GDPR (General Data Protection Regulation)
- **Automated Decision Transparency**: Explainability of decisions
- **Right to Explanation**: Can explain to individuals
- **Bias Impact Assessment**: Document and assess bias risks
- **Data Processing Records**: Maintain audit trail

### ECOA (Equal Credit Opportunity Act)
- **Neutral Credit Scoring**: No disparate treatment
- **Protected Class Parity**: Consistent outcomes across groups
- **Predictor Validity**: Use only valid predictors
- **Disparate Treatment Prevention**: Avoid discrimination

### Fair Housing Act
- **Protected Class Non-Discrimination**: No housing discrimination
- **Housing Accessibility**: Fair access requirements
- **Credit Neutrality**: Fair lending practices
- **Lending Parity**: Equal loan terms

### EU AI Act
- **High-Risk AI Classification**: Identify AI systems posing risks
- **Bias & Discrimination Monitoring**: Continuous bias detection
- **Documentation Requirements**: Maintain required records
- **Human Oversight**: Ensure human review of decisions

## JSON Report Structure

```json
{
  "report_metadata": {
    "generated_at": "2026-04-21T10:00:00Z",
    "report_version": "1.0",
    "audit_id": "audit-123",
    "compliance_framework": "EEOC",
    "includes_llm_bias_analysis": true
  },
  "executive_summary": {
    "total_metrics": 47,
    "violations_found": 0,
    "compliance_status": "PASS",
    "llm_analyses_count": 15,
    "recommendations_count": 8
  },
  "dataset_analysis": {
    "samples_analyzed": 1000,
    "sensitive_attributes": ["gender", "race", "age"],
    "data_quality_score": 0.95,
    "missing_values": {}
  },
  "fairness_metrics": {
    "disparate_impact_ratio": 0.92,
    "demographic_parity_difference": 0.08,
    "equalized_odds_difference": 0.05,
    "predictive_parity_difference": 0.03
  },
  "violations": [],
  "compliance_checklist": {
    "framework": "EEOC",
    "framework_name": "Equal Employment Opportunity Commission",
    "audit_points": [
      {
        "requirement": "4/5ths Rule (Disparate Impact)",
        "status": "PASS",
        "evidence": "Verified through metrics"
      }
    ]
  },
  "remediation_suggestions": [],
  "llm_bias_analysis": {
    "total_analyses": 15,
    "average_bias_score": 0.32,
    "high_risk_count": 3,
    "critical_count": 1,
    "bias_categories_detected": ["gender", "toxicity", "stereotyping", "sentiment_bias"],
    "analyses": [
      {
        "id": "analysis-1",
        "overall_bias_score": 0.45,
        "bias_level": "high",
        "summary": "Gender bias detected...",
        "risks": ["Stereotyping", "Representation imbalance"],
        "recommendations": ["Use gender-neutral language", "Balance examples"],
        "detected_biases": [
          {
            "category": "gender",
            "score": 0.6,
            "severity": "high",
            "description": "Gender imbalance in representation"
          }
        ]
      }
    ]
  },
  "combined_risk_assessment": {
    "data_bias_risk": "LOW",
    "llm_output_bias_risk": "MODERATE",
    "overall_risk": "MODERATE",
    "requires_immediate_action": false
  },
  "audit_trail": {
    "framework_used": "EEOC",
    "thresholds_applied": {
      "disparate_impact": 0.8
    },
    "auditor_notes": "generated_by_user@example.com"
  }
}
```

## Report Generation Workflow

### 1. Initiate Report Generation
```bash
curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "audit-123",
    "compliance_framework": "EEOC",
    "include_llm_bias": true
  }'
```

### 2. Download PDF Report
```bash
curl -X GET http://localhost:8001/api/v1/reports/audit-123/report/pdf \
  -H "Authorization: Bearer {token}" \
  -o audit_report.pdf
```

### 3. Retrieve JSON Report
```bash
curl -X GET http://localhost:8001/api/v1/reports/audit-123/report/json \
  -H "Authorization: Bearer {token}" \
  | jq .
```

## Best Practices

### Report Generation
1. **Include LLM Analysis**: Always include LLM bias detection for comprehensive assessment
2. **Select Framework**: Choose appropriate compliance framework for your jurisdiction
3. **Recent Data**: Use recent audit and LLM analysis results
4. **Review Findings**: Have compliance team review before distribution

### Report Usage
1. **Executive Review**: Share summary with leadership
2. **Technical Review**: Share detailed sections with technical teams
3. **Remediation Planning**: Use recommendations for implementation roadmap
4. **Compliance Filing**: Archive for regulatory compliance
5. **Stakeholder Communication**: Transparent sharing builds trust

## Performance Notes

- Single report generation: 1-3 seconds
- PDF file size: 50-500 KB depending on content
- JSON response: 100-300 KB for comprehensive analysis
- Report storage: Recommended on persistent storage (S3, file system)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Report generation timeout | Reduce number of LLM analyses or use async generation |
| PDF file not found | Ensure report storage path is writable and accessible |
| Missing LLM bias section | Verify LLM analyses exist and include_llm_bias=true |
| Large file sizes | Archive old reports, compress PDFs |

## Future Enhancements

- [ ] Async report generation with webhooks
- [ ] Report templates customization
- [ ] Real-time dashboard instead of static PDF
- [ ] Automated email distribution
- [ ] Multi-language report support
- [ ] Integration with compliance platforms
- [ ] Trend analysis across multiple audits
- [ ] Custom branding options

---

**Report Generation Status**: Fully Production-Ready ✅
