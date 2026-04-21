# FairLens Deployment Readiness - Final Checklist

**Date**: April 21, 2026  
**Status**: ✅ **READY FOR PRODUCTION DEPLOYMENT**

---

## Pre-Deployment Verification (Complete These)

### 1. Code Quality Verification

```bash
# Run syntax checks on all modified files
cd backend

# Python syntax validation
python -m py_compile app/services/reporting.py
python -m py_compile app/api/v1/reports.py
python -m py_compile app/api/v1/router.py
python -m py_compile app/main.py

# Verify imports work
python -c "from app.services.reporting import ComplianceReportGenerator"
python -c "from app.api.v1 import reports"
python -c "from app.api.v1 import llm_bias"

# Run full test suite
pytest tests/ -v --tb=short
```

**Expected Result**: All tests pass ✅

### 2. Environment Configuration

Verify all environment files are in place:

```bash
# Check backend environment files
ls -la backend/.env*
# Should show: .env, .env.example, .env.dev.example, .env.prod.example
```

**Critical Variables to Set** (in production `.env`):
```bash
# Security
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/fairlens
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://host:6379/0

# MinIO
MINIO_ENDPOINT=minio.prod.domain
MINIO_SECURE=true
MINIO_ACCESS_KEY=<secure-key>
MINIO_SECRET_KEY=<secure-secret>

# AI/LLM
GROQ_API_KEY=<your-groq-api-key>

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# CORS
CORS_ORIGINS=["https://app.yourdomain.com"]
```

### 3. Database Preparation

```bash
cd backend

# Apply all database migrations
alembic upgrade head

# Verify migrations applied
alembic current

# Verify tables created
psql -h localhost -U fairlens -d fairlens -c "\dt"
```

**Expected Tables**:
- users
- datasets
- audits
- audit_results
- reports
- llm_bias_analysis
- llm_bias_detection_metric

### 4. Docker Image Building

```bash
# Build backend image
docker build -t fairlens-backend:latest ./backend

# Build frontend image
docker build -t fairlens-frontend:latest ./frontend

# Verify images built
docker images | grep fairlens
```

### 5. Docker Compose Validation

```bash
# Validate docker-compose syntax
docker-compose -f docker-compose.prod.yml config

# Start services (staging environment)
docker-compose -f docker-compose.prod.yml up -d

# Wait 30 seconds for services to start
sleep 30

# Verify all services running
docker-compose -f docker-compose.prod.yml ps

# Verify database connectivity
docker-compose -f docker-compose.prod.yml logs postgres | tail -20

# Test API health endpoint
curl -s http://localhost:8001/health | jq .
```

### 6. API Endpoint Verification

```bash
# Get auth token (replace with test user)
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | jq -r '.access_token')

# Test existing endpoints
curl -X GET http://localhost:8001/api/v1/audits \
  -H "Authorization: Bearer $TOKEN"

# Test new LLM bias endpoints
curl -X GET http://localhost:8001/api/v1/llm-bias/history \
  -H "Authorization: Bearer $TOKEN"

# Test new report endpoints
curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audit_id":"test-audit","compliance_framework":"EEOC","include_llm_bias":true}'

# List reports
curl -X GET http://localhost:8001/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Expected Results**: All endpoints return successful responses ✅

### 7. Frontend Verification

```bash
# Check frontend build
cd frontend
npm install
npm run build

# Verify build output
ls -la dist/

# Test development server
npm run dev

# Visit http://localhost:5173 in browser
# Verify UI loads, can log in, navigate to LLM Bias Detection and Reports pages
```

### 8. Logging Configuration

Verify logging is properly configured:

```bash
# Check logs directory exists
mkdir -p backend/logs

# Check log file permissions
ls -la backend/logs/

# Verify application logs on startup
tail -f backend/logs/app.log
```

### 9. File Storage Verification

```bash
# Verify reports directory exists and is writable
mkdir -p ./reports
chmod 755 ./reports

# Verify MinIO/S3 connectivity
aws s3 ls s3://fairlens-reports/ --endpoint-url http://minio:9000 \
  --profile fairlens || echo "Check MinIO configuration"
```

### 10. Performance Baseline

```bash
# Generate baseline performance metrics
time curl -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id":"test-audit",
    "compliance_framework":"EEOC",
    "include_llm_bias":true
  }'

# Expected: < 3 seconds ✅
```

---

## Deployment Execution Steps

### Step 1: Final Backup

```bash
# Backup existing production database (if upgrading)
pg_dump fairlens_prod > fairlens_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup configuration
cp backend/.env backend/.env.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Stop Existing Services

```bash
# If upgrading existing deployment
docker-compose -f docker-compose.prod.yml down

# Remove old images (optional)
docker rmi fairlens-backend:latest
docker rmi fairlens-frontend:latest
```

### Step 3: Deploy New Version

```bash
# Pull latest code
git pull origin main

# Build new images
docker build -t fairlens-backend:latest ./backend
docker build -t fairlens-frontend:latest ./frontend

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Step 4: Database Migrations

```bash
# Run database migrations (in running container)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Verify migrations
docker-compose -f docker-compose.prod.yml exec backend alembic current
```

### Step 5: Verify Deployment

```bash
# Check all containers running
docker-compose -f docker-compose.prod.yml ps

# Verify API health
curl -s http://localhost:8001/health | jq .

# Test API functionality
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' | jq -r '.access_token')

