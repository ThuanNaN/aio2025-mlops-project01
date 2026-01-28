"""
Docstring for model_pipeline.src.utility.helper
"""
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv


def load_env(env_path: str | None = None) -> None:
    """
    Load environment variables from .env file
    
    Args:
        env_path: Path to .env file. If None, searches in model_pipeline directory.
    """
    if env_path is None:
        # Find .env in model_pipeline directory
        current_file = Path(__file__).resolve()
        model_pipeline_dir = current_file.parents[2]  # Go up: utility -> src -> model_pipeline
        env_path = model_pipeline_dir / ".env"
    else:
        env_path = Path(env_path)
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback: try .env.example if .env doesn't exist
        example_path = env_path.parent / ".env.example"
        if example_path.exists():
            load_dotenv(example_path)


def load_config(config_path: str) -> dict:
    """Load configuration"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)