#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTERNAL_DIR="${ROOT_DIR}/external"
LOG_FILE="${ROOT_DIR}/claude-progress.txt"

mkdir -p "${EXTERNAL_DIR}"
: > "${EXTERNAL_DIR}/.gitkeep"

log_section() {
  printf "\n## %s\n" "$1" >> "${LOG_FILE}"
}

log_line() {
  printf "- %s\n" "$1" >> "${LOG_FILE}"
}

log_section "External Clone Log"
log_line "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
log_line "Notes: Running clone script"
log_line "Failures (log clone errors or missing repos):"

clone_repo() {
  local repo_url="$1"
  local target_dir="$2"

  if [[ -d "${target_dir}/.git" ]]; then
    log_line "SKIP: ${repo_url} already cloned"
    return
  fi

  log_line "CLONE: ${repo_url} -> ${target_dir}"
  if ! git clone "${repo_url}" "${target_dir}"; then
    log_line "FAIL: ${repo_url}"
  fi
}

clone_repo https://github.com/laude-institute/harbor.git "${EXTERNAL_DIR}/harbor"
clone_repo https://github.com/promptfoo/promptfoo.git "${EXTERNAL_DIR}/promptfoo"
clone_repo https://github.com/braintrustdata/autoevals.git "${EXTERNAL_DIR}/autoevals"
clone_repo https://github.com/langchain-ai/langchain.git "${EXTERNAL_DIR}/langchain"
clone_repo https://github.com/langfuse/langfuse.git "${EXTERNAL_DIR}/langfuse"
clone_repo https://github.com/safety-research/petri.git "${EXTERNAL_DIR}/petri"
clone_repo https://github.com/sierra-research/tau2-bench.git "${EXTERNAL_DIR}/tau2-bench"
clone_repo https://github.com/SWE-bench/SWE-bench.git "${EXTERNAL_DIR}/swe-bench"
clone_repo https://github.com/xlang-ai/OSWorld.git "${EXTERNAL_DIR}/osworld"
clone_repo https://github.com/fchollet/ARC-AGI.git "${EXTERNAL_DIR}/arc-agi"
clone_repo https://github.com/web-arena-x/webarena.git "${EXTERNAL_DIR}/webarena"
clone_repo https://github.com/idavidrein/gpqa.git "${EXTERNAL_DIR}/gpqa"
clone_repo https://github.com/safety-research/SHADE-Arena.git "${EXTERNAL_DIR}/shade-arena"
clone_repo https://github.com/redwoodresearch/subversion-strategy-eval.git "${EXTERNAL_DIR}/subversion-strategy-eval"
clone_repo https://github.com/laude-institute/terminal-bench.git "${EXTERNAL_DIR}/terminal-bench"
clone_repo https://github.com/Future-House/LAB-Bench.git "${EXTERNAL_DIR}/lab-bench"
clone_repo https://github.com/centerforaisafety/hle.git "${EXTERNAL_DIR}/hle"
clone_repo https://github.com/TIGER-AI-Lab/MMLU-Pro.git "${EXTERNAL_DIR}/mmlu-pro"
clone_repo https://github.com/MMMU-Benchmark/MMMU.git "${EXTERNAL_DIR}/mmmu"
clone_repo https://github.com/anthropics/claude-cookbooks.git "${EXTERNAL_DIR}/claude-cookbooks"
clone_repo https://github.com/9600dev/llmvm.git "${EXTERNAL_DIR}/llmvm"
clone_repo https://github.com/modelcontextprotocol/servers.git "${EXTERNAL_DIR}/mcp-servers"
clone_repo https://github.com/anthropics/claude-agent-sdk-python.git "${EXTERNAL_DIR}/claude-agent-sdk-python"
clone_repo https://github.com/anthropics/claude-agent-sdk-typescript.git "${EXTERNAL_DIR}/claude-agent-sdk-typescript"
clone_repo https://github.com/puppeteer/puppeteer.git "${EXTERNAL_DIR}/puppeteer"

log_section "Directory Snapshot"
log_line "$(ls "${EXTERNAL_DIR}")"
