#!/usr/bin/env bash
set -e

# =====================
# Parse arguments
# =====================
RUN_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$RUN_ID" ]]; then
  echo "ERROR: --run-id is required"
  exit 1
fi


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

MODEL_NAME="model_xgboost_v0.3.2"
DESCRIPTION="XGBoost model for customer churn prediction"

echo "Registering model from run: $RUN_ID"

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    register \
    --run-id "$RUN_ID" \
    --model-name "$MODEL_NAME" \
    --description "$DESCRIPTION"

