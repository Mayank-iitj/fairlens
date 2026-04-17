"""
Production-Ready Data Pipeline Service.
Handles data ingestion, validation, preprocessing, and quality assessment.
"""
import logging
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, BinaryIO

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataPipelineError(Exception):
    """Custom exception for data pipeline errors."""
    pass


class DataQualityMetrics:
    """Container for data quality metrics."""
    
    def __init__(self):
        self.total_rows: int = 0
        self.total_columns: int = 0
        self.missing_values: Dict[str, int] = {}
        self.duplicates: int = 0
        self.data_types: Dict[str, str] = {}
        self.categorical_features: List[str] = []
        self.numerical_features: List[str] = []
        self.quality_score: float = 1.0
        self.issues: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "missing_values": self.missing_values,
            "duplicates": self.duplicates,
            "data_types": self.data_types,
            "categorical_features": self.categorical_features,
            "numerical_features": self.numerical_features,
            "quality_score": self.quality_score,
            "issues": self.issues
        }


class DataValidator:
    """Validates and preprocesses data for fairness audit."""
    
    MIN_ROWS = 100
    MAX_ROWS = 1_000_000
    MAX_MISSING_RATIO = 0.5
    MAX_DUPLICATE_RATIO = 0.1
    ACCEPTED_FORMATS = {".csv", ".parquet", ".xlsx", ".json"}
    
    def __init__(self):
        """Initialize data validator."""
        self.quality_metrics = DataQualityMetrics()
    
    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate file format and basic properties.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check file exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return False, errors
        
        # Check file size (max 500MB)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 500:
            errors.append(f"File too large: {file_size_mb:.1f}MB (max 500MB)")
        
        # Check file extension
        if file_path.suffix.lower() not in self.ACCEPTED_FORMATS:
            errors.append(
                f"Unsupported format: {file_path.suffix}. "
                f"Accepted: {', '.join(self.ACCEPTED_FORMATS)}"
            )
        
        return len(errors) == 0, errors
    
    def load_data(self, file_obj: BinaryIO, file_name: str) -> pd.DataFrame:
        """
        Load data from uploaded file.
        
        Args:
            file_obj: File-like object from upload
            file_name: Original filename for format detection
            
        Returns:
            Loaded DataFrame
            
        Raises:
            DataPipelineError: If loading fails
        """
        try:
            file_ext = Path(file_name).suffix.lower()
            
            if file_ext == ".csv":
                data = pd.read_csv(file_obj, dtype_backend="numpy_nullable")
            elif file_ext == ".parquet":
                data = pd.read_parquet(file_obj)
            elif file_ext == ".xlsx":
                data = pd.read_excel(file_obj)
            elif file_ext == ".json":
                data = pd.read_json(file_obj)
            else:
                raise DataPipelineError(f"Unsupported file format: {file_ext}")
            
            logger.info(f"Loaded data: {len(data)} rows, {len(data.columns)} columns")
            return data
            
        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            raise DataPipelineError(f"Failed to load file: {str(e)}")
    
    def validate_data_quality(self, data: pd.DataFrame) -> DataQualityMetrics:
        """
        Validate data quality and compute metrics.
        
        Args:
            data: Input DataFrame
            
        Returns:
            DataQualityMetrics object
        """
        metrics = DataQualityMetrics()
        
        # Basic shape
        metrics.total_rows = len(data)
        metrics.total_columns = len(data.columns)
        
        # Row count validation
        if metrics.total_rows < self.MIN_ROWS:
            metrics.issues.append(
                f"Too few rows ({metrics.total_rows}). Minimum: {self.MIN_ROWS}"
            )
        
        if metrics.total_rows > self.MAX_ROWS:
            metrics.issues.append(
                f"Too many rows ({metrics.total_rows}). Maximum: {self.MAX_ROWS}"
            )
        
        # Missing values
        missing = data.isnull().sum()
        metrics.missing_values = missing[missing > 0].to_dict()
        
        missing_ratio = missing.sum() / (metrics.total_rows * metrics.total_columns)
        if missing_ratio > self.MAX_MISSING_RATIO:
            metrics.issues.append(
                f"Too many missing values ({missing_ratio:.1%}). "
                f"Maximum: {self.MAX_MISSING_RATIO:.1%}"
            )
        
        # Duplicates
        metrics.duplicates = data.duplicated().sum()
        dup_ratio = metrics.duplicates / metrics.total_rows if metrics.total_rows > 0 else 0
        if dup_ratio > self.MAX_DUPLICATE_RATIO:
            metrics.issues.append(
                f"Too many duplicates ({dup_ratio:.1%}). "
                f"Maximum: {self.MAX_DUPLICATE_RATIO:.1%}"
            )
        
        # Data types and feature categorization
        for col in data.columns:
            dtype_name = str(data[col].dtype)
            metrics.data_types[col] = dtype_name
            
            # Categorize features
            if data[col].dtype in ["object", "string"]:
                metrics.categorical_features.append(col)
            elif data[col].dtype in ["int64", "int32", "float64", "float32"]:
                metrics.numerical_features.append(col)
        
        # Compute quality score
        quality_score = 1.0
        if missing_ratio > 0.1:
            quality_score *= (1 - missing_ratio)
        if dup_ratio > 0.01:
            quality_score -= 0.05
        
        # Bonus for reasonable data size
        if self.MIN_ROWS <= metrics.total_rows < self.MAX_ROWS:
            quality_score = min(1.0, quality_score + 0.1)
        
        metrics.quality_score = max(0.0, quality_score)
        
        self.quality_metrics = metrics
        
        logger.info(f"Data quality score: {metrics.quality_score:.1%}")
        return metrics
    
    def detect_sensitive_attributes(self, data: pd.DataFrame) -> List[str]:
        """
        Automatically detect potential sensitive attributes.
        
        Args:
            data: Input DataFrame
            
        Returns:
            List of suspected sensitive attribute column names
        """
        suspicious_names = {
            "gender", "sex", "race", "ethnicity", "age", "religion",
            "disability", "veteran", "protected", "group", "demographic"
        }
        
        detected = []
        
        for col in data.columns:
            col_lower = col.lower()
            
            # Check by name
            if any(term in col_lower for term in suspicious_names):
                detected.append(col)
                continue
            
            # Check cardinality (sensitive attrs usually have small cardinality)
            if data[col].dtype in ["object", "string", "category"]:
                unique_ratio = data[col].nunique() / len(data)
                if 0.01 < unique_ratio < 0.2:  # 1-20% unique values
                    detected.append(col)
        
        logger.info(f"Detected {len(detected)} potential sensitive attributes: {detected}")
        return detected
    
    def detect_target_variable(self, data: pd.DataFrame) -> Optional[str]:
        """
        Attempt to auto-detect the target variable column.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Column name or None if not detected
        """
        suspicious_names = {"target", "label", "outcome", "prediction", "decision", "approved", "granted"}
        
        for col in data.columns:
            col_lower = col.lower()
            if col_lower in suspicious_names or any(term in col_lower for term in suspicious_names):
                # Verify it's binary or categorical
                if data[col].nunique() <= 10:
                    logger.info(f"Detected target variable: {col}")
                    return col
        
        # If no name match, look for binary column
        for col in data.columns:
            if data[col].nunique() == 2 and data[col].dtype in ["object", "int64"]:
                logger.info(f"Auto-detected binary target: {col}")
                return col
        
        return None
    
    def clean_data(
        self,
        data: pd.DataFrame,
        handle_missing: str = "drop",
        remove_duplicates: bool = True
    ) -> pd.DataFrame:
        """
        Clean data for fairness audit.
        
        Args:
            data: Input DataFrame
            handle_missing: How to handle missing values (drop, mean, median, forward_fill)
            remove_duplicates: Whether to remove duplicate rows
            
        Returns:
            Cleaned DataFrame
        """
        original_rows = len(data)
        
        # Remove duplicates
        if remove_duplicates:
            data = data.drop_duplicates()
            removed = original_rows - len(data)
            if removed > 0:
                logger.info(f"Removed {removed} duplicate rows")
        
        # Handle missing values
        if handle_missing == "drop":
            data = data.dropna()
        elif handle_missing == "mean":
            for col in data.select_dtypes(include=[np.number]).columns:
                data[col].fillna(data[col].mean(), inplace=True)
        elif handle_missing == "median":
            for col in data.select_dtypes(include=[np.number]).columns:
                data[col].fillna(data[col].median(), inplace=True)
        elif handle_missing == "forward_fill":
            data = data.fillna(method="ffill")
        
        removed = original_rows - len(data)
        if removed > 0:
            logger.info(f"Removed {removed} rows due to missing values")
        
        return data
    
    def sample_data(self, data: pd.DataFrame, max_samples: int = 10000) -> pd.DataFrame:
        """
        Sample data to reasonable size for computation.
        
        Args:
            data: Input DataFrame
            max_samples: Maximum number of samples to keep
            
        Returns:
            Sampled DataFrame preserving class distributions
        """
        if len(data) <= max_samples:
            return data
        
        # Stratified sampling on most categorical column
        potential_strata = [
            col for col in data.columns 
            if data[col].dtype == "object" and data[col].nunique() < 20
        ]
        
        if potential_strata:
            strata_col = potential_strata[0]
            data = data.groupby(strata_col, group_keys=False).apply(
                lambda x: x.sample(frac=max_samples/len(data), random_state=42)
            ).reset_index(drop=True)
        else:
            data = data.sample(n=max_samples, random_state=42)
        
        logger.info(f"Sampled data to {len(data)} rows")
        return data
    
    def validate_for_audit(
        self,
        data: pd.DataFrame,
        y_true_col: Optional[str] = None,
        y_pred_col: Optional[str] = None,
        sensitive_attr_col: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate that data is suitable for fairness audit.
        
        Args:
            data: Input DataFrame
            y_true_col: Ground truth column name (auto-detected if None)
            y_pred_col: Prediction column name (auto-detected if None)
            sensitive_attr_col: Sensitive attribute column (auto-detected if None)
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Auto-detect if not provided
        if y_true_col is None:
            y_true_col = self.detect_target_variable(data)
        if y_true_col is None:
            errors.append("Could not detect ground truth column. Please specify y_true_col")
        
        if y_pred_col is None:
            # Assume last numeric column if not specified
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                y_pred_col = numeric_cols[-1]
        if y_pred_col is None:
            errors.append("Could not detect prediction column. Please specify y_pred_col")
        
        if sensitive_attr_col is None:
            detected = self.detect_sensitive_attributes(data)
            if not detected:
                errors.append("Could not detect sensitive attributes. Please specify sensitive_attr_col")
            else:
                sensitive_attr_col = detected[0]
        
        # Verify columns exist
        required_cols = [c for c in [y_true_col, y_pred_col, sensitive_attr_col] if c]
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")
        
        return len(errors) == 0, errors


# Singleton instance
_validator = DataValidator()


def load_and_validate_data(
    file_obj: BinaryIO,
    file_name: str,
    clean: bool = True,
    sample: bool = True
) -> Tuple[pd.DataFrame, DataQualityMetrics]:
    """
    Load, validate, and prepare data for audit.
    
    Args:
        file_obj: Uploaded file object
        file_name: Original filename
        clean: Whether to clean the data
        sample: Whether to sample if data is too large
        
    Returns:
        Tuple of (cleaned_data, quality_metrics)
    """
    try:
        # Load data
        data = _validator.load_data(file_obj, file_name)
        
        # Validate quality
        metrics = _validator.validate_data_quality(data)
        
        # Optionally clean
        if clean:
            data = _validator.clean_data(data)
        
        # Optionally sample
        if sample:
            data = _validator.sample_data(data)
        
        return data, metrics
        
    except Exception as e:
        logger.error(f"Data loading and validation failed: {e}")
        raise DataPipelineError(f"Data processing failed: {str(e)}")
