# Enhanced Report Generation - Deployment & Integration Guide

## Phase 2 Implementation Summary

This document outlines the enhanced PDF/JSON report generation features that integrate LLM bias detection with existing compliance auditing.

### What's New

#### Core Enhancements
1. **Executive Summary Enhancement**: Now includes LLM bias status alongside data fairness compliance
2. **LLM Bias PDF Section**: Dedicated section in PDF reports showing LLM output bias analysis
3. **Comprehensive Recommendations**: Single unified recommendation section combining data bias and LLM bias findings
4. **Enhanced JSON Reports**: Extended JSON structure with LLM analysis and combined risk assessment
5. **API Endpoints**: New `/reports` endpoints for comprehensive report generation

#### Key Features
- ✅ PDF reports with integrated LLM bias analysis
- ✅ Executive summary showing both data and LLM bias status
- ✅ Detailed LLM bias findings with visual organization
- ✅ Combined risk assessment (data + LLM)
- ✅ Prioritized recommendations with timeline
- ✅ JSON reports with comprehensive metadata
- ✅ Backward compatibility (LLM parameter optional)

## Architecture

### New API Endpoints

```
POST   /api/v1/reports/generate-comprehensive
GET    /api/v1/reports/{audit_id}/report/pdf
GET    /api/v1/reports/{audit_id}/report/json
POST   /api/v1/reports/{audit_id}/report/regenerate
GET    /api/v1/reports
```

### Modified Components

**backend/app/services/reporting.py**
- Modified `generate_pdf_report()` - now accepts optional `llm_bias_analyses` parameter
- Modified `_build_executive_summary()` - includes LLM bias status
- Modified `generate_json_report()` - accepts optional `llm_bias_analyses` parameter
- Added `_build_llm_bias_section()` - renders LLM findings in PDF
- Added `_build_comprehensive_recommendations()` - combines both biases
- Added `generate_json_report_with_llm()` - enhanced JSON with LLM data

**backend/app/api/v1/router.py**
- Added import for reports module
- Registered `/reports` router

### Database Integration

The implementation works with existing database models:
- `Audit` - existing audit records
- `AuditResult` - existing fairness metrics
- `LLMBiasAnalysis` - LLM bias detection results (created in Phase 1)
- `Report` - stores report metadata

## Deployment Steps

### 1. Pre-Deployment Validation

```bash
# Check Python syntax
python -m py_compile backend/app/services/reporting.py
python -m py_compile backend/app/api/v1/reports.py

# Run lint checks
pylint backend/app/services/reporting.py
pylint backend/app/api/v1/reports.py

# Check imports
python -c "from app.services.reporting import ComplianceReportGenerator"
python -c "from app.api.v1 import reports"
```

### 2. Database Preparation

No new database migrations required - Phase 1 LLM tables already exist.

```bash
# Verify Phase 1 migration was applied
cd backend
alembic current
# Expected: 0002_llm_bias.py

# If not applied:
alembic upgrade head
```

### 3. Application Deployment

```bash
# Update requirements.txt (if new dependencies needed)
pip install -r backend/requirements.txt

# Restart application
docker-compose restart backend

# Or if running directly:
python backend/app/main.py
```

### 4. Verification

```bash
# Test health check
curl http://localhost:8001/health

# Test authentication
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Test report endpoints
curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"audit_id": "audit-123", "compliance_framework": "EEOC", "include_llm_bias": true}'
```

## Testing & Validation

### Unit Tests

Run enhanced reporting tests:

```bash
cd backend
pytest tests/test_enhanced_reporting.py -v

# Run specific test
pytest tests/test_enhanced_reporting.py::TestReportGeneration::test_generate_pdf_with_llm_bias -v
```

### Integration Tests

```bash
# Test complete workflow
pytest tests/test_enhanced_reporting.py::TestReportAPI -v

# Test with database
pytest tests/test_enhanced_reporting.py -v --db-url="postgresql://user:pass@localhost/fairlens_test"
```

### Manual Testing

#### Scenario 1: Generate Report Without LLM Bias
```bash
curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "audit-001",
    "compliance_framework": "EEOC",
    "include_llm_bias": false
  }'
```

Expected: Report generated with data bias only

#### Scenario 2: Generate Report With LLM Bias
```bash
curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "audit-001",
    "compliance_framework": "EEOC",
    "include_llm_bias": true,
    "llm_bias_analysis_ids": ["analysis-1", "analysis-2"]
  }'
```

Expected: Report with both data bias and LLM analysis sections

#### Scenario 3: Download PDF Report
```bash
curl -X GET http://localhost:8001/api/v1/reports/audit-001/report/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o audit_report.pdf
```

Expected: PDF file downloaded successfully

#### Scenario 4: Get JSON Report
```bash
curl -X GET http://localhost:8001/api/v1/reports/audit-001/report/json \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

Expected: Complete JSON report with all sections

#### Scenario 5: List All Reports
```bash
curl -X GET "http://localhost:8001/api/v1/reports?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

Expected: List of recent reports

### Edge Cases to Test

| Scenario | Test Case | Expected Result |
|----------|-----------|-----------------|
| No audit results | Generate report for new audit | Should handle gracefully |
| No LLM analyses | include_llm_bias=true but no data | Report without LLM section |
| Large number of analyses | 50+ LLM analyses | First 10 shown, overflow indicated |
| Large file | 1000+ results | PDF <10MB, JSON <5MB |
| Concurrent requests | Multiple report generations | No race conditions |
| Invalid audit ID | Non-existent audit | 404 error returned |
| Unauthorized access | No token | 401 error returned |

## Performance Monitoring

### Key Metrics

