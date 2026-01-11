"""
Docstring for model_pipeline.src.scripts.train
"""
from pathlib import Path
import argparse
import pandas as pd
import yaml
from loguru import logger

import pandas as pd
import yaml
from loguru import logger

from sklearn.preprocessing import LabelEncoder

from src.mlflow_utils.experiment_tracker import ExperimentTracker
from src.model.xgboost_trainer import GenericBinaryClassifierTrainer
from src.utility.helper import load_config
import os

os.environ["AWS_ACCESS_KEY_ID"] = "minio"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minio123"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"




def main():
    parser = argparse.ArgumentParser(description="Train XGBoost model")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
    )

    parser.add_argument(
        "--training-data-path",
        type=str,
        default="data/training_data.csv",
        help="Path to training data",
    )

    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="MLflow run name",
    )
  
    args = parser.parse_args()

    logger.info("Loading configuration...")
    config = load_config(args.config)

    if args.experiment_name:
        config["mlflow"]["experiment_name"] = args.experiment_name
    logger.info(f"Experiment name: {args.experiment_name}")
    
    logger.info("Initializing MLflow experiment tracker...")
    tracker = ExperimentTracker(
        tracking_uri=config["mlflow"]["tracking_uri"],
        experiment_name=config["mlflow"]["experiment_name"],
        artifact_location=config["mlflow"].get("artifact_location"),
    )

    logger.info(f"Loading training data from {args.training_data_path=}")
    data_path = Path(args.training_data_path)

    if data_path.suffix.lower() == '.csv':
        data = pd.read_csv(data_path)
    elif data_path.suffix.lower() in ['.parquet', '.pq']:
        data = pd.read_parquet(data_path)
    else:
        supported_formats = [".csv", ".parquet", ".pq"]
        raise ValueError(
            f"Unsupported file format: {data_path.suffix}. "
            f"Supported formats are: {supported_formats}"
        )
    logger.info(f"Loaded {len(data)} samples with {len(data.columns)} features")

    raw_data = data.copy()
    # preprocessing label encoder
    encoders = {}
    target_col = config["features"]["target_column"]
    feature_cols = config["features"]["training_features"]

    cols_to_encode = data.select_dtypes(include=['object', 'category']).columns.tolist()
    for col in cols_to_encode:
        logger.info(f"Encoding column: {col}")
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col].astype(str))
        encoders[col] = le
    
    target_encoder = encoders.pop(target_col, None)
    feature_encoders = encoders

    
    trainer = GenericBinaryClassifierTrainer(
        config=config["model"],
        experiment_tracker=tracker,
        model_type=config['model']['model_type']
    )

    tags: dict= config["mlflow"]["tags"]
    with tracker.start_run(
        run_name=args.run_name,
        tags=tags,
    ) as run:
        logger.info(f"Started MLflow run: {run.info.run_id}")
        target_col = config["features"]["target_column"]
        feature_cols = config["features"]["training_features"]
        
        dtrain, dval, y_train, y_val = trainer.prepare_data(
            data=data,
            target_col=target_col,
            feature_cols=feature_cols,
            test_size=config["model"]["train_test_split"],
            random_state=config["model"]["random_state"],
        )
        target_encoder = encoders.get(target_col)

        trainer.train(
            X_train=dtrain,
            y_train=y_train,
            X_test=dval,
            y_test=y_val,
            params=config["model"]["parameters"],
        )
        

        trainer.save_model(
            model_name=config['model']['name'],
            input_example=raw_data[feature_cols].head(5),
            label_encoder=target_encoder,
            feature_encoders=feature_encoders
        )
        
        
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info(f"Run ID: {run.info.run_id}")
        logger.info(f"Run Name: {args.run_name or 'N/A'}")
        

if __name__ == "__main__":
    main()