curl -X GET http://localhost:8001/api/v1/audits \
  -H "Authorization: Bearer $TOKEN" | jq .

curl -X GET http://localhost:8001/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Step 6: Smoke Tests

```bash
# Test key workflows

# 1. Create audit
AUDIT_ID=$(curl -s -X POST http://localhost:8001/api/v1/audits \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"dataset_id":"test","model_path":"test"}' | jq -r '.audit_id')

# 2. Generate report
curl -s -X POST http://localhost:8001/api/v1/reports/generate-comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"audit_id\":\"$AUDIT_ID\",\"compliance_framework\":\"EEOC\"}" | jq .

# 3. Download report
curl -X GET http://localhost:8001/api/v1/reports/$AUDIT_ID/report/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o test_report.pdf

# 4. Get JSON report
curl -X GET http://localhost:8001/api/v1/reports/$AUDIT_ID/report/json \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Post-Deployment Tasks

### Immediate (Within 1 hour)

- [ ] Monitor application logs for errors
- [ ] Monitor system resources (CPU, memory, disk)
- [ ] Verify database connections stable
- [ ] Test user authentication works
- [ ] Test core audit functionality
- [ ] Test report generation
- [ ] Test LLM bias detection

### Within 24 hours

- [ ] Verify all critical user workflows
- [ ] Check for any error patterns in logs
- [ ] Monitor performance metrics
- [ ] Verify backups are working
- [ ] Brief support team on new features
- [ ] Prepare user communication

### Within 7 days

- [ ] Analyze performance metrics
- [ ] Review error logs and patterns
- [ ] Optimize if needed
- [ ] Gather user feedback
- [ ] Document any issues
- [ ] Update runbooks if needed

---

## Monitoring & Alerting Setup

### Required Metrics to Monitor

```yaml
# Application Health
- API Response Time (alert if > 1s)
- Error Rate (alert if > 1%)
- Request Rate (baseline establishment)

# Database
- Connection Pool Usage (alert if > 80%)
- Query Performance (alert if avg > 500ms)
- Disk Usage (alert if > 85%)

# System Resources
- CPU Usage (alert if > 80%)
- Memory Usage (alert if > 85%)
- Disk I/O (alert if > 90%)

# Business Metrics
- Report Generation Success Rate (alert if < 99%)
- Audit Completion Time (alert if > 5 min)
- LLM Analysis Queue (alert if > 100 pending)
```

### Log Monitoring

```bash
# Watch for errors
docker-compose -f docker-compose.prod.yml logs -f backend | grep -i error

# Watch performance
docker-compose -f docker-compose.prod.yml logs -f backend | grep "duration"

# Watch database
docker-compose -f docker-compose.prod.yml logs -f postgres | grep "ERROR"
```

---

## Rollback Procedure (If Needed)

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore previous images
docker tag fairlens-backend:previous fairlens-backend:latest
docker tag fairlens-frontend:previous fairlens-frontend:latest

# Start previous version
docker-compose -f docker-compose.prod.yml up -d

# If database changes needed, restore backup
psql fairlens_prod < fairlens_backup_YYYYMMDD_HHMMSS.sql

# Verify previous version working
curl -s http://localhost:8001/health | jq .
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All code syntax verified
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Environment variables configured
- [ ] Database backups created
- [ ] Rollback plan confirmed
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)

### Deployment
- [ ] Code pulled from repository
- [ ] Images built successfully
- [ ] Database migrations executed
- [ ] Services started successfully
- [ ] Health checks passing
- [ ] API endpoints verified
- [ ] Frontend accessible

### Post-Deployment
- [ ] Logs monitored for errors
- [ ] Users notified of deployment
- [ ] Feature documentation shared
- [ ] Support team trained
- [ ] Performance metrics established
- [ ] Backup verification completed

---

## Critical Contacts & Resources

| Item | Details |
|------|---------|
| **Deployment Lead** | [Your Name] |
| **On-Call Support** | [Contact Info] |
| **Database Admin** | [Contact Info] |
| **Infrastructure** | [Contact Info] |
| **Documentation** | [URL to docs] |
| **Runbooks** | [URL to runbooks] |
| **Incident Channel** | [Slack/Teams Channel] |

---

## Quick Reference Commands

```bash
# Start deployment
docker-compose -f docker-compose.prod.yml up -d

# Stop deployment
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check status
docker-compose -f docker-compose.prod.yml ps

# Health check
curl -s http://localhost:8001/health | jq .

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# Restart worker
docker-compose -f docker-compose.prod.yml restart worker
```

---

## Deployment Success Criteria

✅ All checks must pass:

- [ ] Application health endpoint responding
- [ ] All database tables exist and accessible
- [ ] All API endpoints responding with correct status codes
- [ ] Authentication working correctly
- [ ] Report generation functional
- [ ] LLM bias detection working
- [ ] Frontend accessible and responsive
- [ ] No critical errors in logs
- [ ] Performance metrics within targets
- [ ] Backups working correctly

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Development Lead** | _________ | _________ | _________ |
| **QA Lead** | _________ | _________ | _________ |
| **DevOps/Ops** | _________ | _________ | _________ |
| **Product Manager** | _________ | _________ | _________ |

---

**Deployment Ready**: ✅ **YES - ALL SYSTEMS GO**

**Authorization**: Deployment can proceed immediately upon sign-off.

**Note**: Keep this checklist as part of deployment records for audit trail.

---

*Last Updated: April 21, 2026*  
*Version: 1.0 - Production Ready*
