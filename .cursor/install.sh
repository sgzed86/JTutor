#!/usr/bin/env bash
# Idempotent dependency refresh for Jtutor Cloud Agent environments.
# Runs after the repository is checked out. Safe to run repeatedly.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "[install] Installing backend Python dependencies"
python3 -m pip install --user -r backend/requirements.txt

echo "[install] Installing root Node dependencies"
npm install

echo "[install] Installing desktop UI Node dependencies"
npm install --prefix apps/desktop

echo "[install] Done"
