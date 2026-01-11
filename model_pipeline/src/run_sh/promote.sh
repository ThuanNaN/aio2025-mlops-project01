#!/usr/bin/env bash
set -e

# =====================
# Usage
# =====================
usage() {
  echo "Usage: $0 [options]"
  echo
  echo "Options:"
  echo "  --model-name NAME      Model name to promote (required)"
  echo "  --version VERSION     Model version to promote (required)"
  echo "  --config PATH         Path to config YAML"
  echo "  --python-script PATH  Path to register_model.py"
  echo "  -h, --help            Show this help message"
  exit 1
}

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
# Defaults
# =====================
PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/register_model.py"
CONFIG_PATH="$PROJECT_ROOT/src/config/logistic_regression.yaml"

MODEL_NAME="test_logistic_regression_v1.1"
VERSION="5"

# =====================
# Parse arguments
# =====================
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-name)
      MODEL_NAME="$2"
      shift 2
      ;;
    --version)
      VERSION="$2"
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
if [[ -z "$MODEL_NAME" ]]; then
  echo "ERROR: --model-name is required"
  usage
fi

if [[ -z "$VERSION" ]]; then
  echo "ERROR: --version is required"
  usage
fi

# =====================
# Echo config
# =====================
echo "PYTHON_SCRIPT: $PYTHON_SCRIPT"
echo "CONFIG_PATH: $CONFIG_PATH"
echo "MODEL_NAME: $MODEL_NAME"
echo "VERSION: $VERSION"

# =====================
# Promote Model
# =====================
echo "Promoting model: $MODEL_NAME version $VERSION to champion"

python "$PYTHON_SCRIPT" \
  --config "$CONFIG_PATH" \
  promote \
  --model-name "$MODEL_NAME" \
  --version "$VERSION"

echo ""
echo "Model promoted successfully!"
echo "Model is now available as: models:/$MODEL_NAME@champion"
