#!/bin/bash
set -euo pipefail

# AI Music Station - Host worker setup for Apple Silicon
# This script sets up the ACE-Step worker on the Mac mini host.
# The worker runs outside Docker for MPS/MLX GPU access.

echo "=== AI Music Station Worker Setup ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ACESTEP_DIR="${HOME}/ace-step"

cd "$PROJECT_DIR"

# 1. Check Python version
echo "Checking Python..."
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python ${PYTHON_VERSION}"

# 2. Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
echo "  uv: $(uv --version)"

# 3. Clone ACE-Step if not present
if [ ! -d "$ACESTEP_DIR" ]; then
    echo "Cloning ACE-Step v1.5..."
    git clone https://github.com/ace-step/ACE-Step-1.5.git "$ACESTEP_DIR"
else
    echo "  ACE-Step found at ${ACESTEP_DIR}"
fi

# 4. Install ACE-Step dependencies
echo "Installing ACE-Step dependencies..."
cd "$ACESTEP_DIR"
uv sync

# 5. Download models (if not already present)
echo "Downloading ACE-Step models (this may take a while on first run)..."
uv run acestep-download || echo "  Model download skipped (may already exist)"

# 6. Install worker dependencies
echo "Installing worker dependencies..."
cd "$PROJECT_DIR"
pip3 install -r requirements.txt

# 7. Create generated_tracks directory
mkdir -p generated_tracks/lofi generated_tracks/anime generated_tracks/jazz

# 8. Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example — edit it with your passwords"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the ACE-Step API server:"
echo "  cd ${ACESTEP_DIR} && uv run acestep-api"
echo ""
echo "To start the worker:"
echo "  cd ${PROJECT_DIR} && python3 -m worker"
echo ""
echo "To start the Docker services:"
echo "  cd ${PROJECT_DIR} && docker compose up -d"
