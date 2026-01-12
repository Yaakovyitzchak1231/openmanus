# OpenManus → Opus 4.5 Replication - Master Task List

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
