#!/usr/bin/env bash
set -euo pipefail

SVAP_DEV="${SVAP_DEV:-/opt/svap-dev}"
PROJECT_ROOT="${PROJECT_ROOT:-/project}"
LOW_CODE="${PROJECT_ROOT}/low-code-platform"
NR_DIR="${LOW_CODE}/node-red"
USER_DIR="${USER_DIR:-/data/node-red}"
STAMP="${STAMP:-/data/node-red/.install-stamp}"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }

if [[ ! -f "${STAMP}" ]]; then
  red "not installed yet — run: install-svap-designer"
  exit 1
fi

if [[ ! -f "${NR_DIR}/packages/node_modules/node-red/red.js" ]]; then
  red "node-red not built — run: install-svap-designer  (or FULL_REBUILD=1 install-svap-designer)"
  exit 1
fi

green "starting Node-RED http://127.0.0.1:${PORT:-21880}  (Ctrl+C to stop)"
cd "${NR_DIR}"
exec node packages/node_modules/node-red/red.js -u "${USER_DIR}"
