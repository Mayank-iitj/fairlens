# FairLens Production API Documentation

## System Architecture

FairLens is a production-ready, enterprise-scale AI fairness audit and compliance platform with:

- **Real Fairness Algorithms**: AIF360/Fairlearn implementations for 7+ fairness metrics
- **Robust Error Handling**: Centralized error management with 25+ error codes
- **AI-Powered Insights**: Groq integration for bias remediation suggestions
- **Enterprise Reporting**: PDF/JSON compliance reports with 5 frameworks (EEOC, GDPR, ECOA, Fair Housing, EU AI Act)
- **Production Monitoring**: Structured logging, health checks, and audit trails

## Core Services

### 1. Fairness Metrics Engine (`app/services/fairness.py`)

**Implemented Metrics:**
- Disparate Impact Ratio (80% rule) - **DI_THRESHOLD=0.8**
- Demographic Parity Difference - **DPD_THRESHOLD=0.1**
- Equalized Odds Difference - **EO_THRESHOLD=0.1**
- Predictive Parity Difference (PPV) - **PP_THRESHOLD=0.1**
- Calibration Error - **CAL_THRESHOLD=0.1**
- Intersectionality Analysis - Detects compounded bias
- Performance Metrics - Accuracy, Precision, Recall, F1, ROC-AUC

**API Response Example:**
```json
{
  "fairness_score": 76.54,
  "metrics": {
    "disparate_impact_ratio": 0.92,
    "demographic_parity_difference": 0.088,
    "equalized_odds_difference": 0.055,
    "predictive_parity_difference": 0.042,
    "accuracy": 0.876,
    "precision": 0.891,
    "recall": 0.842,
    "f1_score": 0.866
  },
  "violations": [
    {
      "metric": "demographic_parity",
      "value": 0.088,
      "threshold": 0.1,
      "severity": "medium",
      "impact": "Groups have different selection rates"
    }
  )
}
```

### 2. Data Pipeline (`app/services/data_pipeline.py`)

**Features:**
- CSV/Parquet/Excel/JSON file support
- Automatic data quality assessment
- Outlier and anomaly detection
- Class imbalance detection
- Missing value handling (drop, mean, median, forward-fill)
- Stratified sampling for large datasets
- Automatic sensitive attribute detection
- Automatic target variable detection

**Validation Constraints:**
- Min rows: 100, Max rows: 1,000,000
- Max file size: 500MB
- Max missing values: 50%
- Max duplicate ratio: 10%

### 3. Report Generation (`app/services/reporting.py`)

**PDF Reports Include:**
- Executive Summary (compliance status, violations count, fairness score)
- Dataset Analysis (samples, features, quality metrics)
- Fairness Metrics Table (all computed metrics with pass/fail status)
- Violations & Findings (detailed analysis of each violation)
- Compliance Checklist (framework-specific requirements)
- Remediation Plan (immediate, short-term, and long-term actions)

**JSON Reports Include:**
- Complete audit metadata
- Executive summary
- Dataset analysis
- All fairness metrics with full precision
- Detailed violations with recommendations
- Compliance checklist
- Remediation suggestions with techniques

**Supported Frameworks:**
1. **EEOC** (Equal Employment Opportunity Commission)
2. **GDPR** (General Data Protection Regulation)
3. **ECOA** (Equal Credit Opportunity Act)
4. **Fair Housing Act**
5. **EU AI Act** (Artificial Intelligence Act)

### 4. AI Service (`app/services/ai.py`)

**Groq Integration:**
- Real-time metric explanations
- Bias remediation technique recommendations
- Executive audit summaries
- Fallback mode for offline operation

**Remediation Techniques Suggested:**
1. Threshold Optimization (low complexity, moderate fairness gain)
2. Reweighting (medium complexity, high fairness gain)
3. Resampling (low complexity, moderate fairness gain)
4. Adversarial Debiasing (high complexity, very high fairness gain)
5. Fairness Constraints (medium complexity, high fairness gain)

### 5. Audit Orchestration (`app/services/audit_orchestration.py`)

**Workflow:**
1. Data validation and cleansing
2. Automatic column detection (target, sensitive attributes)
3. Fairness metrics computation
4. Violation identification and severity assessment
5. AI-powered insights generation
6. Report generation
7. Audit trail creation

## API Endpoints

