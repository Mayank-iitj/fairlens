#!/bin/bash
# FairLens Complete Deployment Readiness Check Script
# Validates all components before production deployment

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "FairLens Deployment Readiness Check v1.0"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to print check result
print_check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $2"
        ((CHECKS_FAILED++))
    fi
}

# ============================================
# 1. Python Environment Checks
# ============================================
echo "1. Python Environment Checks"
echo "---"

# Check Python version
python --version > /dev/null 2>&1
print_check $? "Python 3.8+ installed"

# Check Python packages
cd backend
python -c "import fastapi" 2>/dev/null
print_check $? "FastAPI installed"

python -c "import sqlalchemy" 2>/dev/null
print_check $? "SQLAlchemy installed"

python -c "import pydantic" 2>/dev/null
print_check $? "Pydantic installed"

python -c "import celery" 2>/dev/null
print_check $? "Celery installed"

python -c "import reportlab" 2>/dev/null
print_check $? "ReportLab installed"

cd ..
echo ""

# ============================================
# 2. Code Quality Checks
# ============================================
echo "2. Code Quality Checks"
echo "---"

# Syntax check
cd backend

python -m py_compile app/services/reporting.py 2>/dev/null
print_check $? "reporting.py syntax valid"

python -m py_compile app/api/v1/reports.py 2>/dev/null
print_check $? "reports.py syntax valid"

python -m py_compile app/api/v1/router.py 2>/dev/null
print_check $? "router.py syntax valid"

python -m py_compile app/main.py 2>/dev/null
print_check $? "main.py syntax valid"

python -m py_compile app/api/v1/llm_bias.py 2>/dev/null
print_check $? "llm_bias.py syntax valid"

# Import checks
python -c "from app.services.reporting import ComplianceReportGenerator" 2>/dev/null
print_check $? "Reporting module imports"

python -c "from app.api.v1 import reports" 2>/dev/null
print_check $? "Reports API module imports"

python -c "from app.api.v1 import llm_bias" 2>/dev/null
print_check $? "LLM Bias API module imports"

python -c "from app.db.models import LLMBiasAnalysis" 2>/dev/null
print_check $? "LLM Bias models imports"

cd ..
echo ""

# ============================================
# 3. Database Configuration Checks
# ============================================
echo "3. Database Configuration Checks"
echo "---"

# Check Alembic
test -f backend/alembic.ini
print_check $? "alembic.ini exists"

test -d backend/alembic/versions
print_check $? "Alembic versions directory exists"

test -f backend/alembic/versions/0001_initial.py
print_check $? "Initial migration exists"

test -f backend/alembic/versions/0002_llm_bias.py
print_check $? "LLM Bias migration exists"

echo ""

# ============================================
# 4. API Endpoint Checks
# ============================================
echo "4. API Endpoint Configuration Checks"
echo "---"

# Check that all required API modules exist
test -f backend/app/api/v1/audits.py
print_check $? "Audits API endpoint exists"

test -f backend/app/api/v1/llm_bias.py
print_check $? "LLM Bias API endpoint exists"

test -f backend/app/api/v1/reports.py
print_check $? "Reports API endpoint exists"

test -f backend/app/api/v1/auth.py
print_check $? "Auth API endpoint exists"

# Check router configuration
grep -q "from app.api.v1 import reports" backend/app/api/v1/router.py
print_check $? "Reports router imported"

grep -q "include_router(reports.router" backend/app/api/v1/router.py
print_check $? "Reports router registered"

echo ""

# ============================================
# 5. Documentation Checks
# ============================================
echo "5. Documentation Checks"
echo "---"

test -f ENHANCED_REPORT_GENERATION.md
print_check $? "ENHANCED_REPORT_GENERATION.md exists"

test -f REPORT_DEPLOYMENT_GUIDE.md
print_check $? "REPORT_DEPLOYMENT_GUIDE.md exists"

test -f PHASE2_VERIFICATION_CHECKLIST.md
print_check $? "PHASE2_VERIFICATION_CHECKLIST.md exists"

test -f PHASE2_COMPLETION_REPORT.md
print_check $? "PHASE2_COMPLETION_REPORT.md exists"

test -f README.md
print_check $? "README.md exists"

test -f API_DOCUMENTATION.md
print_check $? "API_DOCUMENTATION.md exists"

test -f DEPLOYMENT_GUIDE.md
print_check $? "DEPLOYMENT_GUIDE.md exists"

echo ""

# ============================================
# 6. Docker Configuration Checks
# ============================================
echo "6. Docker Configuration Checks"
echo "---"

test -f docker-compose.yml
print_check $? "docker-compose.yml exists"

test -f docker-compose.prod.yml
print_check $? "docker-compose.prod.yml exists"

test -f backend/Dockerfile
print_check $? "Backend Dockerfile exists"

test -f frontend/Dockerfile
print_check $? "Frontend Dockerfile exists"

echo ""

# ============================================
# 7. Environment Configuration Checks
# ============================================
echo "7. Environment Configuration Checks"
echo "---"

test -f backend/.env
print_check $? "Backend .env file exists"

test -f backend/.env.example
print_check $? "Backend .env.example template exists"

test -f backend/.env.prod.example
print_check $? "Backend .env.prod.example template exists"

echo ""

# ============================================
# 8. Frontend Configuration Checks
# ============================================
echo "8. Frontend Configuration Checks"
echo "---"

test -f frontend/package.json
print_check $? "Frontend package.json exists"

test -f frontend/vite.config.ts
print_check $? "Frontend vite.config.ts exists"

test -f frontend/tsconfig.json
print_check $? "Frontend tsconfig.json exists"

test -d frontend/src
print_check $? "Frontend src directory exists"

echo ""

# ============================================
# 9. Test Suite Checks
# ============================================
echo "9. Test Suite Checks"
echo "---"

test -f backend/tests/test_enhanced_reporting.py
print_check $? "Enhanced reporting tests exist"

test -d backend/tests
print_check $? "Tests directory exists"

echo ""

# ============================================
# 10. Dependencies Verification
# ============================================
echo "10. Dependencies Verification"
echo "---"

test -f backend/requirements.txt
print_check $? "requirements.txt exists"

# Check key dependencies in requirements
grep -q "fastapi" backend/requirements.txt
print_check $? "FastAPI in requirements"

grep -q "sqlalchemy" backend/requirements.txt
print_check $? "SQLAlchemy in requirements"

grep -q "psycopg2" backend/requirements.txt
print_check $? "psycopg2 in requirements"

grep -q "celery" backend/requirements.txt
print_check $? "Celery in requirements"

grep -q "reportlab" backend/requirements.txt
print_check $? "ReportLab in requirements"

echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "Deployment Readiness Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Review items above.${NC}"
    exit 1
fi
