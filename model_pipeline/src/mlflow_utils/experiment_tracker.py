"""
Docstring for model_pipeline.src.mlflow_utils.experiment_tracker
"""
import mlflow
from typing import Any
from contextlib import contextmanager
from mlflow import MlflowClient
from loguru import logger
from mlflow.entities.run import Run
from mlflow.store.entities.paged_list import PagedList


class ExperimentTracker:
    def __init__(
        self,
        tracking_uri: str,
        experiment_name: str,
        artifact_location: str | None = None
    ):
        """
        Initialize experiment tracker
        
        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Name of the experiment
            artifact_location: Location to store artifacts
        """
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.artifact_location = artifact_location

        mlflow.set_tracking_uri(tracking_uri)

        self.client = MlflowClient(tracking_uri=tracking_uri)
        self.experiment_id  = self._get_or_create_experiment()
        logger.info(f"Initialized experiment tracker: {experiment_name}")
        logger.info(f"Tracking URI: {tracking_uri}")
        logger.info(f"Experiment ID: {self.experiment_id }")
    
    def _get_or_create_experiment(self) -> str:
        """Get existing experiment or a new one"""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            logger.info(f"Creating new experiment: {self.experiment_name=}")
            experiment_id = mlflow.create_experiment(
                name=self.experiment_name,
                artifact_location=self.artifact_location
            )
        else:
            experiment_id = experiment.experiment_id
            logger.info(f"Using existing experiment: {self.experiment_name=} | {experiment_id=}")
        return experiment_id

    @contextmanager
    def start_run(
        self,
        run_name: str | None = None,
        tags: dict[str, Any] | None = None,
        nested: bool = True
    ):
        """
        Context manager for MLflow run
        
        Args:
            run_name: Name for the run
            tags: Dictionary of tags to add to run
            nested: Whether this is a nested run
            
        Yields:
            MLflow run object
        """

        with mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=run_name,
            nested=nested
        ) as run:
            if tags: 
                mlflow.set_tags(tags)
            
            logger.info(f"Started MLflow run: {run.info.run_id}")
            if run_name:
                logger.info(f"Run name: {run_name}")
            
            yield run
            
            logger.info(f"Completed MLflow run: {run.info.run_id}")
    
    def log_param(self, key: str, value: Any):
        """Log a single parameter"""
        mlflow.log_param(key, value)
    
    def log_params(self, params: dict[str, Any]):
        """Log multiple parameters"""
        mlflow.log_params(params)
        logger.debug(f"Logged {len(params)} parameters")
    
    def log_metric(self, key: str, value: float, step: int | None = None):
        """Log a single metric"""
        mlflow.log_metric(key, value, step=step)
    
    def log_metrics(self, metrics: dict[str, float], step: int | None = None):
        """Log multiple metrics"""
        mlflow.log_metrics(metrics, step=step)
        logger.debug(f"Logged {len(metrics)} metrics")
    
    def log_artifact(self, local_path: str, artifact_path: str | None = None):
        """Log an artifact file"""
        mlflow.log_artifact(local_path, artifact_path)
        logger.debug(f"Logged artifact: {local_path}")
    
    def log_dict(self, dictionary: dict, filename: str):
        """Log a dictionary as JSON artifact"""
        mlflow.log_dict(dictionary, filename)
        logger.debug(f"Logged dictionary: {filename}")
    
    def set_tag(self, key: str, value: Any):
        """Set a single tag"""
        mlflow.set_tag(key, value)
    
    def set_tags(self, tags: dict[str, Any]):
        """Set multiple tags"""
        mlflow.set_tags(tags)
        logger.debug(f"Set {len(tags)} tags")
    
    def get_run(self, run_id: str):
        """Get run details"""
        return self.client.get_run(run_id)

    def search_runs(
        self,
        filter_string: str = "",
        max_results: int = 100,
        order_by: list | None = None,
    ) -> PagedList[Run]:
        """
        Search runs in the experiment
        
        Args:
            filter_string: Filter string (e.g., "metrics.accuracy > 0.9")
            max_results: Maximum number of results
            order_by: List of order by clauses
            
        Returns:
            List of runs
        """
        return self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string=filter_string,
            max_results=max_results,
            order_by=order_by,
        )

    def get_best_run(self, metric_name: str, ascending: bool = False):
        """
        Get best run based on a metric
        
        Args:
            metric_name: Name of the metric to optimize
            ascending: If True, lower is better
            
        Returns:
            Best run
        """
        order = "ASC" if ascending else "DESC"
        runs = self.search_runs(
            max_results=1,
            order_by=[f"metrics.{metric_name} {order}"],
        )
        
        if not runs:
            return None
        
        best_run = runs[0]
        logger.info(
            f"Best run: {best_run.info.run_id} "
            f"with {metric_name}={best_run.data.metrics.get(metric_name)}"
        )
        
        return best_run

    def end_run(self):
        mlflow.end_run()
        logger.info("Ended Mlflow run")

