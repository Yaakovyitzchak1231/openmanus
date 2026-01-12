# OpenManus → Claude Opus 4.5 / Claude Code Replication Plan

## Scope
This plan is the single source of truth. It replaces prior phase checklists to avoid confusion.

## Priority Track (Implement Now)
These items align with the referenced Anthropic pages and focus on immediate replication of Opus 4.5 / Claude Code capabilities.

### 1) Agent Harness + SDK Alignment
- [ ] Define a minimal harness interface (inputs, tool registry, memory adapter, trace hooks)
- [ ] Implement Claude Code-style agent loop orchestration
- [ ] Add structured transcripts/outcomes for runs

### 2) Tool Calling + Advanced Tool Use
- [ ] Centralize tool registry for dynamic discovery
- [ ] Add tool selection hints and execution telemetry
- [ ] Standardize tool errors + retries

### 3) MCP Code Execution Path
- [ ] Add MCP code execution mode to reduce tool token overhead
- [ ] Define sandbox limits + safe execution defaults
- [ ] Document when to use code execution vs direct tool calls

### 4) Context Editing + Memory Tool
- [ ] Add context compaction hooks for long conversations
- [ ] Implement memory tool adapters (in-memory + persistent)

### 5) Effort Control
- [ ] Support effort parameter in model config and surface it in runs

### 6) Minimal Eval Harness
- [ ] Define eval primitives (task, trial, graders, transcript, outcome)
- [ ] Create small capability + regression suites
- [ ] Log capability + safety results, even for minimal suites

### 7) Long-Running Agent Hygiene
- [ ] Add `init.sh` to start dev server + validate environment
- [ ] Keep feature list and progress logs updated per session

## Secondary Track (Planned, Later)
These are deferred until the priority track is functional.

> Note: The legacy phased plan is preserved below for historical context. The priority track above supersedes it for sequencing.

### External Tools + Benchmarks (Deferred)
- [ ] Initialize external repo directory (`external/` + `.gitkeep`)
- [ ] Optional helper: `scripts/clone_external.sh` (batch clone + log to `claude-progress.txt`)
- [ ] Clone open-source frameworks/tools/benchmarks into `/external` (log failures to `claude-progress.txt`)
  - **Article 1 (Demystifying Evals)**
    - [ ] `git clone https://github.com/laude-institute/harbor.git external/harbor` (Terminal-Bench harness)
    - [ ] `git clone https://github.com/promptfoo/promptfoo.git external/promptfoo` (prompt testing; `npm install`)
    - [ ] `git clone https://github.com/braintrustdata/autoevals.git external/autoevals` (model graders; `pip install -e`)
    - [ ] `git clone https://github.com/langchain-ai/langchain.git external/langchain` (LangSmith datasets)
    - [ ] `git clone https://github.com/langfuse/langfuse.git external/langfuse` (self-hosted observability)
  - **Article 2 (Claude Opus 4.5 News)**
    - [ ] `git clone https://github.com/safety-research/petri.git external/petri` (alignment auditing)
    - [ ] `git clone https://github.com/sierra-research/tau2-bench.git external/tau2-bench` (multi-turn agentic evals)
  - **Article 3 (System Card)**
    - [ ] `git clone https://github.com/SWE-bench/SWE-bench.git external/swe-bench` (coding benchmarks)
    - [ ] `git clone https://github.com/xlang-ai/OSWorld.git external/osworld` (computer-use tasks)
    - [ ] `git clone https://github.com/fchollet/ARC-AGI.git external/arc-agi` (reasoning)
    - [ ] `git clone https://github.com/web-arena-x/webarena.git external/webarena` (web agent tasks)
    - [ ] `git clone https://github.com/idavidrein/gpqa.git external/gpqa` (graduate QA)
    - [ ] `git clone https://github.com/safety-research/SHADE-Arena.git external/shade-arena` (safety evals)
    - [ ] `git clone https://github.com/redwoodresearch/subversion-strategy-eval.git external/subversion-strategy-eval`
    - [ ] `git clone https://github.com/laude-institute/terminal-bench.git external/terminal-bench`
    - [ ] `git clone https://github.com/Future-House/LAB-Bench.git external/lab-bench`
      - [ ] `huggingface-cli download futurehouse/lab-bench --local-dir external/lab-bench/dataset`
    - [ ] `git clone https://github.com/centerforaisafety/hle.git external/hle`
      - [ ] `huggingface-cli download cais/hle --local-dir external/hle/dataset`
    - [ ] `git clone https://github.com/TIGER-AI-Lab/MMLU-Pro.git external/mmlu-pro`
    - [ ] `git clone https://github.com/MMMU-Benchmark/MMMU.git external/mmmu`
      - [ ] `huggingface-cli download MMMU/MMMU --local-dir external/mmmu/dataset`
    - [ ] BrowseComp-Plus (dataset only)
      - [ ] `huggingface-cli download Tevatron/browsecomp-plus-corpus --local-dir external/browsecomp-plus`
    - [ ] CyberGym / FinanceAgent / SpreadsheetBench / Vending-Bench 2: conceptual integrations only
      - [ ] `pip install openpyxl` (spreadsheet support)
  - **Article 5 (Advanced Tool Use)**
    - [ ] `git clone https://github.com/anthropics/claude-cookbooks.git external/claude-cookbooks`
    - [ ] `git clone https://github.com/9600dev/llmvm.git external/llmvm`
  - **Article 8 (Code Execution with MCP)**
    - [ ] `git clone https://github.com/modelcontextprotocol/servers.git external/mcp-servers`
  - **Article 9 (Agent SDK)**
    - [ ] `git clone https://github.com/anthropics/claude-agent-sdk-python.git external/claude-agent-sdk-python`
    - [ ] `git clone https://github.com/anthropics/claude-agent-sdk-typescript.git external/claude-agent-sdk-typescript`
  - **Article 10 (Effective Harnesses)**
    - [ ] `git clone https://github.com/puppeteer/puppeteer.git external/puppeteer` (E2E browser evals; `npm install puppeteer`)
