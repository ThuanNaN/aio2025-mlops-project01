"""
Docstring for model_pipelinene.src.mlflow_utils.model_registry
"""
from mlflow import MlflowClient
from mlflow.entities.model_registry import ModelVersion
from loguru import logger
import mlflow

class ModelRegistry:
    def __init__(self, tracking_uri: str):
        self.client = MlflowClient(tracking_uri=tracking_uri)
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"Initialized Model Registry: {tracking_uri}")


    def retrieve_eval_metrics_based_on_run_id(
        self,
        run_id: str,
        metric: str
    ):
        all_experiments = mlflow.search_runs(search_all_experiments=True)
        print(all_experiments)
        evaluation = all_experiments[ #type:ignore
            (all_experiments["tags.source_run_id"] == f"{run_id}") & #type:ignore
            (all_experiments["status"] == "FINISHED") #type:ignore
        ]

        latest_eval = evaluation.sort_values(
            by="end_time",
            ascending=False
        ).head(1)

        eval_run_id = latest_eval['run_id'].values.tolist()[0]
        eval_run = self.client.get_run(eval_run_id)

        return eval_run.data.metrics[metric]
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: dict[str,str] | None = None,
        description: str | None = None
    ) -> ModelVersion:
        """
        Register a model from a run
        Args:
            model_uri: URI of model (e.g., "runs:/<run_id>/model")
            model_name: Name to register model under
            tags: Tags to add to model version
            description: Description of model version
            
        Returns:
            ModelVersion object
        """

        logger.info(f"Registering model: {model_name}")
        logger.info(f"Model URI: {model_uri}")

        try:
            self.client.get_registered_model(model_name)
        except Exception:
            logger.info(f"Registered model '{model_name}' not found. Creating it.")
            self.client.create_registered_model(
                name=model_name,
                description=description,
            )

        model_version = self.client.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=model_uri.split("/")[1] if "runs:" in model_uri else None,
            description=description,
        )

        if tags:
            for key, val in tags.items():
                self.client.set_model_version_tag(
                    name=model_name,
                    version=model_version.version,
                    key=key,
                    value=val
                )
        
        logger.info(f"Model registered: {model_name} v{model_version.version}")
        return model_version
    

    def create_registered_model(
        self,
        name: str,
        tags: dict[str,str] | None = None,
        description: str | None = None
    ): 
        """
        Create a new registered model
        """
        try:
            self.client.create_registered_model(
                name=name,
                tags=tags,
                description=description
            )
        except Exception as e:
            logger.warning(f"Model {name=} may already exist: {e}")
        
    def set_model_version_alias(
        self,
        model_name: str,
        version: str,
        alias: str,
    ):
        """
        Set an alias for a model version (e.g., "champion", "staging")
        
        Args:
            alias: Alias name (e.g., "champion", "staging", "production")
        """
        logger.info(f"Setting alias '{alias}' for {model_name} v{version}")
        
        self.client.set_registered_model_alias(
            name=model_name,
            alias=alias,
            version=version,
        )
        
        logger.info(f"Alias set: {model_name}@{alias} -> v{version}")

    def delete_model_version_alias(
        self,
        model_name: str,
        alias: str,
    ):
        """
        Delete an alias
        
        Args:
            model_name: Name of registered model
            alias: Alias to delete
        """
        self.client.delete_registered_model_alias(
            name=model_name,
            alias=alias,
        )
        logger.info(f"Deleted alias: {model_name}@{alias}")
    
    def get_model_version_by_alias(
        self,
        model_name: str,
        alias: str,
    ) -> ModelVersion:
        """
        Get model version by alias
        
        Args:
            model_name: Name of registered model
            alias: Alias name
            
        Returns:
            ModelVersion object
        """
        return self.client.get_model_version_by_alias(
            name=model_name,
            alias=alias,
        )

    def get_latest_versions(
        self,
        model_name: str,
        stages: list[str] | None = None,
    ) -> list[ModelVersion]:
        """
        Get latest versions of a model
        
        Args:
            model_name: Name of registered model
            stages: List of stages to filter (None = all stages)
            
        Returns:
            List of ModelVersion objects
        """
        return self.client.get_latest_versions(
            name=model_name,
            stages=stages,
        )
    
    def search_model_versions(
        self,
        filter_string: str = "",
        max_results: int = 100,
    ) -> list[ModelVersion]:
        """
        Search model versions
        
        Args:
            filter_string: Filter string (e.g., "name='my_model'")
            max_results: Maximum results to return
            
        Returns:
            List of ModelVersion objects
        """
        return self.client.search_model_versions(
            filter_string=filter_string,
            max_results=max_results,
        )
    
    def transition_model_version_stage(
        self,
        model_name: str,
        version: str,
        stage: str,
        archive_existing_versions: bool = True,
    ):
        """
        Transition model version to a stage
        
        Args:
            model_name: Name of registered model
            version: Version number
            stage: Target stage ("Staging", "Production", "Archived")
            archive_existing_versions: Archive other versions in target stage
        """
        logger.info(
            f"Transitioning {model_name} v{version} to {stage}"
        )
        
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing_versions,
        )
        
        logger.info(f"Model transitioned to {stage}")

    def delete_model_version(
        self,
        model_name: str,
        version: str,
    ):
        """
        Delete a model version
        
        Args:
            model_name: Name of registered model
            version: Version number
        """
        self.client.delete_model_version(
            name=model_name,
            version=version,
        )
        logger.info(f"Deleted {model_name} v{version}")
    
    def get_model_info(
        self,
        model_name: str,
    ) -> dict:
        """
        Get model information including all versions
        
        Args:
            model_name: Name of registered model
            
        Returns:
            Dictionary with model info
        """
        model = self.client.get_registered_model(model_name)
        versions = self.client.search_model_versions(f"name='{model_name}'")
        
        info = {
            "name": model.name,
            "description": model.description,
            "creation_timestamp": model.creation_timestamp,
            "last_updated_timestamp": model.last_updated_timestamp,
            "versions": [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "status": v.status,
                    "run_id": v.run_id,
                    "creation_timestamp": v.creation_timestamp,
                }
                for v in versions
            ],
        }
        
        return info

    def list_registered_models(
        self,
        max_results: int = 100
    ):
        models = self.client.search_registered_models(max_results=max_results)
        return [model.name for model in models]

    
    def promote_model(
        self,
        model_name: str,
        version: str | None,
        from_alias: str = "staging",
        to_alias: str = "champion",
        metric_name: str = "f1_score",
        require_improvement: bool = True,
    ):
        """
        Promote a model from staging to production
        
        Args:
            model_name: Model name
            version: Version to promote
            from_alias: Source alias
            to_alias: Target alias
        """
        logger.info(f"Promoting {model_name} v{version} as global {to_alias}")
        
        if version is None:
            logger.info(f"No version specified, selecting latest version of {model_name}")
            versions = self.get_latest_versions(model_name=model_name)
            if not versions:
                logger.error(f"No versions found for model {model_name}")
                return False
            version = max(versions, key=lambda v: int(v.version)).version
            logger.info(f"Using latest version: v{version}")

        candidate = self.client.get_model_version(
            name=model_name,
            version=version
        )
        candidate_metric = self.retrieve_eval_metrics_based_on_run_id(
            run_id=candidate.run_id,  # type: ignore
            metric=metric_name,
        )

        if candidate_metric is None:
            logger.error(
                f"Candidate {model_name} v{version} missing metric '{metric_name}'. Aborting."
            )
            return False
        
        logger.info(
            f"Candidate {model_name} v{version} {metric_name}: {candidate_metric:.4f}"
        )

        current_champion = None

        for mv in self.search_model_versions():
            mv_details = self.client.get_model_version(
                name=mv.name,
                version=mv.version,
            )
            if mv_details.aliases and to_alias in mv_details.aliases:
                current_champion = mv_details
                break
                
        if current_champion:
            logger.info(
            f"Current champion: {current_champion.name} v{current_champion.version}"
            )

            champion_metric = self.retrieve_eval_metrics_based_on_run_id(
                run_id=current_champion.run_id,  # type: ignore
                metric=metric_name,
            )

            if champion_metric is None:
                logger.warning(
                    f"Current champion missing '{metric_name}'. Proceeding with promotion."
                )
            else:
                logger.info(
                    f"Current champion {metric_name}: {champion_metric:.4f}"
                )

                if require_improvement and candidate_metric <= champion_metric:
                    logger.error(
                        f"Promotion blocked: candidate does not improve {metric_name} "
                        f"({candidate_metric:.4f} <= {champion_metric:.4f})"
                    )
                    return False
                improvement = candidate_metric - champion_metric
                logger.info(
                    f"Candidate improves {metric_name} by {improvement:+.4f}"
                )
            
            self.delete_model_version_alias(
                model_name=current_champion.name,
                alias=to_alias,
            )
            
        else:
            logger.info("No existing global champion found")
        

        try:
            self.delete_model_version_alias(
                model_name=model_name,
                alias=from_alias,
            )
        except Exception:
            logger.info(f"No '{from_alias}' alias to clear for {model_name} v{version}")
        
        self.set_model_version_alias(
            model_name=model_name,
            version=version,
            alias=to_alias,
        )
        logger.success(
            f"Global champion is now {model_name} v{version}"
        )
        return True