#!/usr/bin/env bash
set -e

# =====================
# Usage
# =====================
usage() {
  echo "Usage: $0 --run-id RUN_ID [options]"
  echo
  echo "Required:"
  echo "  --run-id RUN_ID                 MLflow run ID to evaluate"
  echo
  echo "Options:"
  echo "  --config PATH                   Path to config YAML"
  echo "  --eval-data-path PATH           Path to evaluation dataset"
  echo "  --output-path-prediction PATH   Path to save predictions"
  echo "  --python-script PATH            Path to eval script"
  echo "  --no-validate-thresholds        Disable threshold validation"
  echo "  -h, --help                      Show this help message"
  exit 1
}

# =====================
# Defaults
# =====================
RUN_ID=""
VALIDATE_THRESHOLDS=true

# =====================
# Resolve paths
# =====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/eval.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/logistic_regression.yaml"
EVAL_DATASET="/home/mlops/Repository/aio2025-mlops-project01/data-pipeline/churn_feature_store/churn_features/feature_repo/data/test.parquet"
PREDICTION_FOLDER="$PROJECT_ROOT/prediction_folder/prediction11.csv"

# =====================
# Parse arguments
# =====================
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --eval-data-path)
      EVAL_DATASET="$2"
      shift 2
      ;;
    --output-path-prediction)
      PREDICTION_FOLDER="$2"
      shift 2
      ;;
    --python-script)
      PYTHON_SCRIPT="$2"
      shift 2
      ;;
    --no-validate-thresholds)
      VALIDATE_THRESHOLDS=false
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      ;;
  esac
done

# =====================
# Validate required args
# =====================
if [[ -z "$RUN_ID" ]]; then
  echo "ERROR: --run-id is required"
  usage
fi

# =====================
# Python path
# =====================
export PYTHONPATH="$PROJECT_ROOT"

# =====================
# Echo config
# =====================
echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo "PYTHON_SCRIPT: $PYTHON_SCRIPT"
echo "CONFIG_PATH: $CONFIG_PATH"
echo "EVAL_DATASET: $EVAL_DATASET"
echo "PREDICTION_FOLDER: $PREDICTION_FOLDER"
echo "RUN_ID: $RUN_ID"
echo "VALIDATE_THRESHOLDS: $VALIDATE_THRESHOLDS"

# =====================
# Eval
# =====================
CMD=(
  python "$PYTHON_SCRIPT"
  --config "$CONFIG_PATH"
  --run-id "$RUN_ID"
  --eval-data-path "$EVAL_DATASET"
  --output-path-prediction "$PREDICTION_FOLDER"
)

if [[ "$VALIDATE_THRESHOLDS" == "true" ]]; then
  CMD+=(--validate-thresholds)
fi

"${CMD[@]}"
