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


PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/register_model.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/config.yaml"

RUN_ID="0e63c769c40541c7bf27b37e1d008f49"
MODEL_NAME="model_xgboost_v0.3.2"
DESCRIPTION="XGBoost model for customer churn prediction"

echo "Registering model from run: $RUN_ID"

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    register \
    --run-id "$RUN_ID" \
    --model-name "$MODEL_NAME" \
    --description "$DESCRIPTION"

