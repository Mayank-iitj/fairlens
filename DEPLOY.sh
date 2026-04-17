#!/bin/bash
# FairLens Production Deployment and Testing Script
# Complete end-to-end setup and validation

set -e

echo "=========================================="
echo "FairLens Production Deployment Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Backend Setup
echo -e "\n${YELLOW}[1/8] Setting up Python environment...${NC}"
cd backend

# Create venv
python3 -m venv venv
source venv/bin/activate &> /dev/null || . venv/Scripts/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q --upgrade pip setuptools wheel
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Python environment ready${NC}"

# 2. Database Setup
echo -e "\n${YELLOW}[2/8] Setting up database migrations...${NC}"
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql+psycopg2://fairlens:fairlens@localhost:5432/fairlens"
fi

alembic upgrade head

echo -e "${GREEN}✓ Database migrations applied${NC}"

# 3. Test fairness algorithms
echo -e "\n${YELLOW}[3/8] Testing fairness algorithm implementations...${NC}"
python -c "
from app.services.fairness import FairnessMetricsEngine
import pandas as pd
import numpy as np

print('Testing Fairness Engine...')

# Create synthetic test data
np.random.seed(42)
n_samples = 500
data = pd.DataFrame({
    'y_true': np.random.binomial(1, 0.5, n_samples),
    'y_pred': np.random.binomial(1, 0.6, n_samples),
    'gender': np.random.choice(['M', 'F'], n_samples),
    'age_group': np.random.choice(['Young', 'Old'], n_samples)
})

engine = FairnessMetricsEngine()
metrics = engine.compute_all_metrics(
    data=data,
    y_true_col='y_true',
    y_pred_col='y_pred',
    sensitive_attributes=['gender', 'age_group']
)

print(f'✓ Disparate Impact: {metrics.metrics.get(\"disparate_impact_ratio\", 0):.4f}')
print(f'✓ Demographic Parity: {metrics.metrics.get(\"demographic_parity_difference\", 0):.4f}')
print(f'✓ Equalized Odds: {metrics.metrics.get(\"equalized_odds_difference\", 0):.4f}')
print(f'✓ Fairness Score: {metrics.summary_score:.1f}/100')
"

echo -e "${GREEN}✓ Fairness algorithms working${NC}"

# 4. Test report generation
echo -e "\n${YELLOW}[4/8] Testing report generation...${NC}"
python -c "
from app.services.reporting import ComplianceReportGenerator
from pathlib import Path
import os

print('Testing Report Generator...')
generator = ComplianceReportGenerator()

# Create test report
os.makedirs('test_reports', exist_ok=True)

metrics = {
    'disparate_impact_ratio': 0.92,
    'demographic_parity_difference': 0.08,
    'equalized_odds_difference': 0.06
}

violations = [
    {
        'metric': 'demographic_parity',
        'value': 0.12,
        'threshold': 0.1,
        'severity': 'high'
    }
]

# Test JSON report
json_report = generator.generate_json_report(
    audit_id='test_001',
    dataset_info={'sample_count': 1000, 'sensitive_attributes': ['gender']},
    metrics=metrics,
    violations=violations,
    compliance_framework='EEOC'
)

print('✓ JSON report generated')

# Test PDF report
pdf_path = generator.generate_pdf_report(
    destination=Path('test_reports/test_audit.pdf'),
    audit_id='test_001',
    dataset_info={'sample_count': 1000, 'sensitive_attributes': ['gender']},
    metrics=metrics,
    violations=violations,
    compliance_framework='EEOC'
)

print('✓ PDF report generated')
"

echo -e "${GREEN}✓ Report generation working${NC}"

# 5. Test AI service
echo -e "\n${YELLOW}[5/8] Testing AI service (fallback mode)...${NC}"
python -c "
from app.services.ai import GroqAIService

print('Testing AI Service...')
service = GroqAIService()

# Test fallback explanations
explanation = service.explain_metric('disparate_impact', 0.75, 0.8)
print(f'✓ Metric explanation: {explanation[:50]}...')

suggestions = service.suggest_fix('disparate_impact', 0.75, 'high')
print(f'✓ Got {len(suggestions.get(\"techniques\", []))} remediation techniques')

summary = service.summarize_audit(76.5, ['demographic_parity'])
print(f'✓ Audit summary: {summary[:50]}...')
"

echo -e "${GREEN}✓ AI service working (fallback mode)${NC}"

# 6. Test data pipeline
echo -e "\n${YELLOW}[6/8] Testing data pipeline...${NC}"
python -c "
from app.services.data_pipeline import DataValidator
import pandas as pd
import numpy as np
import io

print('Testing Data Pipeline...')
validator = DataValidator()

# Create test CSV
test_data = pd.DataFrame({
    'outcome': np.random.binomial(1, 0.5, 200),
    'score': np.random.uniform(0, 100, 200),
    'gender': np.random.choice(['M', 'F'], 200),
    'age': np.random.randint(18, 80, 200)
})

csv_buffer = io.BytesIO()
test_data.to_csv(csv_buffer, index=False)
csv_buffer.seek(0)

data, metrics = validator.load_data(csv_buffer, 'test.csv'), None
print(f'✓ Loaded {len(data)} rows, {len(data.columns)} columns')

metrics = validator.validate_data_quality(data)
print(f'✓ Data quality score: {metrics.quality_score:.1%}')

sensitive_attrs = validator.detect_sensitive_attributes(data)
print(f'✓ Detected sensitive attributes: {sensitive_attrs}')

target = validator.detect_target_variable(data)
print(f'✓ Detected target: {target}')
"

echo -e "${GREEN}✓ Data pipeline working${NC}"

# 7. Backend syntax validation
echo -e "\n${YELLOW}[7/8] Validating Python code...${NC}"
python -m py_compile \
    app/main.py \
    app/core/config.py \
    app/core/security.py \
    app/core/error_handling.py \
    app/db/models.py \
    app/db/session.py \
    app/services/fairness.py \
    app/services/reporting.py \
    app/services/ai.py \
    app/services/data_pipeline.py \
    app/services/audit_orchestration.py \
    app/api/v1/*.py

echo -e "${GREEN}✓ All Python files valid${NC}"

# 8. Frontend setup
echo -e "\n${YELLOW}[8/8] Setting up frontend...${NC}"
cd ../frontend

npm ci --quiet 2>/dev/null || npm install --quiet
npm run build --silent

echo -e "${GREEN}✓ Frontend build successful${NC}"

# Final summary
cd ..

echo -e "\n${GREEN}=========================================="
echo "FairLens Production Deployment Ready!"
echo "==========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Set environment variables in .env files"
echo "2. Configure database connection string"
echo "3. Add GROQ API key for AI features"
echo "4. Run: docker-compose up -d"
echo "5. Test with: curl http://localhost:8000/health"

echo -e "\n${YELLOW}Documentation:${NC}"
echo "- Backend API: http://localhost:8000/docs"
echo "- Frontend: http://localhost:5173"
echo "- Database: PostgreSQL on localhost:5432"

echo -e "\n${GREEN}✓ Setup complete!${NC}\n"
