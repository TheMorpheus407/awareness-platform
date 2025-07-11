#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read test results
function readResults(filename) {
  try {
    const data = fs.readFileSync(filename, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Error reading ${filename}:`, error.message);
    return null;
  }
}

// Analyze performance metrics
function analyzePerformance(loadResults, stressResults) {
  const analysis = {
    timestamp: new Date().toISOString(),
    summary: {
      status: 'PASS',
      issues: [],
      recommendations: [],
    },
    load_test: {
      duration: loadResults?.metrics?.iteration_duration?.avg || 0,
      requests: loadResults?.metrics?.http_reqs?.count || 0,
      errors: loadResults?.metrics?.errors?.rate || 0,
      p95_latency: loadResults?.metrics?.http_req_duration?.values?.['p(95)'] || 0,
      p99_latency: loadResults?.metrics?.http_req_duration?.values?.['p(99)'] || 0,
    },
    stress_test: {
      max_users: stressResults?.metrics?.vus?.max || 0,
      breaking_point: null,
      peak_error_rate: stressResults?.metrics?.errors?.rate || 0,
      peak_latency: stressResults?.metrics?.http_req_duration?.values?.['p(99)'] || 0,
    },
    resource_usage: {
      cpu: {
        average: stressResults?.metrics?.cpu_usage?.avg || 0,
        peak: stressResults?.metrics?.cpu_usage?.max || 0,
      },
      memory: {
        average: stressResults?.metrics?.memory_usage?.avg || 0,
        peak: stressResults?.metrics?.memory_usage?.max || 0,
      },
    },
  };

  // Determine breaking point
  if (stressResults?.metrics?.errors?.rate > 0.1) {
    analysis.stress_test.breaking_point = Math.floor(
      stressResults.metrics.vus.max * (1 - stressResults.metrics.errors.rate)
    );
  }

  // Check performance criteria
  if (analysis.load_test.p95_latency > 500) {
    analysis.summary.status = 'WARNING';
    analysis.summary.issues.push(
      `P95 latency (${analysis.load_test.p95_latency}ms) exceeds 500ms threshold`
    );
    analysis.summary.recommendations.push(
      'Consider optimizing database queries and implementing caching'
    );
  }

  if (analysis.load_test.errors > 0.01) {
    analysis.summary.status = 'FAIL';
    analysis.summary.issues.push(
      `Error rate (${(analysis.load_test.errors * 100).toFixed(2)}%) exceeds 1% threshold`
    );
    analysis.summary.recommendations.push(
      'Investigate error logs and improve error handling'
    );
  }

  if (analysis.resource_usage.cpu.peak > 80) {
    analysis.summary.status = 'WARNING';
    analysis.summary.issues.push(
      `Peak CPU usage (${analysis.resource_usage.cpu.peak}%) is high`
    );
    analysis.summary.recommendations.push(
      'Consider horizontal scaling or CPU optimization'
    );
  }

  if (analysis.resource_usage.memory.peak > 85) {
    analysis.summary.status = 'WARNING';
    analysis.summary.issues.push(
      `Peak memory usage (${analysis.resource_usage.memory.peak}%) is high`
    );
    analysis.summary.recommendations.push(
      'Review memory usage patterns and potential memory leaks'
    );
  }

  return analysis;
}

// Generate HTML report
function generateHTMLReport(analysis) {
  const statusColor = {
    PASS: '#28a745',
    WARNING: '#ffc107',
    FAIL: '#dc3545',
  };

  return `
<!DOCTYPE html>
<html>
<head>
  <title>Performance Analysis Report</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0;
      padding: 20px;
      background: #f5f5f5;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
      border-bottom: 2px solid #eee;
      padding-bottom: 20px;
    }
    .status {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 4px;
      color: white;
      font-weight: bold;
      background: ${statusColor[analysis.summary.status]};
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }
    .metric-card {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 4px;
      border: 1px solid #dee2e6;
    }
    .metric-card h3 {
      margin: 0 0 10px 0;
      color: #495057;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .metric-value {
      font-size: 32px;
      font-weight: bold;
      color: #212529;
      margin: 0;
    }
    .metric-unit {
      font-size: 16px;
      color: #6c757d;
      font-weight: normal;
    }
    .issues {
      background: #fff3cd;
      border: 1px solid #ffeaa7;
      border-radius: 4px;
      padding: 15px;
      margin: 20px 0;
    }
    .recommendations {
      background: #d1ecf1;
      border: 1px solid #bee5eb;
      border-radius: 4px;
      padding: 15px;
      margin: 20px 0;
    }
    .chart {
      margin: 20px 0;
      padding: 20px;
      background: #f8f9fa;
      border-radius: 4px;
    }
    ul {
      margin: 10px 0;
      padding-left: 20px;
    }
    li {
      margin: 5px 0;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Performance Analysis Report</h1>
      <div>
        <span class="status">${analysis.summary.status}</span>
        <p style="margin: 5px 0 0 0; color: #6c757d;">
          Generated: ${new Date(analysis.timestamp).toLocaleString()}
        </p>
      </div>
    </div>

    <h2>Load Test Results</h2>
    <div class="metrics-grid">
      <div class="metric-card">
        <h3>Total Requests</h3>
        <p class="metric-value">${analysis.load_test.requests.toLocaleString()}</p>
      </div>
      <div class="metric-card">
        <h3>Error Rate</h3>
        <p class="metric-value">
          ${(analysis.load_test.errors * 100).toFixed(2)}<span class="metric-unit">%</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>P95 Latency</h3>
        <p class="metric-value">
          ${analysis.load_test.p95_latency}<span class="metric-unit">ms</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>P99 Latency</h3>
        <p class="metric-value">
          ${analysis.load_test.p99_latency}<span class="metric-unit">ms</span>
        </p>
      </div>
    </div>

    <h2>Stress Test Results</h2>
    <div class="metrics-grid">
      <div class="metric-card">
        <h3>Max Concurrent Users</h3>
        <p class="metric-value">${analysis.stress_test.max_users}</p>
      </div>
      <div class="metric-card">
        <h3>Breaking Point</h3>
        <p class="metric-value">
          ${analysis.stress_test.breaking_point || 'Not Reached'}
          ${analysis.stress_test.breaking_point ? '<span class="metric-unit">users</span>' : ''}
        </p>
      </div>
      <div class="metric-card">
        <h3>Peak Error Rate</h3>
        <p class="metric-value">
          ${(analysis.stress_test.peak_error_rate * 100).toFixed(2)}<span class="metric-unit">%</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>Peak Latency</h3>
        <p class="metric-value">
          ${analysis.stress_test.peak_latency}<span class="metric-unit">ms</span>
        </p>
      </div>
    </div>

    <h2>Resource Usage</h2>
    <div class="metrics-grid">
      <div class="metric-card">
        <h3>Average CPU</h3>
        <p class="metric-value">
          ${analysis.resource_usage.cpu.average.toFixed(1)}<span class="metric-unit">%</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>Peak CPU</h3>
        <p class="metric-value">
          ${analysis.resource_usage.cpu.peak.toFixed(1)}<span class="metric-unit">%</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>Average Memory</h3>
        <p class="metric-value">
          ${analysis.resource_usage.memory.average.toFixed(1)}<span class="metric-unit">%</span>
        </p>
      </div>
      <div class="metric-card">
        <h3>Peak Memory</h3>
        <p class="metric-value">
          ${analysis.resource_usage.memory.peak.toFixed(1)}<span class="metric-unit">%</span>
        </p>
      </div>
    </div>

    ${analysis.summary.issues.length > 0 ? `
      <div class="issues">
        <h3>⚠️ Issues Detected</h3>
        <ul>
          ${analysis.summary.issues.map(issue => `<li>${issue}</li>`).join('')}
        </ul>
      </div>
    ` : ''}

    ${analysis.summary.recommendations.length > 0 ? `
      <div class="recommendations">
        <h3>💡 Recommendations</h3>
        <ul>
          ${analysis.summary.recommendations.map(rec => `<li>${rec}</li>`).join('')}
        </ul>
      </div>
    ` : ''}

    <div class="chart">
      <h3>Performance Trends</h3>
      <p style="color: #6c757d;">
        Note: For detailed performance trends and historical comparison, 
        integrate with your monitoring solution (DataDog, Grafana, etc.)
      </p>
    </div>
  </div>
</body>
</html>
  `;
}

// Main execution
function main() {
  console.log('Analyzing performance test results...');

  const loadResults = readResults('load-test-results.json');
  const stressResults = readResults('stress-test-results.json');

  if (!loadResults && !stressResults) {
    console.error('No test results found. Run load and stress tests first.');
    process.exit(1);
  }

  const analysis = analyzePerformance(loadResults, stressResults);

  // Write analysis results
  fs.writeFileSync(
    'performance-analysis.json',
    JSON.stringify(analysis, null, 2)
  );

  // Generate HTML report
  const htmlReport = generateHTMLReport(analysis);
  fs.writeFileSync('performance-analysis.html', htmlReport);

  console.log(`\nPerformance Analysis Complete:`);
  console.log(`Status: ${analysis.summary.status}`);
  
  if (analysis.summary.issues.length > 0) {
    console.log('\nIssues:');
    analysis.summary.issues.forEach(issue => console.log(`- ${issue}`));
  }
  
  if (analysis.summary.recommendations.length > 0) {
    console.log('\nRecommendations:');
    analysis.summary.recommendations.forEach(rec => console.log(`- ${rec}`));
  }

  console.log('\nReports generated:');
  console.log('- performance-analysis.json');
  console.log('- performance-analysis.html');

  // Exit with appropriate code
  process.exit(analysis.summary.status === 'FAIL' ? 1 : 0);
}

if (require.main === module) {
  main();
}

module.exports = { analyzePerformance, generateHTMLReport };