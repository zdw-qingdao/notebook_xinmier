#!/usr/bin/env bash

set -uo pipefail

PROJECT_DIR="${CONTAINER_PROJECT_DIR:-/opt/autopipe/project}"
PYTHON_BIN="${PYTHON_BIN:-/opt/autopipe/venv/bin/python}"
MAIN_FILE="${PROJECT_DIR}/backend/main.py"
LOG_DIR="${BACKEND_LOG_DIR:-/data/backend_log}"

cleanup_expired_logs() {
    local cutoff
    local file
    local log_date

    cutoff="$(date -d '6 months ago' '+%F')"
    for file in "${LOG_DIR}"/????-??-??.txt; do
        [ -e "${file}" ] || continue
        log_date="${file##*/}"
        log_date="${log_date%.txt}"
        if [[ "${log_date}" < "${cutoff}" ]]; then
            rm -f -- "${file}"
        fi
    done
}

write_logs_by_date() {
    local line
    local current_date
    local previous_date=""

    while IFS= read -r line || [ -n "${line}" ]; do
        current_date="$(date '+%F')"
        if [ "${current_date}" != "${previous_date}" ]; then
            cleanup_expired_logs
            previous_date="${current_date}"
        fi
        printf '%s\n' "${line}" >>"${LOG_DIR}/${current_date}.txt"
    done
}

if [ ! -f "${MAIN_FILE}" ]; then
    echo "错误: 找不到 ${MAIN_FILE}" >&2
    exit 1
fi

mkdir -p "${LOG_DIR}"
cleanup_expired_logs
export PYTHONUNBUFFERED=1

"${PYTHON_BIN}" "${MAIN_FILE}" --dev "$@" 2>&1 | write_logs_by_date
exit "${PIPESTATUS[0]}"
