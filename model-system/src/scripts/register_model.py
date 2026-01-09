"""
Docstring for model-system.src.scripts.register_model
"""
import argparse
from loguru import logger

from src.mlflow_utils.model_registry import ModelRegistry
from src.utility.helper import load_config

def main():
    parser = argparse.ArgumentParser(description="Manage model registry")
    parser.add_argument(
        '--config',
        type=str,
        help='Path to the config file'
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    register_parser = subparsers.add_parser("register", help="Register a model")
    register_parser.add_argument("--run-id", required=True, help="MLflow run ID")
    register_parser.add_argument("--model-name", required=True, help="Model name")
    register_parser.add_argument("--description", help="Model description")

    alias_parser = subparsers.add_parser('set-alias', help='Set model alias')
    alias_parser.add_argument("--model-name", required=True, help="Model name")
    alias_parser.add_argument("--version", required=True, help="Model version")
    alias_parser.add_argument(
        "--alias",
        required=True,
        choices=["staging", "champion", "production"],
        help="Alias to set",
    )

    promote_parser = subparsers.add_parser("promote", help="Promote model to production")
    promote_parser.add_argument("--model-name", required=True, help="Model name")
    promote_parser.add_argument("--version", required=True, help="Model version")

    list_parser = subparsers.add_parser("list", help="List registered models")

    info_parser = subparsers.add_parser("info", help="Get model info")
    info_parser.add_argument("--model-name", required=True, help="Model name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 
    
    config = load_config(args.config)

    registry = ModelRegistry(
        tracking_uri=config["mlflow"]["tracking_uri"],
    )

    if args.command == "register":
        logger.info(f"Register model from run: {args.run_id=}")
        model_uri = f"runs:/{args.run_id}/model"

        model_version = registry.register_model(
            model_uri=model_uri,
            model_name=args.model_name,
            description=args.description,
            tags = {
                "source_run": args.run_id
            }
        )

        logger.info(f"Model registered: {args.model_name} v{model_version.version}")
        logger.info(f"Next: You can set alias with python scripts/register_model.py set-alias --model-name {args.model_name} --version {model_version.version} --alias staging")
    
    elif args.command == "set-alias":
        logger.info(f"Setting alias '{args.alias}' for {args.model_name} v{args.version}")
        
        registry.set_model_version_alias(
            model_name=args.model_name,
            version=args.version,
            alias=args.alias,
        )
        
        logger.info(f"Alias set successfully")
        logger.info(f"Model can be loaded with: models:/{args.model_name}@{args.alias}")
    
    elif args.command == "promote":
        logger.info(f"Promoting {args.model_name} v{args.version} to production")
        
        registry.promote_model(
            model_name=args.model_name,
            version=args.version,
            from_alias="staging",
            to_alias="champion",
        )
        
        logger.info("Model promoted to champion")
    
    elif args.command == "list":
        logger.info("Listing registered models...")
        
        models = registry.list_registered_models()
        
        if not models:
            logger.info("No registered models found")
        else:
            logger.info(f"Found {len(models)} registered models:")
            for model_name in models:
                logger.info(f"  - {model_name}")
    
    elif args.command == "info":
        logger.info(f"Getting info for model: {args.model_name}")
        
        info = registry.get_model_info(args.model_name)
        
        logger.info("=" * 60)
        logger.info(f"Model: {info['name']}")
        logger.info(f"Description: {info['description']}")
        logger.info(f"Created: {info['creation_timestamp']}")
        logger.info(f"Last Updated: {info['last_updated_timestamp']}")
        logger.info("\nVersions:")
        
        for version in info['versions']:
            logger.info(f"  v{version['version']}: stage={version['stage']}, status={version['status']}")


if __name__ == "__main__":
    main()