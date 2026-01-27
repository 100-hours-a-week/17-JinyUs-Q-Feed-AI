#!/usr/bin/env bash
set -euo pipefail

TARBALL_PATH="${1:-}"
if [[ -z "$TARBALL_PATH" ]]; then
  echo "Usage: $0 /path/to/ai-{version}.tar.gz" >&2
  exit 2
fi
if [[ ! -f "$TARBALL_PATH" ]]; then
  echo "Tarball not found: $TARBALL_PATH" >&2
  exit 2
fi

APP_DIR="/srv/qfeed/repo/ai/17-JinyUs-Q-Feed-AI"
BACKUP_DIR="/srv/qfeed/backups/ai"
SERVICE_NAME="qfeed-ai.service"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$BACKUP_DIR"

# Backup current deployment for rollback
if [[ -d "$APP_DIR" ]]; then
  tar -C "$(dirname "$APP_DIR")" -czf "$BACKUP_DIR/ai-$TS.tar.gz" "$(basename "$APP_DIR")"
  echo "Backup created: $BACKUP_DIR/ai-$TS.tar.gz"
else
  echo "No existing deployment to backup (first deploy)"
  mkdir -p "$APP_DIR"
fi

WORKDIR="$(mktemp -d)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

# Extract tarball to temp directory
tar -xzf "$TARBALL_PATH" -C "$WORKDIR"

# Find the extracted content (should be at WORKDIR root or in a subdirectory)
EXTRACTED_ROOT="$WORKDIR"
if [[ -d "$WORKDIR/deploy-package" ]]; then
  EXTRACTED_ROOT="$WORKDIR/deploy-package"
elif [[ $(ls -A "$WORKDIR" | wc -l) -eq 1 ]] && [[ -d "$WORKDIR"/* ]]; then
  # Single directory extracted
  EXTRACTED_ROOT="$(ls -d "$WORKDIR"/*)"
fi

# Verify we have the expected files
if [[ ! -f "$EXTRACTED_ROOT/main.py" ]] || [[ ! -f "$EXTRACTED_ROOT/pyproject.toml" ]]; then
  echo "Invalid tarball: expected main.py and pyproject.toml at archive root" >&2
  exit 2
fi

# Update application files in-place (preserve .venv if it exists)
# Use rsync to update files, excluding .venv and other excluded items
rsync -av --delete \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env*' \
  "$EXTRACTED_ROOT/" "$APP_DIR/"

echo "Deploy complete: $APP_DIR"

# Restart the AI service
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
  echo "Restarting $SERVICE_NAME..."
  systemctl restart "$SERVICE_NAME" || {
    echo "Warning: Failed to restart $SERVICE_NAME" >&2
    exit 1
  }
  echo "Service $SERVICE_NAME restarted successfully"
else
  echo "Warning: Service $SERVICE_NAME not found or not enabled" >&2
fi
