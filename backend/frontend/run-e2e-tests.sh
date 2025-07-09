#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting E2E Test Setup...${NC}"

# Check if backend is running
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${RED}Backend is not running!${NC}"
    echo "Please start the backend first:"
    echo "  cd ../backend && python -m uvicorn main:app --reload"
    exit 1
fi

# Check if frontend is running
if ! curl -s http://localhost:5173 > /dev/null; then
    echo -e "${YELLOW}Frontend is not running. Starting...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    echo "Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null; then
            echo -e "${GREEN}Frontend started!${NC}"
            break
        fi
        sleep 1
    done
    
    if ! curl -s http://localhost:5173 > /dev/null; then
        echo -e "${RED}Failed to start frontend!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Frontend is already running!${NC}"
fi

# Seed E2E test data
echo -e "${YELLOW}Seeding E2E test data...${NC}"
cd ../backend
python scripts/seed_e2e_data.py
cd ../frontend

# Run E2E tests
echo -e "${YELLOW}Running E2E tests...${NC}"
npx playwright test "$@"
TEST_EXIT_CODE=$?

# Kill frontend if we started it
if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}Stopping frontend...${NC}"
    kill $FRONTEND_PID 2>/dev/null
fi

# Show test report if tests failed
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Tests failed!${NC}"
    echo -e "${YELLOW}Opening test report...${NC}"
    npx playwright show-report
else
    echo -e "${GREEN}All tests passed!${NC}"
fi

exit $TEST_EXIT_CODE