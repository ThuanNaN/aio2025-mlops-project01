"""
Docstring for model-system.src.model.xgboost_trainer
"""
from pathlib import Path
import mlflow
import mlflow.xgboost
from mlflow.models import infer_signature
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from loguru import logger

from src.mlflow_utils.experiment_tracker import ExperimentTracker


class XGBBinaryClassifierWrapper(mlflow.pyfunc.PythonModel): #type:ignore
    def __init__(self, booster, feature_names, label_encoder=None, feature_encoders=None):
        self.booster = booster
        self.feature_names = feature_names
        self.label_encoder = label_encoder
        self.feature_encoders = feature_encoders or {}



    def predict(self, context, model_input, params=None): #type:ignore
        df = model_input.copy()

    
        for col, encoder in self.feature_encoders.items():
            if col in df.columns:
                df[col] = encoder.transform(df[col].astype(str))
            
        dmatrix = xgb.DMatrix(
            df[self.feature_names],
            feature_names=self.feature_names,
            
        )
        probs = self.booster.predict(dmatrix)

        
        # Handle params
        if params is None:
            params = {}
        
        return_probs = params.get('return_probs', False)
        return_both = params.get('return_both', False)

        binary_preds = (probs >= 0.5).astype(int)
        if self.label_encoder is not None:
            final_preds = self.label_encoder.inverse_transform(binary_preds)
        else:
            final_preds = binary_preds

        max_probs = np.maximum(probs, 1 - probs)
        
        if return_both:
            return pd.DataFrame({
                'probability': max_probs,
                'prediction': final_preds
            })
        elif return_probs:
            return max_probs
        else:
            return final_preds


class XGBoostTrainer:
    def __init__(
        self,
        config: dict,
        experiment_tracker: ExperimentTracker
    ):
        self.config = config
        self.tracker = experiment_tracker 
        self.model = None
        self.feature_names = None
    
    def prepare_data(
        self,
        data: pd.DataFrame,
        target_col: str,
        feature_cols: list[str],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> tuple[xgb.DMatrix, xgb.DMatrix, pd.Series, pd.Series]:
        logger.info(f"Prepare the training data...")
        if feature_cols is None:
            feature_cols = [
                col for col in data.columns if col != target_col
            ]
        self.feature_names = feature_cols
        X = data[feature_cols]
        y = data[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        logger.info(f"Class distribution - Train: {y_train.value_counts().to_dict()}")
        logger.info(f"Class distribution - Test: {y_test.value_counts().to_dict()}")
        
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
        dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_cols)
        
        return dtrain, dtest, y_train, y_test

    def train(
        self,
        dtrain: xgb.DMatrix,
        dtest: xgb.DMatrix,
        params: dict | None = None,
        num_boost_round: int = 100,
        early_stopping_rounds: int = 10,
    ):
        """
        Train an XgBoost with mlflow tracking
        Args:
            dtrain: Training DMatrix
            dtest: Test DMatrix
            params: XGBoost parameters (None = use config)
            num_boost_round: Number of boosting rounds
            early_stopping_rounds: Early stopping patience
            
        Returns:
            Trained XGBoost booster
        """

        logger.info("Start model training...")
        if params is None:
            params = self.config.get("xgboost", {})
        
        mlflow.xgboost.autolog( #type:ignore
            log_input_examples=True,
            log_model_signatures=True,
            log_models=False,
            model_format="json",  
        )
        if self.feature_names is None:
            raise ValueError(f"Please prepare the data before training")

        self.tracker.log_params({
            "num_boost_round": num_boost_round,
            "early_stopping_rounds": early_stopping_rounds,
            "feature_count": len(self.feature_names),
        })
        self.tracker.log_param("features", ",".join(self.feature_names))
        evals = [(dtrain, "train"), (dtest, "test")]

        self.model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=num_boost_round,
            evals=evals,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=10,
        )

        logger.info(f"Training complete. Best iteration: {self.model.best_iteration}")
        logger.info(f"Best score: {self.model.best_score:.4f}")

        # Log feature importance metrics
        
        importance = self.model.get_score(importance_type="gain")
        sorted_importance = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        for feature, score in sorted_importance:
            self.tracker.log_metric(f"feature_importance/{feature}", score) #type:ignore
        logger.info("Feature importance logged")

        return self.model
    
    def save_model(
        self,
        model_name: str,
        input_example: pd.DataFrame,
        label_encoder=None,
        feature_encoders=None
    ):
        if self.model is None:
            raise ValueError("Model not trained.")

        wrapper = XGBBinaryClassifierWrapper(
            booster=self.model,
            feature_names=self.feature_names,
            label_encoder=label_encoder,
            feature_encoders=feature_encoders
        )

       
        prediction = wrapper.predict(context=None, model_input=input_example)
        
        signature = infer_signature(input_example, prediction)
        SRC_PATH = Path(__file__).resolve().parents[2]
        logger.info(f"{SRC_PATH=}")

        
        logger.info(f"Saving model as '{model_name}'...")
        mlflow.pyfunc.log_model(
            python_model=wrapper,
            artifact_path=model_name,
            signature=signature,
            input_example=input_example.iloc[:3],
            code_paths=[str(SRC_PATH / 'src')]
        )
    
    def load_model(self, model_uri: str):
        logger.info(f"Loading model from {model_uri=}")
        self.model = mlflow.xgboost.load_model(model_uri) #type:ignore
        logger.info("Model loaded successfully")


    