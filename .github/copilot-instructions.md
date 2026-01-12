# GitHub Copilot Instructions for OpenManus

Concise guidance for AI coding agents to be productive in this repo: architecture, workflows, conventions, and integration points with concrete examples.

## Architecture
- **Agents:** Core loop `think → act → run` in [app/agent/base.py](app/agent/base.py). Main agents: [app/agent/manus.py](app/agent/manus.py), [app/agent/mcp.py](app/agent/mcp.py), optional [app/agent/data_analysis.py](app/agent/data_analysis.py); all extend `ToolCallAgent` in [app/agent/toolcall.py](app/agent/toolcall.py).
- **Tools:** Local tools under [app/tool](app/tool), grouped via `ToolCollection` ([app/tool/tool_collection.py](app/tool/tool_collection.py)). MCP tools discovered dynamically via [app/tool/mcp.py](app/tool/mcp.py) and exposed by [app/mcp/server.py](app/mcp/server.py).
- **Flows:** Multi-agent orchestration via `PlanningFlow` in [app/flow/planning.py](app/flow/planning.py), created by [app/flow/flow_factory.py](app/flow/flow_factory.py); delegates plan steps to agents and tracks statuses.
- **LLM Abstraction:** [app/llm.py](app/llm.py) wraps OpenAI/Azure/Bedrock (`ask`, `ask_tool`, `ask_with_images`), handles streaming, retries, and token limits.
- **Config:** Centralized in [app/config.py](app/config.py), read from [config/config.toml](config/config.toml) (see examples under [config/](config)). Optional MCP refs in `config/mcp.json`.

## Workflows
- **Default Agent:**
  ```bash
  python main.py
  # or provide a prompt
  python main.py --prompt "Build a simple TODO app"
  ```
- **MCP Agent + Server:**
  ```bash
  # start MCP tools (stdio)
  python run_mcp_server.py
  # interactive agent using MCP tools
  python run_mcp.py -c stdio -i
  # one-shot task
  python run_mcp.py -c stdio -p "Search docs and summarize"
  ```
- **Multi-Agent Planning:**
  ```bash
  # enable data analysis agent in config/config.toml
  # [runflow]
  # use_data_analysis_agent = true
  python run_flow.py
  ```
- **Optional Integrations:** Daytona sandbox ([app/daytona/README.md](app/daytona/README.md)) via `python sandbox_main.py`; A2A protocol ([protocol/a2a/app/README.md](protocol/a2a/app/README.md)) via `python -m protocol.a2a.app.main`.

## Conventions
- **Prompts:** Agent `system_prompt` and `next_step_prompt` live in [app/prompt](app/prompt); `Manus` adapts `next_step_prompt` when browser tools were recently used.
- **Tool Calls:** Agents call `LLM.ask_tool(...)` with `ToolCollection.to_params()`. Assistant messages include `tool_calls`; results are captured with a `tool_call_id` and appended to memory.
- **Planning Steps:** Keep steps concise; optionally tag executors, e.g., `[data_analysis] Summarize CSV before charting`. `PlanningFlow` marks statuses and summarizes at completion.
- **Termination:** Any tool in `special_tool_names` (default includes the `terminate` tool) sets `AgentState.FINISHED`.
- **Workspace I/O:** Agents/tools read/write under [workspace/](workspace) (e.g., visualization outputs).

## Extensibility
- **Add a Tool:** Implement `BaseTool` in [app/tool](app/tool), define `to_param()` schema and `execute()` result, then register in `Manus.available_tools` or expose via MCP server.
- **Create an Agent:** Subclass `ToolCallAgent`, set `name`, `system_prompt`, `available_tools`, and `special_tool_names`; for MCP agents, connect via `MCPClients` and refresh tools.
- **Add a Flow:** Implement `BaseFlow.execute()` in [app/flow/base.py](app/flow/base.py), then map a new `FlowType` in [app/flow/flow_factory.py](app/flow/flow_factory.py).

## Gotchas
- **Token Limits:** `TokenLimitExceeded` from `LLM`; trim context or disable streaming.
- **Configuration:** Copy [config/config.example.toml](config/config.example.toml) to [config/config.toml](config/config.toml); set `llm` and optional `mcp`, `runflow` keys.
- **Windows:** Activate venv via `.venv\Scripts\activate`; install Playwright with `playwright install` for browser tooling.
- **Chart Visualization:** Follow [app/tool/chart_visualization/README.md](app/tool/chart_visualization/README.md) for Node/Python deps before enabling data analysis.

If any part is unclear (e.g., MCP config shape, planning schema, or visualization run steps), tell me which section to elaborate and I’ll refine.

## Testing & Quality Assurance
- **Test Framework:** Use `pytest` for all tests; install with `pip install pytest pytest-asyncio`.
- **Running Tests:** Execute `pytest -v` from repo root; use `-k <pattern>` to filter tests.
- **Test Location:** Integration tests in root (`test_*.py`), unit tests under `tests/` subdirectories.
- **Test Isolation:** When creating new tests for development/validation:
  - Create a separate folder (e.g., `tests/copilot_tests/` or `/tmp/test_workspace/`) for your test files
  - Create a new branch before running any tests to isolate changes
  - Clean up test artifacts after validation
- **Pre-commit Hooks:** Install via `pre-commit install`; runs `black`, `isort`, `autoflake` on commit.
- **Code Formatting:**
  - Black for Python formatting (line length 88)
  - isort with `--profile black` for import sorting
  - Remove unused imports/variables with autoflake
- **Test Coverage:** New features should include corresponding tests; follow existing test patterns.

## Dependency Management
- **Package Manager:** Use `pip` or `uv` (recommended for faster installs).
- **Requirements:** All dependencies in `requirements.txt`; pin versions with `~=` for compatibility.
- **Virtual Environment:** Always use venv or conda; activate before installing dependencies.
- **Adding Dependencies:** When adding new packages, verify compatibility with Python 3.12+.
- **MCP Configuration:** Optional MCP server connections defined in `config/mcp.json`.

## Security & Best Practices
- **API Keys:** Never commit API keys; use `config/config.toml` (gitignored) and follow `config.example.toml` template.
- **Environment Variables:** Store secrets in `.env` (gitignored); see `.env.example` for reference.
- **Input Validation:** Validate all external inputs, especially in tools that execute code or interact with filesystems.
- **Error Handling:** Use try-except blocks with informative error messages; leverage `loguru` for logging.
- **LLM Costs:** Monitor token usage via built-in cost tracking (`costs.json`); respect token limits in `config.toml`.

## Development Workflow
- **Branching:** Create feature branches from `main`; use descriptive names (e.g., `feature/add-mcp-tool`).
- **Code Review:** All changes require review; ensure tests pass and follow conventions.
- **Documentation:** Update relevant README sections when adding features; maintain inline docstrings for complex functions.
- **Logging:** Use `loguru` logger for all debug/info/error messages; avoid `print()` statements.

## Troubleshooting
- **Import Errors:** Ensure all dependencies installed and virtual environment activated.
- **LLM API Failures:** Check API keys in `config/config.toml`; verify network connectivity and rate limits.
- **Browser Tools:** Run `playwright install` if browser automation fails; requires Node.js for some features.
- **MCP Connection Issues:** Verify MCP server processes are running; check `config/mcp.json` configuration.
- **Token Limit Exceeded:** Reduce context window or increase `max_tokens` in config; consider summarizing long conversations.
- **Test Failures:** Run tests with `-v` flag for verbose output; check logs in `workspace/` directory for debugging.
