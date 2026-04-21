# LLM Bias Detection Feature Documentation

## Overview

FairLens now includes a comprehensive LLM (Large Language Model) bias detection feature that analyzes LLM-generated text for multiple types of bias, toxicity, and fairness issues. This feature uses production-ready algorithms to detect gender bias, stereotyping, toxicity, sentiment bias, and representation issues.

## Features

### 1. **Multi-Algorithm Bias Detection**

The feature implements five complementary bias detection algorithms:

#### Gender Bias Detector
- Detects gender-based stereotypes and imbalances
- Analyzes gender pronoun usage
- Identifies stereotypical language associated with specific genders
- Scores gender representation balance
- **Thresholds**: Score > 0.1 flags as bias

#### Toxicity Detector
- Identifies offensive and dehumanizing language
- Detects hate speech patterns
- Flags aggressive language and threats
- Recognizes slurs and derogatory terms
- **Thresholds**: Score > 0.1 flags as toxic

#### Stereotyping Detector
- Identifies overgeneralization about groups
- Detects stereotypical occupation associations
- Flags age and cultural stereotypes
- Recognizes limiting generalizations
- **Thresholds**: Score > 0.2 flags as stereotyping

#### Sentiment Bias Detector
- Analyzes positive/negative sentiment balance
- Detects unfair favor toward specific topics/groups
- Identifies overwhelming emotional language
- **Thresholds**: Score > 0.2 flags as sentiment bias

#### Representation Analyzer
- Analyzes balanced representation of groups
- Detects imbalanced positive/negative descriptors
- Identifies underrepresentation of minority groups
- **Thresholds**: Score > 0.2 flags as representation issue

### 2. **Comprehensive Analysis Output**

Each analysis provides:
- **Overall Bias Score**: 0-1 scale (1 = highest bias)
- **Bias Level**: very_low, low, moderate, high, critical
- **Detected Biases**: Detailed results from each algorithm
- **Risks**: Identified potential harms
- **Recommendations**: Actionable suggestions for improvement
- **Evidence**: Specific examples found in text

### 3. **Production-Ready Features**

- **Rate Limiting**: 30 requests per minute per user (configurable)
- **Input Validation**: Text length 10-10,000 characters
- **Error Handling**: Comprehensive error codes and messages
- **Database Storage**: All analyses stored for audit trail
- **Batch Processing**: Analyze up to 100 texts at once
- **History Tracking**: View past analyses and trends
- **Comparison**: Compare bias levels across multiple texts

## API Endpoints

### Analyze Single Text
```
POST /api/v1/llm-bias/analyze

Request:
{
  "text": "LLM output text to analyze..."
}

Response:
{
  "id": "analysis-id",
  "overall_bias_score": 0.35,
  "bias_level": "moderate",
  "summary": "Analysis summary...",
  "risks": ["List of identified risks"],
  "recommendations": ["List of recommendations"],
  "detected_biases": [
    {
      "algorithm": "gender_bias_detector",
      "category": "gender",
      "score": 0.4,
      "severity": "high",
      "description": "Gender imbalance detected...",
      "evidence": ["Evidence 1", "Evidence 2"]
    }
  ],
  "created_at": "2026-04-21T...",
  "status": "completed"
}
```

### Batch Analysis
```
POST /api/v1/llm-bias/batch

Request:
{
  "texts": ["text1", "text2", "text3"]
}

Response:
{
  "analyses": [
    { /* analysis results */ }
  ],
  "average_bias_score": 0.32,
  "high_risk_count": 1
}
```

### Get Analysis History
```
GET /api/v1/llm-bias/history?page=1&page_size=10

Response:
{
  "items": [
    {
      "id": "analysis-id",
      "text_input": "First 100 chars of input...",
      "overall_bias_score": 0.35,
      "bias_level": "moderate",
      "summary": "...",
      "created_at": "2026-04-21T..."
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

### Compare Analyses
```
POST /api/v1/llm-bias/compare

Request:
{
  "texts": ["text1", "text2", "text3"],
  "comparison_type": "overall" | "category_wise" | "risk_based"
}