```bash
# Report generation time (should be <3 seconds)
curl -w "@curl-format.txt" \
  -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audit_id": "audit-001", "compliance_framework": "EEOC"}'

# Monitor disk usage
du -sh /reports/  # Should be <100GB for most deployments

# Check log output
docker logs -f fairlens-backend | grep -i "report"
```

### Optimization Tips

1. **Async Generation**: For large audits, consider async report generation with webhooks
2. **Caching**: Cache frequently generated reports
3. **Compression**: Compress old PDFs to save storage
4. **Pagination**: Limit number of LLM analyses per report (default 10)

## Troubleshooting

### Issue: Import Error for reports module

**Symptom**: `ModuleNotFoundError: No module named 'app.api.v1.reports'`

**Solution**:
1. Verify `backend/app/api/v1/reports.py` exists
2. Check `backend/app/api/v1/router.py` has `from app.api.v1 import reports`
3. Restart application

### Issue: Report PDF not created

**Symptom**: `"pdf_path": null` in response

**Solution**:
1. Check `/reports` directory exists and is writable
2. Verify ReportLab is installed: `pip list | grep reportlab`
3. Check disk space: `df -h /`
4. Review logs for errors: `docker logs fairlens-backend`

### Issue: LLM section not appearing in PDF

**Symptom**: PDF generated but no LLM analysis section

**Solution**:
1. Verify `include_llm_bias: true` in request
2. Check LLM analyses exist in database: 
   ```sql
   SELECT COUNT(*) FROM llm_bias_analysis WHERE user_id = 'user-id';
   ```
3. Verify analyses have data: `SELECT * FROM llm_bias_analysis LIMIT 1;`

### Issue: Timeout generating report

**Symptom**: Request times out after 30 seconds

**Solution**:
1. Reduce number of LLM analyses: `llm_bias_analysis_ids` to top 5
2. Increase timeout in application config
3. Use async generation for large reports
4. Check database performance: `EXPLAIN ANALYZE`

## Rollback Procedure

If issues arise post-deployment:

```bash
# Option 1: Revert application (no database changes needed)
git revert <commit-hash>
docker-compose rebuild backend
docker-compose up -d

# Option 2: Disable LLM features temporarily
# Set include_llm_bias=false in all report requests

# Option 3: Use previous application version
docker-compose down
docker pull fairlens-backend:previous-version
docker-compose up -d

# No database rollback needed - only application code changed
```

## Post-Deployment Checklist

- [ ] All tests pass
- [ ] API endpoints responding correctly
- [ ] PDF reports generating successfully
- [ ] JSON reports complete and valid
- [ ] LLM bias section appears in PDFs
- [ ] Report storage working
- [ ] No errors in logs
- [ ] Performance acceptable (<3 sec per report)
- [ ] Backward compatibility verified (reports without LLM work)
- [ ] User documentation updated
- [ ] Production data backed up
- [ ] Monitoring/alerts configured

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8001/api/v1"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Generate comprehensive report
response = requests.post(
    f"{BASE_URL}/reports/generate-comprehensive",
    json={
        "audit_id": "audit-123",
        "compliance_framework": "EEOC",
        "include_llm_bias": True
    },
    headers=headers
)

report = response.json()
print(f"Report ID: {report['report_id']}")
print(f"Status: {report['status']}")

# Download PDF
pdf_response = requests.get(
    f"{BASE_URL}/reports/audit-123/report/pdf",
    headers=headers
)

with open("report.pdf", "wb") as f:
    f.write(pdf_response.content)

# Get JSON report
json_response = requests.get(
    f"{BASE_URL}/reports/audit-123/report/json",
    headers=headers
)

json_report = json_response.json()
print(json.dumps(json_report, indent=2))
```

### Frontend Integration Example

```typescript
// React component to display and download reports
const generateReport = async (auditId: string) => {
  const response = await api.post('/reports/generate-comprehensive', {
    audit_id: auditId,
    compliance_framework: 'EEOC',
    include_llm_bias: true
  });
  
  const report = response.data;
  
  // Download PDF
  const pdfResponse = await api.get(
    `/reports/${auditId}/report/pdf`,
    { responseType: 'blob' }
  );
  
  const url = window.URL.createObjectURL(new Blob([pdfResponse.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `audit_${auditId}_report.pdf`);
  document.body.appendChild(link);
  link.click();
};
```

## Monitoring & Maintenance

### Log Monitoring

```bash
# Watch for report generation errors
docker logs -f fairlens-backend | grep -i "report\|error"

# Archive old logs
find /var/log/fairlens -name "*.log" -mtime +30 -exec gzip {} \;
```

### Database Maintenance

```bash
# Vacuum and analyze report tables
VACUUM ANALYZE audit;
VACUUM ANALYZE audit_result;
VACUUM ANALYZE report;
VACUUM ANALYZE llm_bias_analysis;

# Check for bloated tables
SELECT * FROM pg_stat_user_tables WHERE n_live_tup > 1000000;
```

### Regular Tasks

- [ ] Weekly: Review error logs for report generation issues
- [ ] Monthly: Archive old reports (>90 days)
- [ ] Quarterly: Analyze report generation performance
- [ ] Annually: Upgrade dependencies and test compatibility

## Support & Documentation

- **Bug Reports**: Create GitHub issue with logs and error details
- **Feature Requests**: Post in discussions with use case
- **Documentation**: See [ENHANCED_REPORT_GENERATION.md](ENHANCED_REPORT_GENERATION.md)
- **API Docs**: See Swagger UI at `/docs`

---

**Status**: Production Ready ✅
**Last Updated**: April 2026
**Next Review**: July 2026