- [ ] Verification + tracking
  - [ ] Run `ls external` and log output in `claude-progress.txt`
  - [ ] Add usage notes per repo (Harbor for Terminal-Bench, Promptfoo for rubric grading, etc.)
- [ ] Commit: `git add external claude-progress.txt feature_list.json && git commit -m "Cloned all open-source frameworks from articles"`

---

## Legacy Phased Plan (Historical Reference)

## Phase 1: Preparation and Research ✅ COMPLETE

- [x] Study Opus 4.5's orchestrator logic and multi-stage reasoning
- [x] Set up and familiarize with OpenManus repo
- [x] Configure LLM (OpenRouter + Daytona)
- [x] Test baseline runs - **SUCCESSFUL**: 6,336 tokens
- [x] Document repo structure (architecture_map.md)

## Phase 2: Core Implementation ✅ COMPLETE

- [x] Enhanced PlanningFlow with CoT decomposition (5-10 steps)
- [x] Added verification loop with 3-retry capability
- [x] Integrated cost tracking into orchestrator
- [x] Implemented high-effort mode (20→50 max_steps)
- [x] Created Reviewer agent and ReviewFlow
- [x] Integrated ReviewFlow into run_flow.py with config toggle
- [x] Tested self-correction with factorial task - **SUCCESSFUL**

## Phase 3: Prompt Engineering ✅ COMPLETE

- [x] Enhanced Manus system prompt with 6-step CoT framework
- [x] Enhanced Reviewer prompt with systematic analysis checklist
- [x] Added self-reflection mechanism (every 5 steps in high-effort mode)
- [x] Tested reflection with real web scraper task - **VERIFIED**
- [x] Run manual verification: SpaceX research task (gpt-4o upgrade) - **VERIFIED ✅**
  - Confirmed "Information Integrity" guidelines followed
  - Observed 27-step thorough research
  - Verified multi-source cross-referencing
- [ ] Optional: Full REST API reflection effectiveness test

## Phase 3 Remaining: Advanced Enhancements (OPTION A - Complete Original Vision)

**Resume After Weekend**: Continue with full implementation of remaining Phase 3 features

### 🛠️ Tool Integration & MCP Enhancement

- [x] **Extend Built-in Tools**
  - [x] Create test_runner.py for automated pytest execution
  - [x] Integrate test runner into Reviewer agent workflow
  - [x] Configure Git LFS and track large files (*.vsix, assets)
  - [ ] Add vision capabilities via [llm.vision] config in config.toml
  - [ ] Test vision with image-based tasks
