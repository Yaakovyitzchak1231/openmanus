# OpenManus Testing Plan & Execution Guide

**Date**: January 11, 2026  
**Purpose**: Define testing strategy and execution responsibilities for validating Phase 1-3 implementations.

---

## Testing Strategy Overview

### Current Situation
- ✅ 10 test files exist covering various features
- ⚠️ Dependencies not fully installed in current environment (disk space issue)
- ⚠️ Tests have not been executed to validate recent Phase 2-3 implementations

### Who Should Run Tests?

**Recommended Approach**: **Human developer** should run tests in properly configured environment.

**Rationale**:
1. **Environment Setup**: Requires clean Python environment with full dependencies (~2GB+ disk space)
2. **Configuration**: May need actual API keys for LLM testing
3. **Interpretation**: Test failures may require human judgment (e.g., expected behavior vs. bugs)
4. **Iteration**: May need multiple test-fix cycles

**AI Agent Role** (if tests run successfully):
- Analyze test output
- Identify patterns in failures
- Suggest fixes for code issues
- Validate fixes don't break other tests

---

## Test Execution Prerequisites

### 1. Environment Setup
```bash
# Create clean virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify pytest installation
pytest --version
```

### 2. Configuration Setup
```bash
# Copy example config
cp config/config.example.toml config/config.toml

# Edit config/config.toml:
# - Add your LLM API key
# - Configure model settings
# - Adjust max_tokens if needed
```

### 3. Optional: MCP Setup
```bash
# If testing MCP features
cp config/mcp.example.json config/mcp.json
# Configure MCP servers as needed
```

---

## Test Execution Plan

### Phase 1: Smoke Tests (Quick Validation)
**Purpose**: Verify basic imports and core functionality

```bash
# Test 1: Import check
python -c "from app.agent.manus import Manus; from app.flow.planning import PlanningFlow; from app.flow.review import ReviewFlow; from app.agent.reviewer import Reviewer; print('✅ All imports successful')"

# Test 2: Reviewer instantiation
python -c "from app.agent.reviewer import Reviewer; r = Reviewer(); print(f'✅ Reviewer created: {r.name}')"

# Test 3: TestRunner tool check
python -c "from app.tool.test_runner import TestRunner; t = TestRunner(); print(f'✅ TestRunner created: {t.name}')"
```

**Expected Results**: All imports succeed, no errors

**If Failures Occur**: Check for missing dependencies, resolve import errors

---

### Phase 2: Unit Tests (Component Validation)
**Purpose**: Test individual components in isolation

**Available Tests** (10 core tests in repository root):
```bash
# Run specific test files (fastest to slowest)
pytest test_tool_selection.py -v       # Tool selection logic
pytest test_review_flow.py -v          # ReviewFlow iteration mechanism
pytest test_integration.py -v          # Basic agent-flow integration
pytest test_phase2_integration.py -v   # Phase 2 features (verification, cost tracking)
pytest test_prompt_enhancements.py -v  # Phase 3 prompt engineering features
pytest test_integration_fixes.py -v    # Integration bug fixes
pytest test_binary_search_manual.py -v # Reflection mechanism validation
pytest test_real_webscraper.py -v      # Web scraping with browser tools
pytest test_mcp_connection.py -v       # MCP connectivity
pytest test_mcp_stdio.py -v            # MCP stdio mode

# Additional sandbox tests (if needed):
pytest tests/sandbox/ -v  # 4 tests: client, docker terminal, sandbox, manager
```

**Expected Results**:
- test_tool_selection.py: Tests tool selection logic
- test_review_flow.py: Tests ReviewFlow iteration mechanism
- test_integration.py: Basic integration between agents and flows
- test_phase2_integration.py: Phase 2 features (verification loop, cost tracking)
- test_prompt_enhancements.py: Phase 3 prompt engineering features

**Key Metrics to Track**:
- Pass rate (target: 100%)
- Execution time per test
- Any deprecation warnings

---

### Phase 3: Integration Tests (End-to-End)
**Purpose**: Test complete workflows with real LLM calls

```bash
# Run integration tests (may cost API credits)
pytest test_integration_fixes.py -v
pytest test_binary_search_manual.py -v
pytest test_real_webscraper.py -v
```

**⚠️ Cost Warning**: These tests may make actual LLM API calls and incur charges.

**Expected Results**:
- test_integration_fixes.py: Validates bug fixes in integration
- test_binary_search_manual.py: Tests binary search with reflection mechanism
- test_real_webscraper.py: Tests web scraping with browser tools

**Key Validations**:
1. Reflection triggers at step 5 (in high-effort mode)
2. Reviewer provides structured feedback (PASS/FAIL grade)
3. TestRunner executes pytest successfully
4. PlanningFlow tracks step statuses correctly

