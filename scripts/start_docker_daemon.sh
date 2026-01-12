#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not installed. Install Docker before starting the daemon." >&2
  exit 1
fi

if docker info >/dev/null 2>&1; then
  echo "Docker daemon already running."
  exit 0
fi

if ! command -v dockerd >/dev/null 2>&1; then
  echo "dockerd binary not found. Install Docker Engine before continuing." >&2
  exit 1
fi

if pgrep -x dockerd >/dev/null 2>&1; then
  echo "dockerd process detected but docker info is failing. Check logs for details." >&2
  exit 1
fi

log_file="${DOCKERD_LOG_FILE:-/tmp/dockerd.log}"

nohup dockerd \
  --host=unix:///var/run/docker.sock \
  --iptables=false \
  --bridge=none \
  --ip-forward=false \
  --ip-masq=false \
  --userland-proxy=false \
  --storage-driver=vfs \
  > "${log_file}" 2>&1 &

for _ in $(seq 1 30); do
  if docker info >/dev/null 2>&1; then
    echo "Docker daemon is up (logs: ${log_file})."
    exit 0
  fi
  sleep 1
done

echo "Docker daemon failed to start. Review ${log_file}." >&2
exit 1
