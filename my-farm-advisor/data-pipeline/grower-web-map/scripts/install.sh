#!/usr/bin/env bash
set -euo pipefail

# Grower Web Map — install subskill into runtime
#
# Usage:
#   export DATA_PIPELINE_DATA_ROOT=~/my-farm-advisor-runtime
#   bash scripts/install.sh

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_SRC="${DATA_PIPELINE_DATA_ROOT}/data-pipeline/grower-web-map/src"

if [ -z "${DATA_PIPELINE_DATA_ROOT:-}" ]; then
  echo "ERROR: DATA_PIPELINE_DATA_ROOT is not set"
  echo "Usage: DATA_PIPELINE_DATA_ROOT=~/my-farm-advisor-runtime bash scripts/install.sh"
  exit 1
fi

echo "Installing grower-web-map subskill..."
echo "  Source: ${SKILL_DIR}/src/"
echo "  Target: ${RUNTIME_SRC}"

mkdir -p "$RUNTIME_SRC"
rsync -r --no-times --checksum \
  "${SKILL_DIR}/src/" \
  "${RUNTIME_SRC}/"

echo "  Done."
