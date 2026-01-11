# Recommended Security and Quality Fixes

This document outlines the recommended fixes identified in the comprehensive code review.

## Priority 1: Security Fix (Recommended Before Production)

### TestRunner Command Injection Prevention

**File**: `app/tool/test_runner.py`  
**Lines**: 63-64  
**Severity**: Medium  
**Estimated Time**: 30 minutes

**Current Code**:
```python
cmd = [sys.executable, "-m", "pytest", test_path] + test_args
```

**Issue**: `test_path` and `test_args` are not validated, creating potential command injection risk.

**Recommended Fix**:
```python
from pathlib import Path
from app.config import config

async def execute(
    self,
    test_path: str,
    test_args: Optional[List[str]] = None,
    timeout: int = 120,
) -> ToolResult:
    """Execute pytest on the specified test path with security validation."""
    if test_args is None:
        test_args = ["-v"]

    # Validate test_path exists and is a file/directory
    test_path_obj = Path(test_path).resolve()
    if not test_path_obj.exists():
        return self.fail_response(f"Test path not found: {test_path}")
    
    # Optional: Ensure test path is within workspace for additional security
    try:
        workspace_root = Path(config.workspace_root).resolve()
        test_path_obj.relative_to(workspace_root)
    except ValueError:
        logger.warning(f"Test path {test_path} is outside workspace directory")
        # Decide: allow or reject based on security requirements
    
    # Whitelist allowed pytest arguments to prevent injection
    ALLOWED_ARGS = {
        "-v", "-vv", "-vvv",      # Verbosity
        "-x", "-s",               # Behavior
        "--tb=short", "--tb=long", "--tb=no",  # Traceback
        "--maxfail=1", "--maxfail=2",  # Failure limits
    }
    
    # Filter args: allow whitelisted flags and -k patterns
    filtered_args = []
    for arg in test_args:
        if arg in ALLOWED_ARGS:
            filtered_args.append(arg)
        elif arg.startswith("-k=") or arg.startswith("--maxfail="):
            # Allow test selection patterns
            filtered_args.append(arg)
        else:
            logger.warning(f"Ignoring non-whitelisted pytest argument: {arg}")
    
    # Build pytest command with validated inputs
    cmd = [sys.executable, "-m", "pytest", str(test_path_obj)] + filtered_args
    
    logger.info(f"Running pytest: {' '.join(cmd)}")
    
    # Rest of the method remains the same...
```

**Testing**:
```python
# Add to test_runner.py or create test_test_runner.py
async def test_path_validation():
    runner = TestRunner()
    
    # Test 1: Non-existent path
    result = await runner.execute("/fake/path.py")
    assert "not found" in result.error
    
    # Test 2: Allowed args
    result = await runner.execute("test_file.py", ["-v", "-x"])
    # Should execute normally
    
    # Test 3: Disallowed args filtered
    result = await runner.execute("test_file.py", ["-v", "--dangerous-flag"])
    # --dangerous-flag should be filtered out
```

---

## Priority 2: Reviewer Grade Safety

**File**: `app/agent/reviewer.py`  
**Lines**: 219-220  
**Severity**: Medium  
**Estimated Time**: 15 minutes

**Current Code**:
```python
else:
    logger.warning("Could not determine grade from review, defaulting to PASS")
    return "PASS"
```

**Issue**: Defaults to PASS when grade is unclear, potentially allowing failing code through.

**Recommended Fix**:
```python
else:
    logger.warning("Could not determine grade from review, defaulting to FAIL for safety")
    return "FAIL"
```

**Alternative (More Conservative)**:
```python
else:
    logger.error("Could not determine grade from review - invalid format")
    raise ValueError("Review must include explicit 'GRADE: PASS' or 'GRADE: FAIL'")
```

**Rationale**: Failing safe prevents false positives where broken code is marked as passing.

---

## Priority 3: Configuration Enhancements

### Add Reflection Interval Configuration

**File**: `app/config.py`  
**Lines**: Add to AgentSettings (around line 63-75)  
**Severity**: Low  
**Estimated Time**: 30 minutes

**Current**: Reflection interval hardcoded at 5 steps

**Recommended Addition**:
```python
class AgentSettings(BaseModel):
    high_effort_mode: bool = Field(
        default=False, description="Enable high-effort mode with extended steps"
    )
    max_steps_normal: int = Field(
        default=20, description="Maximum steps in normal mode"
    )
    max_steps_high_effort: int = Field(
        default=50, description="Maximum steps in high-effort mode"
    )
    enable_reflection: bool = Field(
        default=True, description="Enable reflection prompts in high-effort mode"
    )
    # NEW: Add configurable reflection interval
    reflection_interval: int = Field(
        default=5, 
        description="Number of steps between reflection prompts (only in high-effort mode)"
    )
```

**Update config.example.toml**:
```toml
[agent]
high_effort_mode = false
max_steps_normal = 20
max_steps_high_effort = 50
enable_reflection = true
reflection_interval = 5  # Reflect every N steps in high-effort mode
```

