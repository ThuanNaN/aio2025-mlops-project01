#!/usr/bin/env bash
set -e

# =====================
# Usage
# =====================
usage() {
  echo "Usage: $0 --run-id RUN_ID [options]"
  echo
  echo "Required:"
  echo "  --run-id RUN_ID            MLflow run ID to register"
  echo
  echo "Options:"
  echo "  --model-name NAME          Model name"
  echo "  --description TEXT        Model description"
  echo "  --config PATH             Path to config YAML"
  echo "  --python-script PATH      Path to register_model.py"
  echo "  -h, --help                Show this help message"
  exit 1
}

# =====================
# Defaults
# =====================
RUN_ID=""
MODEL_NAME="test_logistic_regression_v1.1"
DESCRIPTION="Logistic Regression model for customer churn prediction"

# =====================
# Resolve paths
# =====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/register_model.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/logistic_regression.yaml"

echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "PROJECT_ROOT: $PROJECT_ROOT"

# =====================
# Parse arguments
# =====================
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --model-name)
      MODEL_NAME="$2"
      shift 2
      ;;
    --description)
      DESCRIPTION="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --python-script)
      PYTHON_SCRIPT="$2"
      shift 2
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
echo "PYTHON_SCRIPT: $PYTHON_SCRIPT"
echo "CONFIG_PATH: $CONFIG_PATH"
echo "RUN_ID: $RUN_ID"
echo "MODEL_NAME: $MODEL_NAME"
echo "DESCRIPTION: $DESCRIPTION"

# =====================
# Register model
# =====================
echo "Registering model from run: $RUN_ID"

python "$PYTHON_SCRIPT" \
  --config "$CONFIG_PATH" \
  register \
  --run-id "$RUN_ID" \
  --model-name "$MODEL_NAME" \
  --description "$DESCRIPTION"