---

### Phase 4: MCP Tests (Optional)
**Purpose**: Test Model Context Protocol integration

```bash
# Run MCP-specific tests
pytest test_mcp_connection.py -v
pytest test_mcp_stdio.py -v
```

**Expected Results**:
- MCP server connection succeeds
- Tools are discovered dynamically
- Stdio communication works

**Note**: May require MCP server to be running separately.

---

## Test Results Documentation Template

### For Each Test File
```markdown
## Test File: [test_name.py]
**Execution Date**: [YYYY-MM-DD HH:MM]
**Environment**: Python [version], pytest [version]

### Results
- Total Tests: [X]
- Passed: [X]
- Failed: [X]
- Skipped: [X]
- Execution Time: [X.XX seconds]

### Failures (if any)
1. **Test Name**: test_example_function
   - **Error**: [Error message]
   - **Cause**: [Root cause analysis]
   - **Fix Required**: [Yes/No] [Description]

2. [Additional failures...]

### Notable Observations
- [Any warnings, deprecations, or unusual behavior]
```

---

## Critical Tests for Phase 3 Validation

### Priority 1: Core Features
1. **test_review_flow.py** - Validates Doer-Critic iteration (NEW in Phase 3)
2. **test_prompt_enhancements.py** - Validates CoT framework (NEW in Phase 3)
3. **test_binary_search_manual.py** - Validates reflection mechanism (ENHANCED in Phase 3)

### Priority 2: Integration
4. **test_phase2_integration.py** - Validates Phase 2 base (prerequisite for Phase 3)
5. **test_integration_fixes.py** - Validates bug fixes

### Priority 3: Tools & MCP
6. **test_tool_selection.py** - Validates context-aware tool selection
7. **test_mcp_connection.py** - Validates MCP integration

---

## Automated Test Execution Script

Create this script for convenience: `run_tests.sh`

```bash
#!/bin/bash

echo "=== OpenManus Test Suite ==="
echo "Started: $(date)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track results
TOTAL_PASS=0
TOTAL_FAIL=0

# Function to run test and track result
run_test() {
    TEST_FILE=$1
    echo "Running: $TEST_FILE"
    if pytest "$TEST_FILE" -v --tb=short; then
        echo -e "${GREEN}✅ PASSED${NC}: $TEST_FILE"
        ((TOTAL_PASS++))
    else
        echo -e "${RED}❌ FAILED${NC}: $TEST_FILE"
        ((TOTAL_FAIL++))
    fi
    echo ""
}

# Phase 1: Smoke tests
echo "=== Phase 1: Smoke Tests ==="
python -c "from app.agent.manus import Manus; print('✅ Manus import OK')" || echo "❌ Manus import failed"
python -c "from app.flow.review import ReviewFlow; print('✅ ReviewFlow import OK')" || echo "❌ ReviewFlow import failed"
python -c "from app.agent.reviewer import Reviewer; print('✅ Reviewer import OK')" || echo "❌ Reviewer import failed"
echo ""

# Phase 2: Unit tests (priority order)
echo "=== Phase 2: Unit Tests ==="
run_test "test_tool_selection.py"
run_test "test_review_flow.py"
run_test "test_integration.py"

# Phase 3: Integration tests (if Phase 2 passed)
if [ $TOTAL_FAIL -eq 0 ]; then
    echo "=== Phase 3: Integration Tests ==="
    run_test "test_phase2_integration.py"
    run_test "test_prompt_enhancements.py"
    run_test "test_binary_search_manual.py"
else
    echo "⚠️ Skipping integration tests due to unit test failures"
fi

# Summary
echo "=== Test Summary ==="
echo "Completed: $(date)"
echo "Passed: $TOTAL_PASS"
echo "Failed: $TOTAL_FAIL"

if [ $TOTAL_FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
```

**Make executable**:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## Handling Test Failures

### Common Issues & Solutions

#### 1. Import Errors (ModuleNotFoundError)
**Symptom**: `ModuleNotFoundError: No module named 'pydantic'`  
**Cause**: Dependencies not installed  
**Solution**: `pip install -r requirements.txt`

#### 2. Configuration Errors
**Symptom**: `FileNotFoundError: config/config.toml`  
**Cause**: Config file not created  
**Solution**: `cp config/config.example.toml config/config.toml`

#### 3. API Key Errors
**Symptom**: `AuthenticationError` or `InvalidAPIKey`  
**Cause**: Invalid/missing API key in config  
**Solution**: Add valid API key to config/config.toml

#### 4. Timeout Errors
**Symptom**: `TimeoutError` in LLM calls  
**Cause**: Network issues or model overload  
**Solution**: Increase timeout in config, retry, or use different model