- [x] **Context-Aware Tool Selector**
  - [x] Tool selection hints implemented in PlanningFlow._format_tool_selection_hint()
  - **DEFERRED**: Separate tool_selector.py module not needed - current inline implementation is sufficient and more flexible for agent-based tool selection
- [x] **MCP Server Configuration**
  - [x] Configure filesystem MCP server in config.toml (primary source)
  - [x] Maintain backward compatibility with mcp.json (override)
  - [x] Support multiple MCP servers running simultaneously
  - [x] Add MCP tool discovery logging (implemented in manus.py lines 113-132)
  - [x] Register ReviewFlow in FlowFactory for proper orchestration

### 🏗️ Hierarchical Orchestrator (Complex - High Value)

- [ ] **Design & Planning**
  - [ ] Design task graph structure (consider using networkx)
  - [ ] Define sub-agent types: CodeExecutor, SearchAgent, DataAnalysisAgent
  - [ ] Plan branching/merging logic
- [ ] **Implementation**
  - [ ] Create app/flow/hierarchical.py
  - [ ] Implement HierarchicalFlow class
  - [ ] Add dynamic sub-agent spawning based on task type
  - [ ] Create app/agent/synthesizer.py for output merging
- [ ] **Integration**
  - [ ] Add FlowType.HIERARCHICAL to flow_factory.py
  - [ ] Register HierarchicalFlow in FlowFactory
  - [ ] Add config toggle: use_hierarchical_flow
- [ ] **Testing**
  - [ ] Test with complex branching scenario
  - [ ] Verify parallel execution works
  - [ ] Test synthesizer merges outputs correctly

### 🔄 External Feedback Loops (HITL)

- [x] **Human-in-the-Loop Integration**
  - [x] Add HITL pause in PlanningFlow after step completion
  - [x] Use input() for user feedback collection
  - [x] Feed user feedback back to agent for next iteration
  - [x] Add config toggle: enable_hitl in config.toml
- [x] **Feedback Logging**
  - [x] Create app/tool/feedback_logger.py
  - [x] Set up SQLite database for feedback storage
  - [x] Log HITL corrections and error patterns
  - [x] Test feedback retrieval and analysis
- [x] **Testing**
  - [x] Test HITL with intentionally buggy code
  - [x] Verify feedback improves output quality
  - [x] Test feedback database queries

### ⚡ Performance Optimizations

- [ ] **Caching Implementation**
  - [ ] Add functools.lru_cache for sub-task outputs
  - [ ] Implement hash-based caching in PlanningFlow
  - [ ] Test cache hit/miss rates
  - [ ] Verify caching reduces redundant LLM calls
- [ ] **Monitoring & Metrics**
  - [ ] Create app/utils/metrics.py
  - [ ] Track tokens/step, latency, success rate
  - [ ] Add logging export functionality
  - [ ] Set up metrics dashboard (optional)
- [ ] **Optimization Features**
  - [ ] Add early-stop thresholds (improvement < 5%)
  - [ ] Implement asyncio.gather() for parallel sub-agents
  - [ ] Add timeouts to tool calls (browser, search)
  - [ ] Test performance improvements

## Phase 4: Testing and Iteration

- [ ] **Benchmarking**
  - [ ] Set up HumanEval or custom coding benchmark suite
  - [ ] Run benchmarks on current implementation
  - [ ] Compare results against Opus 4.5 (if accessible)
  - [ ] Log results to benchmarks/results.json
  - [ ] Analyze failures and iterate
- [ ] **Integration & Documentation**
  - [ ] Commit all changes to git with proper tagging
  - [ ] Test full flows with run_flow.py
  - [ ] Add cost monitoring dashboard
  - [ ] Document final system architecture
  - [ ] Create comprehensive usage guide
  - [ ] Write README with examples

## Optional/Low Priority

- [ ] RL-based tuning (cloud GPU required, budget permitting)
- [ ] Multi-LLM integration (task-based model routing)
- [ ] Scalability testing (max_steps 100+)

## Current Status

**Last Completed**: SpaceX Research Verification (Phase 3) & Git LFS Setup
**In Progress**: Implementing External Feedback Loops (HITL)
**Next Up**: Hierarchical Orchestrator Implementation
