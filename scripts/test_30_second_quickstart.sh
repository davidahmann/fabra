#!/bin/bash
# Fabra 30-Second Quickstart Validation Script
#
# Run this on a fresh machine/container to validate the quickstart experience.
# This script tests both Feature Store and Context Store demos.
#
# Usage:
#   ./scripts/test_30_second_quickstart.sh           # Run all tests
#   ./scripts/test_30_second_quickstart.sh features  # Only test Feature Store
#   ./scripts/test_30_second_quickstart.sh context   # Only test Context Store
#
# Requirements:
#   - Python 3.10+
#   - pip or uv

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PORT=8765  # Use non-standard port to avoid conflicts
TIMEOUT=30
MODE=${1:-all}  # all, features, or context

echo -e "${BLUE}=== Fabra 30-Second Quickstart Validation ===${NC}"
echo -e "Mode: ${MODE}"
echo -e "Port: ${PORT}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    # Kill any remaining fabra processes on our port
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
}

trap cleanup EXIT

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "examples" ]; then
    echo -e "${RED}ERROR: Run this script from the project root directory${NC}"
    exit 1
fi

# Track total time
TOTAL_START=$(date +%s)

# Function to test Feature Store demo
test_features() {
    echo -e "\n${BLUE}--- Testing Feature Store Demo ---${NC}"
    local START=$(date +%s)

    # Start server in background
    echo -e "${YELLOW}Starting server with demo_features.py...${NC}"
    uv run fabra serve examples/demo_features.py --port $PORT &
    SERVER_PID=$!

    # Wait for server to be ready (poll health endpoint)
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    for i in {1..20}; do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}Server is ready!${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo -e "${RED}ERROR: Server failed to start within 10 seconds${NC}"
            return 1
        fi
        sleep 0.5
    done

    # Test feature endpoint
    echo -e "${YELLOW}Testing feature endpoint...${NC}"
    RESPONSE=$(curl -s "http://localhost:$PORT/features/user_engagement?entity_id=user_123")
    echo -e "Response: ${RESPONSE}"

    # Validate response has value
    if echo "$RESPONSE" | grep -q '"value"'; then
        echo -e "${GREEN}SUCCESS: Got feature value${NC}"
    else
        echo -e "${RED}FAILURE: No feature value returned${NC}"
        return 1
    fi

    # Validate response has freshness_ms
    if echo "$RESPONSE" | grep -q '"freshness_ms"'; then
        echo -e "${GREEN}SUCCESS: Got freshness_ms${NC}"
    else
        echo -e "${YELLOW}WARNING: No freshness_ms in response${NC}"
    fi

    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    unset SERVER_PID

    local END=$(date +%s)
    local DURATION=$((END - START))
    echo -e "${GREEN}Feature Store test completed in ${DURATION} seconds${NC}"

    if [ $DURATION -gt $TIMEOUT ]; then
        echo -e "${YELLOW}WARNING: Test took longer than ${TIMEOUT} seconds${NC}"
    fi

    return 0
}

# Function to test Context Store demo
test_context() {
    echo -e "\n${BLUE}--- Testing Context Store Demo ---${NC}"
    local START=$(date +%s)

    # Start server in background
    echo -e "${YELLOW}Starting server with demo_context.py...${NC}"
    uv run fabra serve examples/demo_context.py --port $PORT &
    SERVER_PID=$!

    # Wait for server to be ready
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    for i in {1..20}; do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}Server is ready!${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo -e "${RED}ERROR: Server failed to start within 10 seconds${NC}"
            return 1
        fi
        sleep 0.5
    done

    # Test context endpoint
    echo -e "${YELLOW}Testing context endpoint...${NC}"
    RESPONSE=$(curl -s -X POST "http://localhost:$PORT/v1/context/chat_context" \
        -H "Content-Type: application/json" \
        -d '{"user_id":"user_123","query":"how do features work?"}')

    echo -e "Response (truncated): ${RESPONSE:0:200}..."

    # Validate response has id (context_id)
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo -e "${GREEN}SUCCESS: Got context ID${NC}"
    else
        echo -e "${RED}FAILURE: No context ID returned${NC}"
        return 1
    fi

    # Validate response has content
    if echo "$RESPONSE" | grep -q '"content"'; then
        echo -e "${GREEN}SUCCESS: Got context content${NC}"
    else
        echo -e "${RED}FAILURE: No content returned${NC}"
        return 1
    fi

    # Validate response has meta with freshness_status
    if echo "$RESPONSE" | grep -q '"freshness_status"'; then
        echo -e "${GREEN}SUCCESS: Got freshness_status${NC}"
    else
        echo -e "${YELLOW}WARNING: No freshness_status in response${NC}"
    fi

    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    unset SERVER_PID

    local END=$(date +%s)
    local DURATION=$((END - START))
    echo -e "${GREEN}Context Store test completed in ${DURATION} seconds${NC}"

    if [ $DURATION -gt $TIMEOUT ]; then
        echo -e "${YELLOW}WARNING: Test took longer than ${TIMEOUT} seconds${NC}"
    fi

    return 0
}

# Run tests based on mode
FAILURES=0

if [ "$MODE" = "all" ] || [ "$MODE" = "features" ]; then
    if ! test_features; then
        ((FAILURES++))
    fi
fi

if [ "$MODE" = "all" ] || [ "$MODE" = "context" ]; then
    if ! test_context; then
        ((FAILURES++))
    fi
fi

# Final summary
TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "Total time: ${TOTAL_DURATION} seconds"
echo -e "Target: < ${TIMEOUT} seconds"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    if [ $TOTAL_DURATION -le $TIMEOUT ]; then
        echo -e "${GREEN}30-second quickstart validated successfully!${NC}"
    else
        echo -e "${YELLOW}Tests passed but took longer than ${TIMEOUT} seconds${NC}"
    fi
    exit 0
else
    echo -e "${RED}${FAILURES} test(s) failed${NC}"
    exit 1
fi
