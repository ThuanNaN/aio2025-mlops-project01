#!/usr/bin/env bash
set -e

# =====================
# Resolve paths
# =====================


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "PROJECT_ROOT: $PROJECT_ROOT"

# =====================
# Python path 
# =====================

export PYTHONPATH="$PROJECT_ROOT"

# =====================
# Variables
# =====================

PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/train.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/config.yaml"
TRAINING_DATA_PATH="/home/mlops/Repository/aio2025-mlops-project01/data-pipeline/churn_feature_store/churn_features/feature_repo/data/processed_churn_data.parquet"

RUN_NAME="baseline-xgboost_v0.3.1"
EXPERIMENT_NAME="test_churn_prediction_v0.1"

# =====================
# Train
# =====================

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    --training-data-path "$TRAINING_DATA_PATH" \
    --run-name "$RUN_NAME"

echo "Training script completed."