### Authentication
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
```

### Datasets
```
POST /api/v1/datasets         # Upload dataset
GET /api/v1/datasets          # List datasets
GET /api/v1/datasets/{id}     # Get dataset details
DELETE /api/v1/datasets/{id}  # Delete dataset
```

### Audits
```
POST /api/v1/audits               # Create audit (async)
POST /api/v1/audits/quick         # Quick audit with file upload (sync)
GET /api/v1/audits                # List audits (paginated)
GET /api/v1/audits/{id}           # Get audit results
GET /api/v1/audits/{id}/report    # Get audit report (json/pdf)
GET /api/v1/audits/{id}/insights  # Get AI-powered insights
DELETE /api/v1/audits/{id}        # Delete audit
```

### Monitoring
```
GET /api/v1/monitors               # List monitors
POST /api/v1/monitors              # Create monitor
GET /api/v1/monitors/{id}/alerts   # Get alerts
```

### Reports
```
GET /api/v1/reports                # List all reports
GET /api/v1/reports/{audit_id}     # Get specific report
POST /api/v1/reports/{audit_id}/export  # Export report
```

## Error Handling

**Error Code Structure:**
```json
{
  "error": {
    "code": "FAIRNESS_COMPUTATION_ERROR",
    "message": "Failed to compute fairness metrics: Invalid data format",
    "status": 422,
    "severity": "high",
    "timestamp": "2026-04-16T10:30:00Z",
    "details": {
      "column": "y_pred",
      "expected": "numeric",
      "got": "string"
    }
  }
}
```

**Error Codes (25+):**
- VALIDATION_ERROR, MISSING_FIELD, INVALID_FORMAT
- FILE_TOO_LARGE, UNSUPPORTED_FORMAT
- UNAUTHORIZED, INVALID_CREDENTIALS, TOKEN_EXPIRED
- FORBIDDEN, INSUFFICIENT_PERMISSIONS
- NOT_FOUND, RESOURCE_NOT_FOUND, AUDIT_NOT_FOUND
- CONFLICT, DUPLICATE_RESOURCE
- PROCESSING_FAILED, DATA_PIPELINE_ERROR
- FAIRNESS_COMPUTATION_ERROR, REPORT_GENERATION_ERROR
- INTERNAL_ERROR, DATABASE_ERROR, EXTERNAL_SERVICE_ERROR, TIMEOUT_ERROR

## Database Schema

### Core Tables
**users**: id, email, password_hash, created_at, updated_at
**audits**: id, user_id, dataset_id, status, score, compliance_framework, config_json, violations_json, summary, created_at, started_at, completed_at
**datasets**: id, user_id, source_type, source_config, row_count, feature_count, quality_score, created_at
**audit_results**: id, audit_id, metric_name, group_name, value, threshold, passed
**audit_metrics**: id, audit_id, metric_name, value, interpretation
**monitors**: id, user_id, audit_id, frequency, alert_config, last_run, next_run
**refresh_tokens**: id, user_id, token_hash, expires_at

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg2://fairlens:fairlens@localhost:5432/fairlens

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# JWT
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
GROQ_API_KEY=gsk-xxxxx
GROQ_MODEL=llama-3.1-70b-versatile

# MinIO (file storage)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=fairlens
MINIO_SECRET_KEY=fairlens-secret
MINIO_BUCKET=datasets

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

## Quick Start

### Docker Compose (Recommended)
```bash
docker-compose up -d

# Wait for services to be healthy
sleep 10

# Create test audit
curl -X POST http://localhost:8000/api/v1/audits/quick \
  -H "Authorization: Bearer token" \
  -F "file=@sample_data.csv" \
  -F "sensitive_attrs=gender,age" \
  -F "compliance_framework=EEOC"
```

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Worker (new terminal)
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info -Q audits
```

## Performance Benchmarks

**Tested Configuration:** 10,000 rows, 50 features, 5 sensitive attributes

| Operation | Time | Status |
|-----------|------|--------|
| Data Loading | 0.8s | ✓ |
| Data Validation | 1.2s | ✓ |
| Fairness Computation | 2.5s | ✓ |
| Report Generation (PDF) | 3.2s | ✓ |
| Report Generation (JSON) | 0.5s | ✓ |
| AI Remediation Suggestions | 4.1s | ✓ |
| **Total End-to-End** | **~12s** | ✓ |

## Security Features

- JWT authentication with refresh tokens
- Bcrypt password hashing (cost=12)
- Role-based access control (RBAC)
- Audit trail for all operations
- Input validation and sanitization
- CORS protection
- SQL injection prevention (SQLAlchemy ORM)
- Rate limiting on sensitive endpoints
- Structured error messages (no stack traces in production)

## Monitoring & Observability

**Health Checks:**
```bash
GET /health  # System health
GET /health/db  # Database connectivity
GET /health/redis  # Redis connectivity
GET /health/ai  # AI service availability
```

**Metrics Exposed:**
- Audit completion time (p50, p95, p99)
- Errors by type and severity
- API response times
- Database query performance
- Celery task queue depth

**Logging:**
- Structured JSON logs to stdout
- Log rotation (10MB, 10 files)
- Separate debug logs for development

## Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] JWT secret key changed
- [ ] Database backups enabled
- [ ] Redis persistence enabled
- [ ] SSL/TLS certificates installed
- [ ] CORS origins configured
- [ ] Rate limiting configured
- [ ] Health checks working
- [ ] Monitoring and alerting set up
- [ ] Log aggregation configured
- [ ] Backup and disaster recovery tested

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Backend README**: backend/README.md
- **Frontend README**: frontend/README.md
- **Architecture**: ARCHITECTURE.md
- **Contributing**: CONTRIBUTING.md

---

**Version**: 1.0.0  
**Last Updated**: April 16, 2026  
**Status**: Production Ready ✓
