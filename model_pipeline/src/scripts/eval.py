"""
Docstring for model_pipelinenene.src.scripts.eval
"""
import sys
from pathlib import Path
import argparse
import pandas as pd
from loguru import logger
import os
import mlflow

from src.model.evaluator import ModelEvaluator
from src.model.xgboost_trainer import ExperimentTracker
from src.utility.helper import load_config

# [IMPORTANT] SETUP docker, remember to get rid of these hardcoded!
os.environ["AWS_ACCESS_KEY_ID"] = "minio"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minio123"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"


def save_predictions_with_probabilities(
    model_uri: str,
    eval_data: pd.DataFrame,
    target_col: str,
    output_path: str,
):
    """
    Load model, generate predictions with probabilities, and save to CSV
    
    Args:
        model_uri: MLflow model URI
        eval_data: Evaluation data including features and target
        target_col: Name of target column
        output_path: Path to save predictions CSV
    """
    logger.info("Loading model for prediction...")
    model = mlflow.pyfunc.load_model(model_uri)
    
    feature_cols = [col for col in eval_data.columns if col != target_col]
    X_eval = eval_data[feature_cols]
    y_true = eval_data[target_col]
    
    logger.info(f"Generating predictions for {len(X_eval)} samples...")
    
    
    y_pred = model.predict(X_eval) 
    
    output_df = eval_data.copy()
    output_df['prediction'] = y_pred
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to: {output_path}")
    
    logger.info(f"Prediction Summary:")
    logger.info(f"  - Total samples: {len(output_df)}")

    logger.info(f"  - Predicted positives: {output_df['prediction'].sum()} ({output_df['prediction'].mean():.2%})")

    
    return output_df


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained XGBoost model")

    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="MLflow run ID to evaluate",
    )
    
    parser.add_argument(
        "--model-uri",
        type=str,
        default=None,
        help="Model URI (e.g., 'runs:/<run_id>/model' or 'models:/<name>@<alias>')",
    )

    parser.add_argument(
        "--eval-data-path",
        type=str,
        default="data/cleaned_churn_data.csv",
        help="Path to evaluation data",
    )

    parser.add_argument(
        "--validate-thresholds",
        action="store_true",
        help="Validate metrics against configured thresholds",
    )

    parser.add_argument(
        "--compare-baseline",
        type=str,
        default=None,
        help="Baseline model URI to compare against",
    )

    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="MLflow experiment name for evaluation run",
    )
    
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="MLflow run name for evaluation",
    )

    parser.add_argument(
        "--output-path-prediction",
        type=str,
        default=None,
        help="Path to save predictions CSV with probabilities (e.g., 'outputs/predictions.csv')",
    )

    args = parser.parse_args()

    if not args.run_id and not args.model_uri:
        parser.error("Either --run-id or --model-uri must be provided")
    
    logger.info("Loading configuration...")
    config = load_config(args.config)

    if args.run_id and not args.model_uri:
        model_uri = f"runs:/{args.run_id}/{config['model']['name']}" #pattern1. models:/<model_id>
        logger.info(f"Using model from run: {args.run_id}")
        logger.info(f"Using model URI: {model_uri}")
    else:
        model_uri = args.model_uri
        logger.info(f"Using model URI: {model_uri}")
    
    if args.experiment_name:
        config["mlflow"]["experiment_name"] = args.experiment_name
    
    logger.info("Initializing MLflow experiment tracker...")
    tracker = ExperimentTracker(
        tracking_uri=config["mlflow"]["tracking_uri"],
        experiment_name=config["mlflow"]["experiment_name"],
        artifact_location=config["mlflow"].get("artifact_location"),
    )
    
    logger.info(f"Loading evaluation data from {args.eval_data_path}")
    data_path = Path(args.eval_data_path)

    if data_path.suffix.lower() == '.csv':
        eval_data = pd.read_csv(data_path)
    elif data_path.suffix.lower() in ['.parquet', '.pq']:
        eval_data = pd.read_parquet(data_path)
    else:
        supported_formats = [".csv", ".parquet", ".pq"]
        raise ValueError(
            f"Unsupported file format: {data_path.suffix}. "
            f"Supported formats are: {supported_formats}"
        )
    

    cols_to_drop = [c for c in eval_data.columns if c.strip() == "" or "Unnamed" in c]
    if cols_to_drop:
        logger.warning(f"Dropping dirty columns from evaluation data: {cols_to_drop}")
        eval_data = eval_data.drop(columns=cols_to_drop)
    logger.info(f"Loaded {len(eval_data)} samples with {len(eval_data.columns)} features")

    target_col = config["features"]["target_column"]
    feature_cols = config["features"]["training_features"]

    eval_data = eval_data[feature_cols + [target_col]]

    
    evaluator = ModelEvaluator(
        config=config.get("evaluation", {}),
        experiment_tracker=tracker,
    )

    tags = {
        "task": "model_evaluation",
        "model_uri": model_uri,
    }
    if args.run_id:
        tags["source_run_id"] = args.run_id
    
    with tracker.start_run(
        run_name=args.run_name or f"eval_{args.run_id or 'model'}",
        tags=tags,
    ) as run:
        logger.info(f"Started evaluation run: {run.info.run_id}")
        
        target_col = config["features"]["target_column"]
        logger.info(f"Target column: {target_col=}")
        
        logger.info("=" * 60)
        logger.info("EVALUATING MODEL")
        logger.info("=" * 60)
        metrics = evaluator.evaluate_model(
            model_uri=model_uri,
            eval_data=eval_data,
            target_col=target_col,
            model_type=config["model"]["type"],
         
        )

        tracker.log_metrics(metrics)
        
        if args.validate_thresholds:
            logger.info("=" * 60)
            logger.info("VALIDATING AGAINST THRESHOLDS")
            logger.info("=" * 60)
            
            validation_passed = evaluator.validate_against_threshold(metrics)
            tracker.set_tag("validation_passed", str(validation_passed))
            
            if validation_passed:
                logger.info("Model passed all threshold validations")
            else:
                logger.error("Model failed threshold validation")
                # sys.exit(1)


        if args.output_path_prediction:
            logger.info("=" * 60)
            logger.info("GENERATING PREDICTIONS")
            logger.info("=" * 60)
            
            try:
                
                save_predictions_with_probabilities(
                    model_uri=model_uri,
                    eval_data=eval_data,
                    target_col=target_col,
                    output_path=args.output_path_prediction,
                )
                
                tracker.log_artifact(args.output_path_prediction)
                logger.info("Predictions artifact logged to MLflow")
                
            except Exception as e:
                logger.error(f"Failed to generate predictions: {e}")
                raise
        
        logger.info("=" * 60)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 60)

        metrics_summary = evaluator.get_metrics_summary()
        logger.info(f"\n{metrics_summary.to_string()}")

        logger.info("=" * 60)
        logger.info("EVALUATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Evaluation Run ID: {run.info.run_id}")
        logger.info(f"Model URI: {model_uri}")

        if args.validate_thresholds:
            logger.info(f"Threshold Validation: {'PASSED' if validation_passed else 'FAILED'}") #type:ignore
        
        if args.output_path_prediction:
            logger.info(f"Predictions saved to: {args.output_path_prediction}")
    
        logger.info("=" * 60)

if __name__ == "__main__":
    main()