#### 5. Test Runner Errors
**Symptom**: TestRunner tool fails to find pytest  
**Cause**: pytest not in system path  
**Solution**: Ensure pytest installed: `pip install pytest`

---

## Test Coverage Gaps (Future Work)

### Current Test Coverage (14 tests total)

**What IS Covered**:
- ✅ **Phase 2-3 Core Features**: PlanningFlow, ReviewFlow, Reviewer agent, TestRunner tool
- ✅ **Integration Points**: Agent-flow coordination, tool selection
- ✅ **Prompt Engineering**: CoT framework, reflection mechanism
- ✅ **MCP Integration**: Connection, stdio mode
- ✅ **Sandbox**: Client, docker terminal, sandbox manager
- ✅ **Real-World Scenarios**: Binary search, web scraping

**What Is NOT Covered** (gaps):
- ❌ **Individual Tool Coverage**: No unit tests for each tool in app/tool/ (file operators, browser, search, etc.)
- ❌ **All Agent Types**: No dedicated tests for data_analysis, swe, sandbox_agent
- ❌ **LLM Edge Cases**: Token limits, rate limiting, error recovery
- ❌ **Configuration Variants**: Different LLM providers (Azure, Bedrock, Ollama)
- ❌ **Flow Factory**: Limited testing of dynamic flow creation
- ❌ **Cost Tracking**: No validation of budget monitoring accuracy

**Coverage Estimate**: Tests cover ~40-50% of codebase, focusing on **critical paths** (planning, review, agent coordination) rather than comprehensive unit coverage.

**Recommendation**: Current tests validate Phase 2-3 implementations. For production, add unit tests for individual tools and agents.

### Missing Test Areas
1. **Vision Capabilities** - No tests yet (tasks not implemented)
2. **MCP Multi-Server** - Tests for multiple simultaneous MCP servers
3. **High-Effort Mode** - Comprehensive test of reflection every 5 steps
4. **Cost Tracking** - Validation of $20 budget monitoring
5. **Error Recovery** - Tests for retry mechanisms

### Recommended New Tests (After Vision Implementation)
1. `test_vision_capabilities.py` - Test image analysis tasks
2. `test_llm_vision_config.py` - Test vision model configuration
3. `test_vision_with_reviewer.py` - Test Reviewer analyzing vision outputs

---

## Continuous Integration Recommendations

### GitHub Actions Workflow (Future)
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run smoke tests
        run: python -c "from app.agent.manus import Manus"
      - name: Run unit tests
        run: pytest test_tool_selection.py test_review_flow.py -v
      # Skip integration tests in CI (API costs)
```

---

## Test Execution Timeline

### Immediate (Before proceeding to vision tasks)
1. ✅ Create summary documents (this document + OPUS_REVIEW_SUMMARY.md)
2. ⏳ **HUMAN**: Set up clean environment with dependencies
3. ⏳ **HUMAN**: Run smoke tests (5 minutes)
4. ⏳ **HUMAN**: Run unit tests (10-15 minutes)
5. ⏳ **HUMAN**: Document results
6. ⏳ **AI/HUMAN**: Analyze failures and create fix plan if needed

### After Test Results Available
7. ⏳ **AI**: Review test results and identify issues
8. ⏳ **AI**: Propose fixes for any failures
9. ⏳ **HUMAN**: Approve and apply fixes
10. ⏳ **HUMAN**: Re-run tests to validate fixes
11. ✅ **PROCEED** to vision tasks if tests pass

---

## Decision Matrix: Proceed or Fix?

### PROCEED to Vision Tasks if:
- ✅ Smoke tests pass (imports work)
- ✅ Core unit tests pass (test_review_flow.py, test_tool_selection.py)
- ✅ No critical failures in integration tests
- ⚠️ Minor issues documented but don't block vision work

### FIX FIRST if:
- ❌ Smoke tests fail (core imports broken)
- ❌ ReviewFlow tests fail (NEW feature not working)
- ❌ Multiple integration test failures (architecture issues)
- ❌ Critical bugs discovered that would affect vision implementation

### PARALLEL APPROACH if:
- ⚠️ Some tests fail but unrelated to vision capabilities
- ⚠️ Vision work is independent of failing tests
- ✅ Can create fixes while implementing vision tasks

---

## Conclusion

**Recommendation**: Human developer should execute tests in proper environment, then share results with Claude Opus 4.5 for analysis and decision-making.

**Alternative**: If environment setup is not feasible, Claude Opus 4.5 can review code statically (using OPUS_REVIEW_SUMMARY.md) and provide architectural feedback without test execution results.

**Next Step**: Determine who will execute tests and in what timeframe.
