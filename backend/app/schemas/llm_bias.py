"""
Pydantic schemas for LLM Bias Detection API endpoints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class BiasDetectionResultSchema(BaseModel):
    """Schema for individual bias detection result."""
    algorithm: str
    category: str
    score: float = Field(..., ge=0, le=1)
    severity: str  # low, medium, high, critical
    description: str
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class LLMBiasAnalysisRequest(BaseModel):
    """Schema for LLM bias analysis request."""
    text: str = Field(..., min_length=10, max_length=10000, description="LLM output text to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "A great leader must be strong and decisive. Women are typically more nurturing than men, making them better at supporting roles rather than leading teams."
            }
        }


class LLMBiasAnalysisResponse(BaseModel):
    """Schema for LLM bias analysis response."""
    id: str
    overall_bias_score: float = Field(..., ge=0, le=1)
    bias_level: str  # very_low, low, moderate, high, critical
    summary: str
    risks: List[str]
    recommendations: List[str]
    detected_biases: List[BiasDetectionResultSchema]
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


class LLMBiasAnalysisHistoryItem(BaseModel):
    """Schema for history item of LLM bias analysis."""
    id: str
    text_input: str
    overall_bias_score: float
    bias_level: str
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True


class LLMBiasAnalysisHistory(BaseModel):
    """Schema for LLM bias analysis history."""
    items: List[LLMBiasAnalysisHistoryItem]
    total: int
    page: int
    page_size: int


class BatchBiasAnalysisRequest(BaseModel):
    """Schema for batch bias analysis request."""
    texts: List[str] = Field(..., min_items=1, max_items=100)

    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "First LLM output...",
                    "Second LLM output..."
                ]
            }
        }


class BatchBiasAnalysisResponse(BaseModel):
    """Schema for batch bias analysis response."""
    analyses: List[LLMBiasAnalysisResponse]
    average_bias_score: float
    high_risk_count: int


class BiasComparisonRequest(BaseModel):
    """Schema for comparing multiple texts."""
    texts: List[str] = Field(..., min_items=2, max_items=10, description="Texts to compare")
    comparison_type: str = Field(default="overall", description="Type of comparison: overall, category_wise, risk_based")


class BiasComparisonResponse(BaseModel):
    """Schema for bias comparison response."""
    comparison_type: str
    analyses: List[LLMBiasAnalysisResponse]
    comparison_summary: Dict[str, Any]
    recommendations: List[str]
