
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
VERSION="2"  # Version to promote

# =====================
# Promote Model to Production
# =====================

echo "Promoting model: $MODEL_NAME version $VERSION to champion"

python "$PYTHON_SCRIPT" \
    --config "$CONFIG_PATH" \
    promote \
    --model-name "$MODEL_NAME" \
    --version "$VERSION"

echo ""
echo "Model promoted successfully!"
echo "Model is now in production as: models:/$MODEL_NAME@champion"