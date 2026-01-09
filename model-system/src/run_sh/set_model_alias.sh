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


MODEL_NAME="model_xgboost_v0.3.2"
VERSION="2"  # Version number from registration output
ALIAS="staging"  # Options: staging, champion, production

echo "Setting alias '$ALIAS' for model: $MODEL_NAME version $VERSION"

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    set-alias \
    --model-name "$MODEL_NAME" \
    --version "$VERSION" \
    --alias "$ALIAS"

echo ""
echo "Alias set successfully!"
echo "Model can now be loaded with: models:/$MODEL_NAME@$ALIAS"


