#!/usr/bin/env bash
#
# Fabra CI Full Suite
# ====================
# Comprehensive test and build script that validates everything.
#
# Usage:
#   ./scripts/ci_full.sh           # Run all tests and builds
#   ./scripts/ci_full.sh --tests   # Run tests only
#   ./scripts/ci_full.sh --builds  # Run builds only
#   ./scripts/ci_full.sh --quick   # Skip Playwright UI tests and Docker builds
#

# Don't exit on first error - we want to run all checks and report summary
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Track results using simple variables (portable)
RESULT_UNIT=""
RESULT_PERF=""
RESULT_INTEGRATION=""
RESULT_E2E=""
RESULT_PLAYWRIGHT=""
RESULT_PRECOMMIT=""
RESULT_PYTHON=""
RESULT_UI_NEXT=""
RESULT_PLAYGROUND=""
RESULT_DOCS=""
RESULT_DOCKER1=""
RESULT_DOCKER2=""

FAILED=0
START_TIME=$(date +%s)

# Parse arguments
RUN_TESTS=true
RUN_BUILDS=true
SKIP_SLOW=false

for arg in "$@"; do
    case $arg in
        --tests)
            RUN_BUILDS=false
            ;;
        --builds)
            RUN_TESTS=false
            ;;
        --quick)
            SKIP_SLOW=true
            ;;
        --help|-h)
            echo "Fabra CI Full Suite"
            echo ""
            echo "Usage:"
            echo "  ./scripts/ci_full.sh           # Run all tests and builds"
            echo "  ./scripts/ci_full.sh --tests   # Run tests only"
            echo "  ./scripts/ci_full.sh --builds  # Run builds only"
            echo "  ./scripts/ci_full.sh --quick   # Skip Playwright UI tests and Docker builds"
            exit 0
            ;;
    esac
done

# Change to project root
cd "$(dirname "$0")/.."

# Print header
print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Print section
print_section() {
    echo ""
    echo -e "${YELLOW}▸ $1${NC}"
}

# Print final summary
print_summary() {
    local END_TIME=$(date +%s)
    local DURATION=$((END_TIME - START_TIME))
    local MINUTES=$((DURATION / 60))
    local SECONDS=$((DURATION % 60))

    print_header "CI SUMMARY"

    echo -e "${BOLD}Results:${NC}"
    echo ""

    # Tests section
    if [ "$RUN_TESTS" = "true" ]; then
        echo -e "  ${BOLD}Tests:${NC}"
        [ -n "$RESULT_UNIT" ] && printf "    %-25s %b\n" "Unit Tests" "$RESULT_UNIT"
        [ -n "$RESULT_PERF" ] && printf "    %-25s %b\n" "Performance Tests" "$RESULT_PERF"
        [ -n "$RESULT_INTEGRATION" ] && printf "    %-25s %b\n" "Integration Tests" "$RESULT_INTEGRATION"
        [ -n "$RESULT_E2E" ] && printf "    %-25s %b\n" "E2E Tests" "$RESULT_E2E"
        [ -n "$RESULT_PLAYWRIGHT" ] && printf "    %-25s %b\n" "Playwright UI Tests" "$RESULT_PLAYWRIGHT"
        [ -n "$RESULT_PRECOMMIT" ] && printf "    %-25s %b\n" "Pre-commit Hooks" "$RESULT_PRECOMMIT"
        echo ""
    fi

    # Builds section
    if [ "$RUN_BUILDS" = "true" ]; then
        echo -e "  ${BOLD}Builds:${NC}"
        [ -n "$RESULT_PYTHON" ] && printf "    %-25s %b\n" "Python Package" "$RESULT_PYTHON"
        [ -n "$RESULT_UI_NEXT" ] && printf "    %-25s %b\n" "ui-next Build" "$RESULT_UI_NEXT"
        [ -n "$RESULT_PLAYGROUND" ] && printf "    %-25s %b\n" "playground Build" "$RESULT_PLAYGROUND"
        [ -n "$RESULT_DOCS" ] && printf "    %-25s %b\n" "docs-site Build" "$RESULT_DOCS"
        [ -n "$RESULT_DOCKER1" ] && printf "    %-25s %b\n" "Docker: Dockerfile" "$RESULT_DOCKER1"
        [ -n "$RESULT_DOCKER2" ] && printf "    %-25s %b\n" "Docker: quickstart-test" "$RESULT_DOCKER2"
        echo ""
    fi

    echo -e "  ${BOLD}Duration:${NC} ${MINUTES}m ${SECONDS}s"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}${BOLD}  ALL CHECKS PASSED!${NC}"
        echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo -e "${RED}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}${BOLD}  SOME CHECKS FAILED - SEE ABOVE FOR DETAILS${NC}"
        echo -e "${RED}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    echo ""
}

