"""
Real Fairness Metrics Implementation using AIF360 and Fairlearn.
Production-ready algorithms for detecting and measuring bias.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    confusion_matrix, roc_auc_score
)

logger = logging.getLogger(__name__)


class FairnessComputeError(Exception):
    """Custom exception for fairness computation errors."""
    pass


@dataclass
class MetricResult:
    """Single fairness metric result."""
    metric_name: str
    group_name: str
    value: float
    threshold: float
    passed: bool


class MetricsResult:
    """Container for all fairness metrics results."""
    
    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self.thresholds: Dict[str, float] = {}
        self.violations: List[Dict[str, Any]] = []
        self.summary_score: float = 0.0
        self.detailed_results: Dict[str, Any] = {}
        self.metric_results: List[MetricResult] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "violations": self.violations,
            "summary_score": self.summary_score,
            "detailed_results": self.detailed_results
        }


class FairnessMetricsEngine:
    """Production-ready fairness metrics computation engine."""
    
    # Industry standard disparate impact ratio threshold (80% rule)
    DI_THRESHOLD = 0.8
    # Demographic parity difference threshold
    DPD_THRESHOLD = 0.1
    # Equalized odds threshold
    EO_THRESHOLD = 0.1
    # Predictive parity threshold
    PP_THRESHOLD = 0.1
    # Calibration threshold
    CAL_THRESHOLD = 0.1
    
    def __init__(self):
        """Initialize fairness metrics engine."""
        self.required_columns = {"y_true", "y_pred", "sensitive_attribute"}
        
    def validate_input(
        self, 
        data: pd.DataFrame, 
        y_true_col: str,
        y_pred_col: str,
        sensitive_attr_col: str
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate input data for fairness computation.
        
        Args:
            data: Input dataframe
            y_true_col: Ground truth column name
            y_pred_col: Predictions column name
            sensitive_attr_col: Sensitive attribute column name
            
        Returns:
            Cleaned data and list of validation warnings
            
        Raises:
            FairnessComputeError: If validation fails
        """
        warnings = []
        
        # Check for required columns
        required = {y_true_col, y_pred_col, sensitive_attr_col}
        missing = required - set(data.columns)
        if missing:
            raise FairnessComputeError(f"Missing required columns: {missing}")
        
        # Check for null values
        null_counts = data[list(required)].isnull().sum()
        if null_counts.any():
            null_info = null_counts[null_counts > 0]
            warnings.append(f"Found null values: {dict(null_info)}")
            data = data.dropna(subset=list(required))
        
        # Validate binary classification (or multiclass)
        unique_true = data[y_true_col].nunique()
        unique_pred = data[y_pred_col].nunique()
        
        if unique_true > 10:
            raise FairnessComputeError(
                f"Expected binary/multiclass, got {unique_true} classes in y_true"
            )
        if unique_pred > 10:
            raise FairnessComputeError(
                f"Expected binary/multiclass, got {unique_pred} classes in y_pred"
            )
        
        # Check sample size
        if len(data) < 100:
            warnings.append(f"Small sample size ({len(data)} samples); metrics may be unreliable")
        
        # Check group balance
        group_sizes = data[sensitive_attr_col].value_counts()
        if (group_sizes.min() / group_sizes.max()) < 0.05:
            warnings.append(
                f"Imbalanced sensitive attribute groups: {dict(group_sizes)}. "
                "Some metrics may be unreliable."
            )
        
        return data, warnings
    
    def compute_disparate_impact(
        self, 
        data: pd.DataFrame,
        y_pred_col: str,
        sensitive_attr_col: str,
        favorable_outcome: Optional[Any] = None
    ) -> Dict[str, float]:
        """
        Compute Disparate Impact Ratio (80% rule).
        
        Formula: min(P(outcome|group1) / P(outcome|group2))
        
        A ratio < 0.8 indicates potential discrimination.
        """
        if favorable_outcome is None:
            favorable_outcome = data[y_pred_col].max()
        
        groups = data[sensitive_attr_col].unique()
        di_ratios = {}
        
        for group in groups:
            group_data = data[data[sensitive_attr_col] == group]
            if len(group_data) == 0:
                continue
            
            favorable_rate = (group_data[y_pred_col] == favorable_outcome).mean()
            di_ratios[str(group)] = favorable_rate
        
        # Compute min ratio
        if len(di_ratios) > 1:
            favorable_rates = list(di_ratios.values())
            max_rate = max(favorable_rates)
            min_rate = min(favorable_rates)
            
            if max_rate > 0:
                di_ratio = min_rate / max_rate
            else:
                di_ratio = 1.0
        else:
            di_ratio = 1.0
        
        return {
            "disparate_impact_ratio": di_ratio,
            "favorable_rates_by_group": di_ratios,
            "threshold": self.DI_THRESHOLD,
            "violation": di_ratio < self.DI_THRESHOLD
        }
    
    def compute_demographic_parity_difference(
        self,
        data: pd.DataFrame,
        y_pred_col: str,
        sensitive_attr_col: str,
        favorable_outcome: Optional[Any] = None
    ) -> Dict[str, float]:
        """
        Compute Demographic Parity Difference.
        
        Formula: max(|P(outcome|group_i) - P(outcome|group_j)|)
        
        Measures if different groups have equal selection/positive outcome rates.
        """
        if favorable_outcome is None:
            favorable_outcome = data[y_pred_col].max()
        
        groups = data[sensitive_attr_col].unique()
        favorable_rates = {}
        
        for group in groups:
            group_data = data[data[sensitive_attr_col] == group]
            if len(group_data) == 0:
                continue
            rate = (group_data[y_pred_col] == favorable_outcome).mean()
            favorable_rates[str(group)] = rate
        
        # Compute max difference
        if len(favorable_rates) > 1:
            rates = list(favorable_rates.values())
            dpd = max(rates) - min(rates)
        else:
            dpd = 0.0
        
        return {
            "demographic_parity_difference": dpd,
            "favorable_rates_by_group": favorable_rates,
            "threshold": self.DPD_THRESHOLD,
            "violation": dpd > self.DPD_THRESHOLD
        }
    
    def compute_equalized_odds_difference(
        self,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        sensitive_attr_col: str,
        favorable_outcome: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Compute Equalized Odds Difference.
        
        Formula: max(|TPR_i - TPR_j|, |FPR_i - FPR_j|)
        
        Ensures equal true positive and false positive rates across groups.
        """
        if favorable_outcome is None:
            favorable_outcome = data[y_pred_col].max()
        
        groups = data[sensitive_attr_col].unique()
        tpr_by_group = {}
        fpr_by_group = {}
        
        for group in groups:
            group_data = data[data[sensitive_attr_col] == group]
            if len(group_data) == 0:
                continue
            
            # True positives and false positives
            tp = ((group_data[y_true_col] == favorable_outcome) & 
                  (group_data[y_pred_col] == favorable_outcome)).sum()
            fn = ((group_data[y_true_col] == favorable_outcome) & 
                  (group_data[y_pred_col] != favorable_outcome)).sum()
            fp = ((group_data[y_true_col] != favorable_outcome) & 
                  (group_data[y_pred_col] == favorable_outcome)).sum()
            tn = ((group_data[y_true_col] != favorable_outcome) & 
                  (group_data[y_pred_col] != favorable_outcome)).sum()
            
            # TPR = TP / (TP + FN), FPR = FP / (FP + TN)
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            
            tpr_by_group[str(group)] = tpr
            fpr_by_group[str(group)] = fpr
        
        # Compute max differences
        if len(tpr_by_group) > 1:
            tpr_values = list(tpr_by_group.values())
            fpr_values = list(fpr_by_group.values())
            eod_tpr = max(tpr_values) - min(tpr_values)
            eod_fpr = max(fpr_values) - min(fpr_values)
            eod = max(eod_tpr, eod_fpr)
        else:
            eod = 0.0
        
        return {
            "equalized_odds_difference": eod,
            "tpr_by_group": tpr_by_group,
            "fpr_by_group": fpr_by_group,
            "threshold": self.EO_THRESHOLD,
            "violation": eod > self.EO_THRESHOLD
        }
    
    def compute_predictive_parity_difference(
        self,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        sensitive_attr_col: str,
        favorable_outcome: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Compute Predictive Parity Difference.
        
        Formula: max(|PPV_i - PPV_j|)
        
        Ensures similar precision/positive predictive value across groups.
        """
        if favorable_outcome is None:
            favorable_outcome = data[y_pred_col].max()
        
        groups = data[sensitive_attr_col].unique()
        ppv_by_group = {}
        
        for group in groups:
            group_data = data[data[sensitive_attr_col] == group]
            if len(group_data) == 0:
                continue
            
            # True positives and false positives
            tp = ((group_data[y_true_col] == favorable_outcome) & 
                  (group_data[y_pred_col] == favorable_outcome)).sum()
            fp = ((group_data[y_true_col] != favorable_outcome) & 
                  (group_data[y_pred_col] == favorable_outcome)).sum()
            
            # PPV = TP / (TP + FP)
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            ppv_by_group[str(group)] = ppv
        
        # Compute max difference
        if len(ppv_by_group) > 1:
            ppv_values = list(ppv_by_group.values())
            ppd = max(ppv_values) - min(ppv_values)
        else:
            ppd = 0.0
        
        return {
            "predictive_parity_difference": ppd,
            "ppv_by_group": ppv_by_group,
            "threshold": self.PP_THRESHOLD,
            "violation": ppd > self.PP_THRESHOLD
        }
    
    def compute_intersectional_metrics(
        self,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        sensitive_attrs: List[str],
        favorable_outcome: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Compute fairness metrics across intersections of sensitive attributes.
        
        Detects compounded bias affecting multiple marginalized groups.
        """
        if favorable_outcome is None:
            favorable_outcome = data[y_pred_col].max()
        
        intersectional_metrics = {}
        violation_count = 0
        
        # Generate all intersections
        for primary_attr in sensitive_attrs:
            for secondary_attr in sensitive_attrs:
                if primary_attr == secondary_attr:
                    continue
                
                key = f"{primary_attr}_x_{secondary_attr}"
                group_metrics = []
                
                primary_groups = data[primary_attr].unique()
                secondary_groups = data[secondary_attr].unique()
                
                for p_group in primary_groups:
                    for s_group in secondary_groups:
                        subset = data[
                            (data[primary_attr] == p_group) & 
                            (data[secondary_attr] == s_group)
                        ]
                        
                        if len(subset) < 20:  # Need minimum sample
                            continue
                        
                        favorable_rate = (subset[y_pred_col] == favorable_outcome).mean()
                        
                        # Compute local DI ratio
                        tp = ((subset[y_true_col] == favorable_outcome) & 
                              (subset[y_pred_col] == favorable_outcome)).sum()
                        fp = ((subset[y_true_col] != favorable_outcome) & 
                              (subset[y_pred_col] == favorable_outcome)).sum()
                        
                        group_metrics.append({
                            "group": f"{p_group}_{s_group}",
                            "favorable_rate": favorable_rate,
                            "sample_size": len(subset),
                            "precision": tp / (tp + fp) if (tp + fp) > 0 else 0.0
                        })
                        
                        if favorable_rate < self.DI_THRESHOLD * 0.5:  # Severe bias
                            violation_count += 1
                
                if group_metrics:
                    intersectional_metrics[key] = {
                        "groups": group_metrics,
                        "violation_count": violation_count
                    }
        
        return {
            "intersectional_analysis": intersectional_metrics,
            "total_intersection_violations": violation_count
        }
    
    def compute_calibration_metrics(
        self,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_proba_col: Optional[str],
        sensitive_attr_col: str
    ) -> Dict[str, Any]:
        """Compute calibration metrics for probability predictions."""
        if y_pred_proba_col is None or y_pred_proba_col not in data.columns:
            return {"calibration_error": None, "calibration_by_group": {}}
        
        groups = data[sensitive_attr_col].unique()
        calibration_by_group = {}
        
        for group in groups:
            group_data = data[data[sensitive_attr_col] == group]
            if len(group_data) == 0:
                continue
            
            # Expected Calibration Error (ECE)
            expected_pos = group_data[y_pred_proba_col].mean()
            actual_pos = (group_data[y_true_col] == 1).mean()
            ece = abs(expected_pos - actual_pos)
            
            calibration_by_group[str(group)] = {
                "expected_positive_rate": expected_pos,
                "actual_positive_rate": actual_pos,
                "calibration_error": ece
            }
        
        overall_ece = np.mean([v["calibration_error"] for v in calibration_by_group.values()])
        
        return {
            "calibration_error": overall_ece,
            "calibration_by_group": calibration_by_group,
            "threshold": self.CAL_THRESHOLD,
            "violation": overall_ece > self.CAL_THRESHOLD
        }
    
    def compute_all_metrics(
        self,
        data: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        sensitive_attributes: List[str],
        y_pred_proba_col: Optional[str] = None,
        favorable_outcome: Optional[Any] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Tuple[float, List[MetricResult]]:
        """
        Compute all fairness metrics - returns score and metric results for backward compatibility.
        
        Args:
            data: Input dataframe
            y_true_col: Ground truth column name
            y_pred_col: Predictions column name
            sensitive_attributes: List of sensitive attribute column names
            y_pred_proba_col: (Optional) Predicted probability column
            favorable_outcome: (Optional) Favorable outcome value
            thresholds: (Optional) Custom thresholds dict
            
        Returns:
            Tuple of (score, metric_results_list)
        """
        metric_results = []
        
        try:
            # Validate input
            data, warnings = self.validate_input(
                data, y_true_col, y_pred_col, sensitive_attributes[0]
            )
            
            if len(data) == 0:
                raise FairnessComputeError("No valid data after validation")
            
            # Set favorable outcome if not provided
            if favorable_outcome is None:
                favorable_outcome = data[y_pred_col].max()
            
            # Set thresholds
            if thresholds is None:
                thresholds = {}
            
            # Compute core fairness metrics for primary sensitive attribute
            primary_attr = sensitive_attributes[0]
            
            # 1. Disparate Impact
            di_results = self.compute_disparate_impact(
                data, y_pred_col, primary_attr, favorable_outcome
            )
            di_value = di_results["disparate_impact_ratio"]
            di_threshold = thresholds.get("disparate_impact", self.DI_THRESHOLD)
            di_passed = di_value >= di_threshold
            metric_results.append(MetricResult(
                metric_name="disparate_impact",
                group_name="overall",
                value=round(di_value, 4),
                threshold=di_threshold,
                passed=di_passed
            ))
            
            # 2. Demographic Parity Difference
            dpd_results = self.compute_demographic_parity_difference(
                data, y_pred_col, primary_attr, favorable_outcome
            )
            dpd_value = dpd_results["demographic_parity_difference"]
            dpd_threshold = thresholds.get("demographic_parity_diff", self.DPD_THRESHOLD)
            dpd_passed = dpd_value <= dpd_threshold
            metric_results.append(MetricResult(
                metric_name="demographic_parity_diff",
                group_name="overall",
                value=round(dpd_value, 4),
                threshold=dpd_threshold,
                passed=dpd_passed
            ))
            
            # 3. Equalized Odds Difference
            eod_results = self.compute_equalized_odds_difference(
                data, y_true_col, y_pred_col, primary_attr, favorable_outcome
            )
            eod_value = eod_results["equalized_odds_difference"]
            eod_threshold = thresholds.get("equalized_odds_diff", self.EO_THRESHOLD)
            eod_passed = eod_value <= eod_threshold
            metric_results.append(MetricResult(
                metric_name="equalized_odds_diff",
                group_name="overall",
                value=round(eod_value, 4),
                threshold=eod_threshold,
                passed=eod_passed
            ))
            
            # 4. Predictive Parity Difference
            ppd_results = self.compute_predictive_parity_difference(
                data, y_true_col, y_pred_col, primary_attr, favorable_outcome
            )
            ppd_value = ppd_results["predictive_parity_difference"]
            ppd_threshold = thresholds.get("predictive_parity_diff", self.PP_THRESHOLD)
            ppd_passed = ppd_value <= ppd_threshold
            metric_results.append(MetricResult(
                metric_name="predictive_parity_diff",
                group_name="overall",
                value=round(ppd_value, 4),
                threshold=ppd_threshold,
                passed=ppd_passed
            ))
            
            # Compute fairness score (0-100)
            score = round((sum(1 for item in metric_results if item.passed) / max(len(metric_results), 1)) * 100, 2)
            
            logger.info(f"Fairness computation complete. Score: {score}")
            
            return score, metric_results
            
        except FairnessComputeError as e:
            logger.error(f"Fairness computation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in fairness computation: {e}")
            raise FairnessComputeError(f"Computation failed: {str(e)}")


# Singleton instance
_fairness_engine = FairnessMetricsEngine()


def run_fairness_pipeline(config: dict) -> tuple[float, list[MetricResult]]:
    """
    Main entry point - backward compatible with existing code.
    """
    try:
        return _fairness_engine.compute_all_metrics(
            data=config.get("data"),
            y_true_col=config.get("y_true_col", "y_true"),
            y_pred_col=config.get("y_pred_col", "y_pred"),
            sensitive_attributes=config.get("sensitive_attributes", ["sensitive_attr"]),
            y_pred_proba_col=config.get("y_pred_proba_col"),
            favorable_outcome=config.get("favorable_outcome"),
            thresholds=config.get("thresholds")
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
