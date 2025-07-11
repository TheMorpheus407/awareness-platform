#!/usr/bin/env node

/**
 * Comprehensive test runner for the Awareness Platform frontend.
 * Provides various test execution modes and reporting options.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  unit: args.includes('--unit'),
  integration: args.includes('--integration'),
  e2e: args.includes('--e2e'),
  coverage: args.includes('--coverage'),
  watch: args.includes('--watch'),
  ui: args.includes('--ui'),
  updateSnapshots: args.includes('--update-snapshots'),
  headed: args.includes('--headed'),
  debug: args.includes('--debug'),
  ci: args.includes('--ci') || process.env.CI === 'true',
};

// If no specific test type is selected, run unit tests
if (!options.unit && !options.integration && !options.e2e) {
  options.unit = true;
}

/**
 * Run a command and return a promise
 */
function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    console.log(`Running: ${command} ${args.join(' ')}`);
    
    const child = spawn(command, args, {
      stdio: 'inherit',
      shell: true,
      ...options,
    });

    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Command failed with exit code ${code}`));
      } else {
        resolve();
      }
    });

    child.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Run unit tests
 */
async function runUnitTests() {
  console.log('\n🧪 Running Unit Tests...\n');
  
  const vitestArgs = [];
  
  if (!options.watch) {
    vitestArgs.push('--run');
  }
  
  if (options.coverage) {
    vitestArgs.push('--coverage');
  }
  
  if (options.ui) {
    vitestArgs.push('--ui');
  }
  
  if (options.ci) {
    vitestArgs.push('--reporter=verbose');
    vitestArgs.push('--pool=forks');
  }
  
  // Add test file pattern
  vitestArgs.push('src/**/*.{test,spec}.{ts,tsx}');
  
  await runCommand('npx', ['vitest', ...vitestArgs]);
}

/**
 * Run integration tests
 */
async function runIntegrationTests() {
  console.log('\n🔗 Running Integration Tests...\n');
  
  const vitestArgs = ['--run'];
  
  if (options.coverage) {
    vitestArgs.push('--coverage');
  }
  
  // Add integration test pattern
  vitestArgs.push('src/**/*.integration.test.{ts,tsx}');
  
  await runCommand('npx', ['vitest', ...vitestArgs]);
}

/**
 * Run E2E tests
 */
async function runE2ETests() {
  console.log('\n🌐 Running E2E Tests...\n');
  
  const playwrightArgs = ['test'];
  
  if (options.headed) {
    playwrightArgs.push('--headed');
  }
  
  if (options.debug) {
    playwrightArgs.push('--debug');
  }
  
  if (options.ui) {
    playwrightArgs.push('--ui');
  }
  
  if (options.updateSnapshots) {
    playwrightArgs.push('--update-snapshots');
  }
  
  await runCommand('npx', ['playwright', ...playwrightArgs]);
}

/**
 * Run linting
 */
async function runLinting() {
  console.log('\n🔍 Running Linting...\n');
  await runCommand('npm', ['run', 'lint']);
}

/**
 * Run type checking
 */
async function runTypeCheck() {
  console.log('\n📝 Running Type Check...\n');
  await runCommand('npm', ['run', 'type-check']);
}

/**
 * Generate coverage report
 */
async function generateCoverageReport() {
  console.log('\n📊 Generating Coverage Report...\n');
  
  const coveragePath = path.join(__dirname, 'coverage');
  
  if (fs.existsSync(coveragePath)) {
    const summaryPath = path.join(coveragePath, 'coverage-summary.json');
    
    if (fs.existsSync(summaryPath)) {
      const summary = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
      const total = summary.total;
      
      console.log('\nCoverage Summary:');
      console.log(`  Statements: ${total.statements.pct}%`);
      console.log(`  Branches: ${total.branches.pct}%`);
      console.log(`  Functions: ${total.functions.pct}%`);
      console.log(`  Lines: ${total.lines.pct}%`);
      
      // Check thresholds
      const thresholds = {
        statements: 60,
        branches: 60,
        functions: 60,
        lines: 60,
      };
      
      let failed = false;
      for (const [metric, threshold] of Object.entries(thresholds)) {
        if (total[metric].pct < threshold) {
          console.error(`\n❌ ${metric} coverage (${total[metric].pct}%) is below threshold (${threshold}%)`);
          failed = true;
        }
      }
      
      if (failed && !options.ci) {
        console.log('\n💡 Tip: Run with --coverage to see detailed coverage report');
      }
      
      return !failed;
    }
  }
  
  return true;
}

/**
 * Main execution
 */
async function main() {
  try {
    console.log('🚀 Awareness Platform Frontend Test Runner\n');
    
    // Always run linting and type checking first in CI
    if (options.ci) {
      await runLinting();
      await runTypeCheck();
    }
    
    // Run selected test types
    if (options.unit) {
      await runUnitTests();
    }
    
    if (options.integration) {
      await runIntegrationTests();
    }
    
    if (options.e2e) {
      await runE2ETests();
    }
    
    // Generate coverage report if coverage was enabled
    if (options.coverage) {
      const coveragePassed = await generateCoverageReport();
      if (!coveragePassed && options.ci) {
        process.exit(1);
      }
    }
    
    console.log('\n✅ All tests completed successfully!\n');
  } catch (error) {
    console.error('\n❌ Test execution failed:', error.message);
    process.exit(1);
  }
}

// Show help if requested
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Frontend Test Runner

Usage: node run-tests.js [options]

Options:
  --unit              Run unit tests (default if no test type specified)
  --integration       Run integration tests
  --e2e               Run E2E tests
  --coverage          Generate coverage report
  --watch             Run tests in watch mode
  --ui                Open test UI
  --update-snapshots  Update E2E snapshots
  --headed            Run E2E tests in headed mode
  --debug             Run E2E tests in debug mode
  --ci                Run in CI mode (verbose output, strict checks)
  --help, -h          Show this help message

Examples:
  node run-tests.js                     # Run unit tests
  node run-tests.js --coverage          # Run unit tests with coverage
  node run-tests.js --e2e --headed      # Run E2E tests in headed mode
  node run-tests.js --unit --watch      # Run unit tests in watch mode
  `);
  process.exit(0);
}

// Run main function
main();