Response:
{
  "comparison_type": "overall",
  "analyses": [/* analysis results */],
  "comparison_summary": {
    "average_bias_score": 0.32,
    "min_bias_score": 0.15,
    "max_bias_score": 0.45,
    "highest_risk": "high"
  },
  "recommendations": [/* consolidated recommendations */]
}
```

### Get Specific Analysis
```
GET /api/v1/llm-bias/{analysis_id}
```

### List All Analyses
```
GET /api/v1/llm-bias?skip=0&limit=10
```

### Delete Analysis
```
DELETE /api/v1/llm-bias/{analysis_id}
```

## Database Schema

### LLMBiasAnalysis Table
```sql
CREATE TABLE llm_bias_analyses (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  text_input TEXT NOT NULL,
  overall_bias_score FLOAT NOT NULL,
  bias_level VARCHAR(32) NOT NULL,
  analysis_results JSON NOT NULL,
  detected_biases JSON NOT NULL,
  summary TEXT,
  risks JSON,
  recommendations JSON,
  status VARCHAR(32) DEFAULT 'completed',
  error_message TEXT,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX ix_llm_bias_analyses_user_id ON llm_bias_analyses(user_id);
CREATE INDEX ix_llm_bias_analyses_created_at ON llm_bias_analyses(created_at);
```

### LLMBiasDetectionMetric Table
```sql
CREATE TABLE llm_bias_detection_metrics (
  id VARCHAR(36) PRIMARY KEY,
  analysis_id VARCHAR(36) NOT NULL,
  algorithm VARCHAR(128) NOT NULL,
  category VARCHAR(64) NOT NULL,
  score FLOAT NOT NULL,
  severity VARCHAR(32) NOT NULL,
  description TEXT,
  evidence JSON,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (analysis_id) REFERENCES llm_bias_analyses(id)
);

CREATE INDEX ix_llm_bias_detection_metrics_analysis_id 
ON llm_bias_detection_metrics(analysis_id);
```

## Frontend Components

### LLMBiasDetectionPage
Main page component featuring:
- Text input area for pasting LLM output
- Real-time analysis with progress indicator
- Visual bias score gauge with color coding
- Detailed results breakdown by bias type
- Evidence and recommendations display
- Analysis history sidebar
- Batch analysis capabilities

## Configuration

### Environment Variables
```env
# Rate limiting (default: 30)
LLM_BIAS_RATE_LIMIT=30

# Min text length (default: 10)
LLM_BIAS_MIN_TEXT_LENGTH=10

# Max text length (default: 10000)
LLM_BIAS_MAX_TEXT_LENGTH=10000

# Database connection for storing analyses
DATABASE_URL=postgresql://user:pass@host/db
```

### Thresholds (Configurable in code)
```python
# In llm_bias_detection.py
DI_THRESHOLD = 0.8          # Disparate impact ratio (80% rule)
DPD_THRESHOLD = 0.1         # Demographic parity difference
EO_THRESHOLD = 0.1          # Equalized odds
PP_THRESHOLD = 0.1          # Predictive parity
CAL_THRESHOLD = 0.1         # Calibration
```

## Error Handling

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| INVALID_INPUT | 400 | Input validation failed |
| TEXT_TOO_SHORT | 400 | Text less than 10 characters |
| TEXT_TOO_LONG | 400 | Text exceeds 10,000 characters |
| ANALYSIS_FAILED | 500 | Analysis algorithm failed |
| DATABASE_ERROR | 500 | Database operation failed |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| UNAUTHORIZED | 401 | Authentication required |

### Error Response Format
```json
{
  "error_code": "ANALYSIS_FAILED",
  "message": "LLM bias analysis failed: specific reason",
  "details": {
    "algorithm": "gender_bias_detector",
    "retry_after": 60
  }
}
```

## Deployment

### Production Checklist

- [x] Database migrations applied
- [x] Environment variables configured
- [x] Rate limiting configured
- [x] Error logging configured
- [x] Frontend routes added
- [x] API endpoints registered
- [x] Input validation enabled
- [x] Database indexes created
- [x] CORS configured if needed
- [x] SSL/TLS enabled (production)

### Docker Deployment

The feature is included in the default Docker setup. No additional configuration needed:

```bash
docker-compose up -d
```

### Database Migration

Apply the migration for new tables:

```bash
# From backend directory
alembic upgrade head
```

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Use batch endpoint for multiple texts (up to 100)
2. **Caching**: Analysis results are stored in database for quick retrieval
3. **Rate Limiting**: Configure based on expected usage
4. **Database Indexes**: Ensure indexes on user_id and created_at

### Expected Performance

- Single analysis: ~50-100ms per 1000 characters
- Batch analysis (100 texts): ~5-10 seconds
- Database storage: ~5-10ms per analysis

## Monitoring and Logging

### Log Levels

```python
# INFO: Analysis completed, audit trail
logger.info(f"LLM bias analysis completed for user {user.id}")

# WARNING: Rate limit exceeded, validation errors
logger.warning(f"Rate limit exceeded for user {user.id}")

# ERROR: Analysis failures, database errors
logger.error(f"Error during LLM bias analysis", exc_info=True)

# DEBUG: Detailed tracing (development only)
logger.debug(f"Text validation passed: {text_length} characters")
```

### Metrics to Monitor

1. **Analysis Success Rate**: Percentage of analyses completed
2. **Average Bias Score**: Trend of bias scores over time
3. **High-Risk Detections**: Texts flagged as high/critical risk
4. **Response Time**: API endpoint latency
5. **Rate Limit Hits**: Number of users hitting rate limit
6. **Error Rate**: Percentage of failed analyses

## Example Usage

### Python Client
```python
import requests

# Analyze single text
response = requests.post(
    "http://localhost:8001/api/v1/llm-bias/analyze",
    json={"text": "LLM output text..."},
    headers={"Authorization": f"Bearer {token}"}
)
result = response.json()
print(f"Bias Score: {result['overall_bias_score']}")
print(f"Level: {result['bias_level']}")

# Get history
history = requests.get(
    "http://localhost:8001/api/v1/llm-bias/history",
    headers={"Authorization": f"Bearer {token}"}
).json()
print(f"Total analyses: {history['total']}")
```

### JavaScript/Frontend
```typescript
import { api } from '@/lib/api'

// Analyze text
const response = await api.post('/llm-bias/analyze', {
  text: 'LLM output text...'
})

const analysis = response.data
console.log(`Bias Score: ${analysis.overall_bias_score}`)
console.log(`Detected Biases: ${analysis.detected_biases.length}`)

// Get history with pagination
const history = await api.get('/llm-bias/history', {
  params: { page: 1, page_size: 10 }
})
```

## Troubleshooting

### Common Issues

**Issue**: Rate limit exceeded
- **Solution**: Implement client-side retry with exponential backoff
- **Code**: Add `Retry-After` header checking

**Issue**: Text too long error
- **Solution**: Truncate text to 10,000 characters or split into batches

**Issue**: Database connection error
- **Solution**: Verify DATABASE_URL and network connectivity

**Issue**: Slow analysis performance
- **Solution**: Use batch endpoint, check database indexes, monitor server load

## Future Enhancements

1. **Multi-language Support**: Support for text in multiple languages
2. **Custom Models**: Allow organizations to define custom bias patterns
3. **Real-time Streaming**: Analyze streaming LLM outputs
4. **Integration with LLM APIs**: Direct integration with OpenAI, Claude, etc.
5. **Advanced Analytics**: Detailed trend analysis and reporting
6. **Automated Remediation**: Suggest rewrites of biased text
7. **Team Collaboration**: Share analyses across teams
8. **Webhooks**: Notify external systems of high-risk detections

## Support & Contributing

For issues, questions, or contributions:
- GitHub: https://github.com/fairlens/fairlens
- Documentation: https://fairlens.dev/docs
- Discord: https://discord.gg/fairlens

## License

This feature is part of FairLens and is licensed under [LICENSE_TYPE].
