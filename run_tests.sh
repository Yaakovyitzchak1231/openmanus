#!/bin/bash

echo "=== OpenManus Test Suite ==="
echo "Started: $(date)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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
python -c "from app.agent.manus import Manus; print('✅ Manus import OK')" || { echo "❌ Manus import failed"; ((TOTAL_FAIL++)); }
python -c "from app.flow.review import ReviewFlow; print('✅ ReviewFlow import OK')" || { echo "❌ ReviewFlow import failed"; ((TOTAL_FAIL++)); }
python -c "from app.agent.reviewer import Reviewer; print('✅ Reviewer import OK')" || { echo "❌ Reviewer import failed"; ((TOTAL_FAIL++)); }
python -c "from app.tool.test_runner import TestRunner; print('✅ TestRunner import OK')" || { echo "❌ TestRunner import failed"; ((TOTAL_FAIL++)); }
python -c "from app.flow.planning import PlanningFlow; print('✅ PlanningFlow import OK')" || { echo "❌ PlanningFlow import failed"; ((TOTAL_FAIL++)); }
echo ""

# Check if smoke tests passed
if [ $TOTAL_FAIL -gt 0 ]; then
    echo -e "${RED}⚠️ Smoke tests failed. Please fix import errors before running test suite.${NC}"
    echo "Common causes:"
    echo "  1. Missing dependencies: pip install -r requirements.txt"
    echo "  2. Wrong Python version: Requires Python 3.10+"
    echo "  3. Import path issues: Run from project root directory"
    exit 1
fi

echo -e "${GREEN}✅ All smoke tests passed! Proceeding to unit tests...${NC}"
echo ""

# Phase 2: Unit tests (priority order)
echo "=== Phase 2: Unit Tests ==="
run_test "test_tool_selection.py"
run_test "test_review_flow.py"
run_test "test_integration.py"

# Phase 3: Integration tests (if Phase 2 passed)
if [ $TOTAL_FAIL -eq 0 ]; then
    echo "=== Phase 3: Integration Tests ==="
    echo -e "${YELLOW}⚠️ Note: Integration tests may make LLM API calls and incur costs${NC}"
    run_test "test_phase2_integration.py"
    run_test "test_prompt_enhancements.py"
    run_test "test_binary_search_manual.py"
else
    echo -e "${YELLOW}⚠️ Skipping integration tests due to unit test failures${NC}"
fi

# Phase 4: Optional MCP tests
echo ""
echo "=== Phase 4: MCP Tests (Optional) ==="
echo "To run MCP tests, execute manually:"
echo "  pytest test_mcp_connection.py -v"
echo "  pytest test_mcp_stdio.py -v"
echo ""

# Summary
echo "=== Test Summary ==="
echo "Completed: $(date)"
echo "Passed: $TOTAL_PASS"
echo "Failed: $TOTAL_FAIL"
echo ""

if [ $TOTAL_FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review OPUS_REVIEW_SUMMARY.md for detailed code analysis"
    echo "  2. Proceed to vision capabilities implementation (Phase 3 final tasks)"
    echo "  3. Consider running optional MCP tests if using MCP features"
    exit 0
else
    echo -e "${RED}❌ $TOTAL_FAIL test(s) failed${NC}"
    echo ""
    echo "Recommended actions:"
    echo "  1. Review test output above for error details"
    echo "  2. Check TESTING_PLAN.md for common issues and solutions"
    echo "  3. Fix failing tests before proceeding to new features"
    echo "  4. Re-run this script after fixes: ./run_tests.sh"
    exit 1
fi