**Update Manus agent to use config**:
```python
# In app/agent/manus.py, wherever reflection check happens
def _should_reflect(self) -> bool:
    """Check if we should inject a reflection prompt at current step."""
    if not getattr(config.agent, "enable_reflection", False):
        return False
    if self.effort_level != "high":
        return False
    
    reflection_interval = getattr(config.agent, "reflection_interval", 5)
    return self.current_step > 0 and self.current_step % reflection_interval == 0
```

---

## Priority 4: Documentation Improvements

### Document MCP Configuration Precedence

**File**: `README.md` or `DEPLOY.md`  
**Severity**: Low  
**Estimated Time**: 15 minutes

**Add Section**:
```markdown
## MCP Configuration

OpenManus supports Model Context Protocol (MCP) servers for dynamic tool discovery.

### Configuration Files

MCP servers can be configured in two ways:

1. **Primary: config/config.toml** (Recommended)
   ```toml
   [mcp_config.servers.filesystem]
   type = "stdio"
   command = "npx"
   args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"]
   ```

2. **Override: config/mcp.json** (Optional)
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
       }
     }
   }
   ```

### Precedence

- If `mcp.json` exists, it **overrides** servers defined in `config.toml`
- If `mcp.json` doesn't exist, servers from `config.toml` are used
- This allows environment-specific overrides without modifying the main config

### Best Practices

- Use `config.toml` for default/shared configuration
- Use `mcp.json` for local development overrides (gitignored)
- Add `config/mcp.json` to `.gitignore` if not already present
```

---

## Optional Improvements (Post-Vision Implementation)

### 1. Plan Validation Enhancement

**File**: `app/flow/planning.py`  
**Lines**: Around 220-241 (fallback plan creation)  
**Estimated Time**: 1 hour

Add validation to ensure generated plan matches request:

```python
async def _validate_plan(self, plan: dict, request: str) -> bool:
    """Validate that generated plan is reasonable for the request."""
    steps = plan.get("steps", [])
    
    # Basic checks
    if len(steps) < 3:
        logger.warning("Plan has too few steps (< 3)")
        return False
    
    if len(steps) > 15:
        logger.warning("Plan has too many steps (> 15)")
        return False
    
    # Optional: Use LLM to validate plan relevance
    validation_prompt = f"""
    Request: {request}
    
    Generated Plan:
    {json.dumps(steps, indent=2)}
    
    Does this plan reasonably address the request? Answer only YES or NO.
    """
    
    response = await self.llm.ask(
        messages=[Message.user_message(validation_prompt)],
        system_msgs=[Message.system_message("You are a plan validator.")]
    )
    
    return "YES" in response.content.upper()
```

### 2. Token Limit Handling in Flows

**Files**: `app/flow/planning.py`, `app/flow/review.py`  
**Estimated Time**: 1 hour

Add explicit handling for TokenLimitExceeded:

```python
# In PlanningFlow.execute()
try:
    step_result = await self._execute_step(executor, step_info)
except TokenLimitExceeded as e:
    logger.error(f"Token limit exceeded at step {self.current_step_index}: {e}")
    # Attempt recovery: summarize context and retry
    await self._summarize_context()
    step_result = await self._execute_step(executor, step_info)
```

### 3. Cost Tracking Tests

**File**: Create `tests/test_cost_tracking.py`  
**Estimated Time**: 2 hours

```python
import pytest
from app.llm import LLM
from app.config import config

@pytest.mark.asyncio
async def test_cost_tracking():
    """Verify cost tracking works and alerts at thresholds."""
    llm = LLM()
    
    # Make a small request
    response = await llm.ask([Message.user_message("Hello")])
    
    # Check costs.json was updated
    import json
    with open("costs.json") as f:
        costs = json.load(f)
    
    assert len(costs) > 0
    assert "input_tokens" in costs[-1]
    assert "output_tokens" in costs[-1]
    assert "cost" in costs[-1]

@pytest.mark.asyncio
async def test_budget_alert():
    """Test that budget alerts trigger at $10, $15, $18."""
    # Mock high token usage to trigger alerts
    # (Implementation depends on how alerts are implemented)
    pass
```

---

## Implementation Order

1. **Immediate** (Before vision tasks):
   - [ ] TestRunner security fix (30 min)

2. **Parallel with vision work**:
   - [ ] Reviewer grade default (15 min)
   - [ ] Reflection interval config (30 min)
   - [ ] MCP documentation (15 min)

3. **After vision implementation**:
   - [ ] Plan validation (1 hour)
   - [ ] Token limit handling (1 hour)
   - [ ] Cost tracking tests (2 hours)
   - [ ] Unit tests for tools (4-8 hours)

---

## Testing Recommendations

After implementing fixes:

1. **Run focused tests**:
   ```bash
   pytest app/tool/test_runner.py -v  # If test exists
   pytest test_review_flow.py -v
   pytest test_tool_selection.py -v
   ```

2. **Run full test suite**:
   ```bash
   ./Opus4.5Review_1_11_2026/run_tests.sh
   ```

3. **Manual verification**:
   - Test TestRunner with edge cases (invalid paths, malicious args)
   - Test Reviewer with unclear outputs to verify FAIL default
   - Test reflection at configured intervals

---

## Conclusion

These fixes enhance security and robustness without blocking vision task implementation. The TestRunner security fix is highest priority and should be implemented before production deployment.

All other fixes are improvements that can be addressed in parallel with or after vision capabilities.
