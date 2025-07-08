#!/bin/bash

echo "Frontend Test Suite - Fixed Version"
echo "==================================="
echo ""

# Set environment
export NODE_ENV=test

echo "1. Running API service tests..."
npx vitest run src/services/api.test.ts --reporter=verbose || echo "API tests failed"

echo ""
echo "2. Running Store tests..."
npx vitest run src/store/authStore.test.ts --reporter=verbose || echo "Store tests failed"

echo ""
echo "3. Running Component tests..."
npx vitest run src/components/**/*.test.* --reporter=verbose || echo "Component tests failed"

echo ""
echo "4. Running Page tests..."
npx vitest run src/pages/**/*.test.* --reporter=verbose || echo "Page tests failed"

echo ""
echo "5. Running simple test..."
npx vitest run src/test-simple.test.tsx --reporter=verbose || echo "Simple test failed"

echo ""
echo "Test run complete!"
echo ""
echo "Note: If tests are hanging, try the following:"
echo "1. Run tests individually: npx vitest run [test-file]"
echo "2. Use --pool=forks flag: npx vitest run --pool=forks"
echo "3. Clear node_modules and reinstall: rm -rf node_modules && npm install"
echo "4. Run in a native Linux environment instead of WSL2"