"""
API endpoints for LLM Bias Detection.
Production-ready endpoints with comprehensive error handling and validation.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import LLMBiasAnalysis, LLMBiasDetectionMetric, User
from app.db.session import get_db
from app.schemas.llm_bias import (
    LLMBiasAnalysisRequest,
    LLMBiasAnalysisResponse,
    LLMBiasAnalysisHistory,
    LLMBiasAnalysisHistoryItem,
    BatchBiasAnalysisRequest,
    BatchBiasAnalysisResponse,
    BiasComparisonRequest,
    BiasComparisonResponse,
    BiasDetectionResultSchema,
)
from app.services.llm_bias_detection import LLMBiasDetectionEngine
from app.services.llm_bias_errors import (
    TextValidator,
    BatchAnalysisValidator,
    BiasDetectionError,
    DatabaseError,
    AnalysisFailedError,
    RateLimitError,
    get_rate_limiter,
    log_analysis_error,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the bias detection engine
bias_engine = LLMBiasDetectionEngine()
rate_limiter = get_rate_limiter()


def _serialize_detection(detection: dict) -> BiasDetectionResultSchema:
    """Serialize a detector payload safely for API responses."""
    return BiasDetectionResultSchema(
        algorithm=detection.get("algorithm"),
        category=detection.get("category"),
        score=detection.get("score"),
        severity=detection.get("severity"),
        description=detection.get("description"),
        evidence=detection.get("evidence") or [],
        recommendations=detection.get("recommendations") or [],
    )


@router.post("/analyze", response_model=LLMBiasAnalysisResponse)
def analyze_llm_output(
    request: LLMBiasAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LLMBiasAnalysisResponse:
    """
    Analyze LLM output for bias.
    
    Args:
        request: The LLM output text to analyze
        user: Current authenticated user
        db: Database session
        
    Returns:
        Comprehensive bias analysis result
        
    Raises:
        HTTPException: If analysis fails or input is invalid
    """
    try:
        # Check rate limit
        if not rate_limiter.check_rate_limit(user.id):
            logger.warning(f"Rate limit exceeded for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        
        # Validate input
        TextValidator.validate(request.text)
        
        # Perform bias analysis
        analysis = bias_engine.analyze(request.text)
        
        # Prepare detected biases for storage
        detected_biases_list = []
        for detection in analysis.detected_biases:
            detected_biases_list.append({
                "algorithm": detection.algorithm,
                "category": detection.category,
                "score": detection.score,
                "severity": detection.severity,
                "description": detection.description,
                "evidence": detection.evidence,
                "recommendations": detection.recommendations,
            })
        
        # Store analysis in database
        db_analysis = LLMBiasAnalysis(
            user_id=user.id,
            text_input=request.text,
            overall_bias_score=analysis.overall_bias_score,
            bias_level=analysis.bias_level,
            analysis_results={
                "timestamp": analysis.timestamp,
                "overall_bias_score": analysis.overall_bias_score,
                "bias_level": analysis.bias_level,
                "detected_biases": detected_biases_list,
            },
            detected_biases=detected_biases_list,
            summary=analysis.summary,
            risks=analysis.risks,
            recommendations=analysis.recommendations,
            status="completed",
        )
        
        db.add(db_analysis)
        db.flush()  # Get the ID before committing
        
        # Store individual metrics
        for detection in analysis.detected_biases:
            metric = LLMBiasDetectionMetric(
                analysis_id=db_analysis.id,
                algorithm=detection.algorithm,
                category=detection.category,
                score=detection.score,
                severity=detection.severity,
                description=detection.description,
                evidence=detection.evidence,
            )
            db.add(metric)
        
        db.commit()
        db.refresh(db_analysis)
        
        logger.info(
            f"LLM bias analysis completed for user {user.id}: "
            f"score={analysis.overall_bias_score}, level={analysis.bias_level}"
        )
        
        # Return response
        return LLMBiasAnalysisResponse(
            id=db_analysis.id,
            overall_bias_score=db_analysis.overall_bias_score,
            bias_level=db_analysis.bias_level,
            summary=db_analysis.summary,
            risks=db_analysis.risks,
            recommendations=db_analysis.recommendations,
            detected_biases=[
                _serialize_detection(d)
                for d in detected_biases_list
            ],
            created_at=db_analysis.created_at,
            status="completed",
        )
        
    except BiasDetectionError as e:
        logger.warning(f"Validation error in LLM bias analysis: {e.to_dict()}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        log_analysis_error(user.id, e, {"input_length": len(request.text)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze text for bias. Please try again later.",
        )


@router.post("/batch", response_model=BatchBiasAnalysisResponse)
def batch_analyze_llm_outputs(
    request: BatchBiasAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchBiasAnalysisResponse:
    """
    Analyze multiple LLM outputs for bias in batch.
    
    Args:
        request: List of texts to analyze
        user: Current authenticated user
        db: Database session
        
    Returns:
        Batch analysis results with statistics
    """
    try:
        # Validate batch
        BatchAnalysisValidator.validate(request.texts)
        
        # Check rate limit
        if not rate_limiter.check_rate_limit(user.id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        
        analyses = []
        total_score = 0.0
        high_risk_count = 0
        failed_analyses = 0
        
        for idx, text in enumerate(request.texts):
            try:
                batch_request = LLMBiasAnalysisRequest(text=text)
                result = analyze_llm_output(batch_request, user, db)
                analyses.append(result)
                total_score += result.overall_bias_score
                if result.bias_level in ["high", "critical"]:
                    high_risk_count += 1
            except HTTPException as e:
                logger.warning(f"Failed to analyze text {idx} in batch: {e.detail}")
                failed_analyses += 1
                continue
            except Exception as e:
                log_analysis_error(user.id, e, {"batch_index": idx})
                failed_analyses += 1
                continue
        
        if not analyses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to analyze any texts in the batch.",
            )
        
        average_score = total_score / len(analyses)
        
        logger.info(
            f"Batch analysis completed for user {user.id}: "
            f"analyzed={len(analyses)}, failed={failed_analyses}, "
            f"average_score={average_score}"
        )
        
        return BatchBiasAnalysisResponse(
            analyses=analyses,
            average_bias_score=average_score,
            high_risk_count=high_risk_count,
        )
    
    except BiasDetectionError as e:
        logger.warning(f"Validation error in batch analysis: {e.to_dict()}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        log_analysis_error(user.id, e, {"batch_size": len(request.texts)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch analysis failed. Please try again later.",
        )


@router.get("/history", response_model=LLMBiasAnalysisHistory)
def get_analysis_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> LLMBiasAnalysisHistory:
    """
    Get user's LLM bias analysis history.
    
    Args:
        user: Current authenticated user
        db: Database session
        page: Page number for pagination
        page_size: Number of items per page
        
    Returns:
        Paginated history of analyses
    """
    # Get total count
    total = db.scalar(
        select(func.count())
        .select_from(LLMBiasAnalysis)
        .where(LLMBiasAnalysis.user_id == user.id)
    ) or 0
    
    # Get analyses with pagination
    offset = (page - 1) * page_size
    analyses = db.scalars(
        select(LLMBiasAnalysis)
        .where(LLMBiasAnalysis.user_id == user.id)
        .order_by(desc(LLMBiasAnalysis.created_at))
        .offset(offset)
        .limit(page_size)
    ).all()
    
    items = [
        LLMBiasAnalysisHistoryItem(
            id=a.id,
            text_input=a.text_input[:100] + "..." if len(a.text_input) > 100 else a.text_input,
            overall_bias_score=a.overall_bias_score,
            bias_level=a.bias_level,
            summary=a.summary,
            created_at=a.created_at,
        )
        for a in analyses
    ]
    
    logger.info(f"Retrieved analysis history for user {user.id}: page={page}, total={total}")
    
    return LLMBiasAnalysisHistory(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{analysis_id}", response_model=LLMBiasAnalysisResponse)
def get_analysis_result(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LLMBiasAnalysisResponse:
    """
    Get detailed results of a specific LLM bias analysis.
    
    Args:
        analysis_id: ID of the analysis
        user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed analysis result
        
    Raises:
        HTTPException: If analysis not found or unauthorized
    """
    analysis = db.scalar(
        select(LLMBiasAnalysis).where(
            LLMBiasAnalysis.id == analysis_id,
            LLMBiasAnalysis.user_id == user.id,
        )
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    detected_biases = [
        _serialize_detection(d)
        for d in analysis.detected_biases
    ]
    
    logger.info(f"Retrieved analysis {analysis_id} for user {user.id}")
    
    return LLMBiasAnalysisResponse(
        id=analysis.id,
        overall_bias_score=analysis.overall_bias_score,
        bias_level=analysis.bias_level,
        summary=analysis.summary,
        risks=analysis.risks,
        recommendations=analysis.recommendations,
        detected_biases=detected_biases,
        created_at=analysis.created_at,
        status=analysis.status,
    )


@router.post("/compare", response_model=BiasComparisonResponse)
def compare_bias_levels(
    request: BiasComparisonRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BiasComparisonResponse:
    """
    Compare bias levels across multiple LLM outputs.
    
    Args:
        request: List of texts to compare
        user: Current authenticated user
        db: Database session
        
    Returns:
        Comparison results and summary
    """
    analyses = []
    
    for text in request.texts:
        try:
            batch_request = LLMBiasAnalysisRequest(text=text)
            result = analyze_llm_output(batch_request, user, db)
            analyses.append(result)
        except HTTPException:
            continue
    
    if not analyses:
        raise HTTPException(status_code=400, detail="Failed to analyze any texts")
    
    # Generate comparison summary
    comparison_summary = _generate_comparison_summary(analyses, request.comparison_type)
    
    recommendations = set()
    for analysis in analyses:
        recommendations.update(analysis.recommendations)
    
    logger.info(f"Comparison completed for user {user.id}: {len(analyses)} texts")
    
    return BiasComparisonResponse(
        comparison_type=request.comparison_type,
        analyses=analyses,
        comparison_summary=comparison_summary,
        recommendations=list(recommendations),
    )


def _generate_comparison_summary(analyses: list[LLMBiasAnalysisResponse], comparison_type: str) -> dict:
    """Generate a summary comparing multiple analyses."""
    if comparison_type == "overall":
        scores = [a.overall_bias_score for a in analyses]
        return {
            "average_bias_score": sum(scores) / len(scores),
            "min_bias_score": min(scores),
            "max_bias_score": max(scores),
            "highest_risk": max(analyses, key=lambda x: x.overall_bias_score).bias_level,
            "text_count": len(analyses),
        }
    
    elif comparison_type == "category_wise":
        categories_breakdown = {}
        for analysis in analyses:
            for bias in analysis.detected_biases:
                if bias.category not in categories_breakdown:
                    categories_breakdown[bias.category] = []
                categories_breakdown[bias.category].append(bias.score)
        
        return {
            "categories": {
                cat: {
                    "average_score": sum(scores) / len(scores),
                    "count": len(scores),
                }
                for cat, scores in categories_breakdown.items()
            },
            "total_categories_detected": len(categories_breakdown),
        }
    
    elif comparison_type == "risk_based":
        risk_distribution = {"very_low": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0}
        for analysis in analyses:
            risk_distribution[analysis.bias_level] += 1
        
        return {
            "risk_distribution": risk_distribution,
            "high_risk_percentage": (risk_distribution["high"] + risk_distribution["critical"]) / len(analyses) * 100,
        }
    
    return {}


@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete a LLM bias analysis record.
    
    Args:
        analysis_id: ID of the analysis to delete
        user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If analysis not found or unauthorized
    """
    analysis = db.scalar(
        select(LLMBiasAnalysis).where(
            LLMBiasAnalysis.id == analysis_id,
            LLMBiasAnalysis.user_id == user.id,
        )
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    
    logger.info(f"Deleted analysis {analysis_id} for user {user.id}")
    
    return {"status": "success", "message": "Analysis deleted"}


@router.get("")
def list_analyses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> list[LLMBiasAnalysisResponse]:
    """
    List all LLM bias analyses for the current user.
    
    Args:
        user: Current authenticated user
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of analysis results
    """
    analyses = db.scalars(
        select(LLMBiasAnalysis)
        .where(LLMBiasAnalysis.user_id == user.id)
        .order_by(desc(LLMBiasAnalysis.created_at))
        .offset(skip)
        .limit(limit)
    ).all()
    
    results = []
    for analysis in analyses:
        detected_biases = [
            _serialize_detection(d)
            for d in analysis.detected_biases
        ]
        
        results.append(
            LLMBiasAnalysisResponse(
                id=analysis.id,
                overall_bias_score=analysis.overall_bias_score,
                bias_level=analysis.bias_level,
                summary=analysis.summary,
                risks=analysis.risks,
                recommendations=analysis.recommendations,
                detected_biases=detected_biases,
                created_at=analysis.created_at,
                status=analysis.status,
            )
        )
    
    return results