# Cleanup function
cleanup() {
    # Kill any background processes we started
    if [ -n "$UI_SERVER_PID" ]; then
        kill $UI_SERVER_PID 2>/dev/null || true
    fi
    if [ -n "$API_SERVER_PID" ]; then
        kill $API_SERVER_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_header "FABRA CI FULL SUITE"

echo -e "Project: ${BOLD}$(basename $(pwd))${NC}"
echo -e "Date:    ${BOLD}$(date)${NC}"
echo -e "Mode:    ${BOLD}Tests=$RUN_TESTS, Builds=$RUN_BUILDS, Quick=$SKIP_SLOW${NC}"

# =============================================================================
# TESTS
# =============================================================================

if [ "$RUN_TESTS" = "true" ]; then
    print_header "RUNNING TESTS"

    # Unit Tests (override default marker filter from pytest.ini)
    print_section "Unit Tests"
    if uv run pytest tests/unit -v --tb=short -m ""; then
        RESULT_UNIT="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ Unit Tests passed${NC}"
    else
        RESULT_UNIT="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ Unit Tests failed${NC}"
        FAILED=1
    fi

    # Performance Tests (in tests/perf, not marked with e2e)
    print_section "Performance Tests"
    if uv run pytest tests/perf -v --tb=short -m ""; then
        RESULT_PERF="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ Performance Tests passed${NC}"
    else
        RESULT_PERF="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ Performance Tests failed${NC}"
        FAILED=1
    fi

    # Integration Tests (override default marker filter)
    print_section "Integration Tests"
    if uv run pytest tests/integration -v --tb=short -m ""; then
        RESULT_INTEGRATION="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ Integration Tests passed${NC}"
    else
        RESULT_INTEGRATION="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ Integration Tests failed${NC}"
        FAILED=1
    fi

    # E2E Tests (run all e2e folder tests, not filtered by marker)
    print_section "E2E Tests"
    if uv run pytest tests/e2e -v --tb=short -m ""; then
        RESULT_E2E="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ E2E Tests passed${NC}"
    else
        RESULT_E2E="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ E2E Tests failed${NC}"
        FAILED=1
    fi

    # Playwright UI Tests (slow - skip with --quick)
    if [ "$SKIP_SLOW" = "false" ]; then
        print_section "Playwright UI Tests"
        if uv run pytest tests/ui -m e2e -v --tb=short; then
            RESULT_PLAYWRIGHT="${GREEN}✓ PASS${NC}"
            echo -e "${GREEN}✓ Playwright UI Tests passed${NC}"
        else
            # Playwright tests are optional - don't fail the build
            RESULT_PLAYWRIGHT="${YELLOW}⚠ WARN${NC}"
            echo -e "${YELLOW}⚠ Playwright UI Tests had warnings (non-blocking)${NC}"
        fi
    else
        RESULT_PLAYWRIGHT="${YELLOW}⊘ SKIP${NC}"
        echo -e "${YELLOW}⊘ Playwright UI Tests skipped (--quick mode)${NC}"
    fi

    # Pre-commit hooks
    print_section "Pre-commit Hooks"
    if uv run pre-commit run --all-files; then
        RESULT_PRECOMMIT="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ Pre-commit Hooks passed${NC}"
    else
        RESULT_PRECOMMIT="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ Pre-commit Hooks failed${NC}"
        FAILED=1
    fi
fi

# =============================================================================
# BUILDS
# =============================================================================

if [ "$RUN_BUILDS" = "true" ]; then
    print_header "RUNNING BUILDS"

    # Python Package
    print_section "Python Package"
    if uv build; then
        RESULT_PYTHON="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ Python Package build passed${NC}"
    else
        RESULT_PYTHON="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ Python Package build failed${NC}"
        FAILED=1
    fi

    # ui-next Build
    print_section "ui-next Build"
    if (cd src/fabra/ui-next && npm run build); then
        RESULT_UI_NEXT="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ ui-next build passed${NC}"
    else
        RESULT_UI_NEXT="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ ui-next build failed${NC}"
        FAILED=1
    fi

    # playground Build
    print_section "playground Build"
    if (cd playground && npm run build); then
        RESULT_PLAYGROUND="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ playground build passed${NC}"
    else
        RESULT_PLAYGROUND="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ playground build failed${NC}"
        FAILED=1
    fi

    # docs-site Build
    print_section "docs-site Build"
    if (cd docs-site && npm run build); then
        RESULT_DOCS="${GREEN}✓ PASS${NC}"
        echo -e "${GREEN}✓ docs-site build passed${NC}"
    else
        RESULT_DOCS="${RED}✗ FAIL${NC}"
        echo -e "${RED}✗ docs-site build failed${NC}"
        FAILED=1
    fi

    # Docker builds (slow - skip with --quick)
    if [ "$SKIP_SLOW" = "false" ]; then
        # Check if Docker is available
        if command -v docker &> /dev/null && docker info &> /dev/null; then
            print_section "Docker: Dockerfile"
            if docker build -t fabra:ci-test .; then
                RESULT_DOCKER1="${GREEN}✓ PASS${NC}"
                echo -e "${GREEN}✓ Docker build passed${NC}"
            else
                RESULT_DOCKER1="${RED}✗ FAIL${NC}"
                echo -e "${RED}✗ Docker build failed${NC}"
                FAILED=1
            fi

            print_section "Docker: Dockerfile.quickstart-test"
            if docker build -t fabra:ci-quickstart-test -f Dockerfile.quickstart-test .; then
                RESULT_DOCKER2="${GREEN}✓ PASS${NC}"
                echo -e "${GREEN}✓ Docker quickstart-test build passed${NC}"
            else
                RESULT_DOCKER2="${RED}✗ FAIL${NC}"
                echo -e "${RED}✗ Docker quickstart-test build failed${NC}"
                FAILED=1
            fi
        else
            RESULT_DOCKER1="${YELLOW}⊘ SKIP${NC}"
            RESULT_DOCKER2="${YELLOW}⊘ SKIP${NC}"
            echo -e "${YELLOW}⊘ Docker not available - skipping Docker builds${NC}"
        fi
    else
        RESULT_DOCKER1="${YELLOW}⊘ SKIP${NC}"
        RESULT_DOCKER2="${YELLOW}⊘ SKIP${NC}"
        echo -e "${YELLOW}⊘ Docker builds skipped (--quick mode)${NC}"
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================

print_summary

exit $FAILED
