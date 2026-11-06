#!/usr/bin/env bash
set -euo pipefail

SVAP_DEV="${SVAP_DEV:-/opt/svap-dev}"
PROJECT_ROOT="${PROJECT_ROOT:-/project}"
LOW_CODE="${PROJECT_ROOT}/low-code-platform"
NR_DIR="${LOW_CODE}/node-red"
USER_DIR="${USER_DIR:-/data/node-red}"
STAMP="${STAMP:-/data/node-red/.install-stamp}"
PLUGIN_LIST="${SVAP_DEV}/dev-plugin-packages.txt"
USER_PKG="${SVAP_DEV}/dev-userDir-package.json"

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red() { printf '\033[31m%s\033[0m\n' "$*"; }

install_plugins() {
  while IFS= read -r rel || [[ -n "${rel}" ]]; do
    rel="${rel%%#*}"
    rel="$(echo "${rel}" | xargs)"
    [[ -z "${rel}" ]] && continue
    src="${LOW_CODE}/${rel}"
    [[ -f "${src}/package.json" ]] || continue
    green "plugin: ${rel}"
    (
      cd "${src}"
      pnpm -r install
      if [[ -f vue-ui/package.json ]] && grep -q '"build-only"' vue-ui/package.json; then
        (cd vue-ui && pnpm run build-only)
        pnpm run --if-present build
      else
        pnpm -r run --if-present build
      fi
    )
  done < "${PLUGIN_LIST}"
}

do_install() {
  green "=== Node-RED ==="
  (cd "${NR_DIR}" && npm install && npm run build)

  green "=== plugin-nodes ==="
  install_plugins

  green "=== userDir ==="
  mkdir -p "${USER_DIR}"
  cp -f "${USER_PKG}" "${USER_DIR}/package.json"
  [[ -f "${USER_DIR}/settings.js" ]] || cp -f "${NR_DIR}/packages/node_modules/node-red/settings.js" "${USER_DIR}/settings.js"
  [[ -f "${USER_DIR}/flows.json" ]] || echo '[]' > "${USER_DIR}/flows.json"
  (
    cd "${USER_DIR}"
    rm -rf node_modules package-lock.json
    npm install
    if [[ -d node_modules/better-sqlite3 ]]; then
      rm -rf node_modules/better-sqlite3/prebuilds
      npm rebuild better-sqlite3 --build-from-source
    fi
  )
  touch "${STAMP}"
  green "install finished"
}

if [[ "${FULL_REBUILD:-0}" == "1" ]]; then
  rm -f "${STAMP}"
fi

if [[ -f "${STAMP}" ]]; then
  green "already installed (${STAMP}); use FULL_REBUILD=1 to reinstall"
  exit 0
fi

do_install
