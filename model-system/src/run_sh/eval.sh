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


PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/eval.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/config.yaml"
EVAL_DATASET="/home/mlops/Repository/aio2025-mlops-project01/data-pipeline/churn_feature_store/churn_features/feature_repo/data/test.parquet"
PREDICTION_FOLDER="$PROJECT_ROOT/prediction_folder/prediction11.csv"

echo "$PROJECT_ROOT"

# =====================
# Eval
# =====================

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    --run-id "$RUN_ID" \
    --eval-data-path "$EVAL_DATASET"  \
    --output-path-prediction "$PREDICTION_FOLDER"
