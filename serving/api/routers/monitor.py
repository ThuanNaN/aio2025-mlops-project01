"""
Drift monitoring endpoints - FIXED VERSION
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd
import logging
import os
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from monitoring import generate_drift_report, load_reference_data, load_current_data

router = APIRouter(prefix="/monitor", tags=["Monitoring"])
logger = logging.getLogger(__name__)


class DriftMetricsResponse(BaseModel):
    """Response schema for drift metrics"""
    overall_drift_score: float = Field(..., description="Overall drift score (0-1)")
    drift_status: str = Field(..., description="Drift status: LOW/MEDIUM/HIGH")
    dataset_drift: Optional[bool] = Field(None, description="Whether dataset drift detected")
    number_of_drifted_features: Optional[int] = Field(None, description="Number of features with drift")
    total_features: Optional[int] = Field(None, description="Total number of features")
    drift_by_feature: Optional[dict] = Field(None, description="Drift details by feature")
    target_drift: Optional[bool] = Field(None, description="Whether target drift detected")
    prediction_drift: Optional[bool] = Field(None, description="Whether prediction drift detected")
    performance: Optional[dict] = Field(None, description="Performance metrics comparison")
    reference_data_size: int = Field(..., description="Size of reference dataset")
    current_data_size: int = Field(..., description="Size of current dataset")
    timestamp: str = Field(..., description="Timestamp of drift check")


@router.get("/drift", response_model=DriftMetricsResponse)
async def check_drift(
    format: str = Query("json", pattern="^(json|html)$", description="Output format: json or html"),
    reference_path: Optional[str] = Query(None, description="Path to reference data CSV"),
    current_path: Optional[str] = Query(None, description="Path to current/production data CSV"),
    days: int = Query(30, ge=1, le=365, description="Number of recent days for current data"),
    save_html: bool = Query(False, description="Save HTML report to file")
):
    """
    Check for data drift between reference and current production data.
    
    Returns drift metrics for:
    - Feature distribution drift (data drift)
    - Prediction distribution drift (if predictions available)
    
    Note: Classification performance metrics require ground truth labels in production data.
    """
    try:
        # Set default paths
        ref_path = reference_path or "/home/mlops/Repository/aio2025-mlops-project01/model-system/prediction_folder/prediction4.csv"
        curr_path = current_path or "/home/mlops/Repository/aio2025-mlops-project01/serving/data_model/production/production.csv"
        
        logger.info(f"Loading reference data from: {ref_path}")
        logger.info(f"Loading current data from: {curr_path} (last {days} days)")
        
        # Load data
        try:
            reference_df = load_reference_data(ref_path)
            current_df = load_current_data(curr_path, days=days)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        logger.info(f"Reference data shape: {reference_df.shape}")
        logger.info(f"Current data shape: {current_df.shape}")
        
        # Define feature columns for drift monitoring
        feature_columns = [
            'Age', 'Gender', 'Tenure', 'Usage_Frequency', 'Support_Calls',
            'Payment_Delay', 'Subscription_Type', 'Contract_Length',
            'Total_Spend', 'Last_Interaction'
        ]
        
        # Filter to only existing columns
        existing_features = [col for col in feature_columns if col in reference_df.columns and col in current_df.columns]
        
        if not existing_features:
            raise HTTPException(
                status_code=400, 
                detail="No common feature columns found between reference and current data"
            )
        
        logger.info(f"Monitoring drift for features: {existing_features}")
        
        # Prepare data for drift analysis
        ref_data = reference_df[existing_features].copy()
        curr_data = current_df[existing_features].copy()
        
        #  Proper classification metrics setup
        include_classification = False
        
        # Check if we can do classification metrics
        #  need BOTH target AND prediction in BOTH datasets
        has_ref_target = 'Churn' in reference_df.columns
        has_ref_prediction = 'prediction' in reference_df.columns
        has_curr_target = 'Churn' in current_df.columns  
        has_curr_prediction = 'prediction' in current_df.columns
        
        if has_ref_target and has_ref_prediction and has_curr_target and has_curr_prediction:
            # Both datasets have ground truth and predictions
            logger.info("Classification metrics available: Both datasets have target and prediction")
            ref_data['target'] = reference_df['Churn']
            ref_data['prediction'] = reference_df['prediction']
            curr_data['target'] = current_df['Churn']
            curr_data['prediction'] = current_df['prediction']
            include_classification = True
            
        elif has_ref_prediction and has_curr_prediction:
            #  Only prediction drift (no performance metrics)
            logger.info("Prediction drift only: No ground truth in production data")
            # Just monitor prediction distribution drift
            ref_data['prediction'] = reference_df['prediction']
            curr_data['prediction'] = current_df['prediction']
            # Don't set target - Evidently will only compute prediction drift
            include_classification = False
            
        else:
            logger.info("No classification metrics: Missing prediction columns")
        
        # Generate HTML report path if needed
        html_path = None
        if save_html or format == "html":
            reports_dir = "reports/drift"
            os.makedirs(reports_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = f"{reports_dir}/drift_report_{timestamp_str}.html"
        
        # Generate drift report
        metrics = generate_drift_report(
            current_df=curr_data,
            reference_df=ref_data,
            output_path=html_path if save_html else None,
            include_classification=include_classification
        )
        
        # Add metadata
        metrics['reference_data_size'] = len(reference_df)
        metrics['current_data_size'] = len(current_df)
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Return HTML if requested
        if format == "html":
            temp_path = f"/tmp/drift_report_{datetime.now().timestamp()}.html"
            
            try:
                from evidently.report import Report
                from evidently.metric_preset import DataDriftPreset, ClassificationPreset
            except ImportError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to import Evidently AI: {str(e)}"
                )
            
            # Build metrics list
            metrics_list = [DataDriftPreset()]
            if include_classification:
                metrics_list.append(ClassificationPreset())
            
            report = Report(metrics=metrics_list)
            report.run(reference_data=ref_data, current_data=curr_data, column_mapping=None)
            report.save_html(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return HTMLResponse(content=html_content)
        
        # Return JSON metrics
        return DriftMetricsResponse(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking drift: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")