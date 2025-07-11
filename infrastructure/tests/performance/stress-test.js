import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const cpuUsage = new Trend('cpu_usage');
const memoryUsage = new Trend('memory_usage');

// Stress test configuration - push system to breaking point
export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '2m', target: 200 },   // Ramp up to 200 users
    { duration: '2m', target: 300 },   // Ramp up to 300 users
    { duration: '2m', target: 400 },   // Ramp up to 400 users
    { duration: '2m', target: 500 },   // Ramp up to 500 users
    { duration: '5m', target: 500 },   // Stay at 500 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s even under stress
    errors: ['rate<0.5'],              // Error rate under 50% even under extreme load
    http_req_failed: ['rate<0.5'],     // HTTP failure rate under 50%
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://staging.bootstrap-awareness.de';

export default function () {
  // Heavy operations to stress the system
  const operations = [
    // Heavy read operation
    () => {
      const start = new Date();
      const res = http.get(`${BASE_URL}/api/v1/courses?limit=1000&include=all`);
      responseTime.add(new Date() - start);
      
      const success = check(res, {
        'Heavy read successful': (r) => r.status === 200 || r.status === 503,
      });
      errorRate.add(!success && res.status !== 503);
    },
    
    // Heavy write operation
    () => {
      const start = new Date();
      const res = http.post(
        `${BASE_URL}/api/v1/analytics/bulk`,
        JSON.stringify({
          events: Array.from({ length: 100 }, (_, i) => ({
            type: 'page_view',
            timestamp: new Date().toISOString(),
            data: { page: `/stress-test-${i}`, duration: Math.random() * 1000 },
          })),
        }),
        { headers: { 'Content-Type': 'application/json' } }
      );
      responseTime.add(new Date() - start);
      
      const success = check(res, {
        'Heavy write successful': (r) => r.status === 200 || r.status === 503,
      });
      errorRate.add(!success && res.status !== 503);
    },
    
    // Complex search operation
    () => {
      const start = new Date();
      const res = http.get(
        `${BASE_URL}/api/v1/search?q=${Math.random().toString(36)}&type=all&limit=100`
      );
      responseTime.add(new Date() - start);
      
      const success = check(res, {
        'Search successful': (r) => r.status === 200 || r.status === 503,
      });
      errorRate.add(!success && res.status !== 503);
    },
    
    // Concurrent API calls
    () => {
      const batch = [
        ['GET', `${BASE_URL}/api/v1/health`],
        ['GET', `${BASE_URL}/api/v1/courses`],
        ['GET', `${BASE_URL}/api/v1/users/me`],
        ['GET', `${BASE_URL}/api/v1/analytics/summary`],
      ];
      
      const start = new Date();
      const responses = http.batch(batch);
      responseTime.add(new Date() - start);
      
      responses.forEach((res) => {
        const success = res.status === 200 || res.status === 503;
        errorRate.add(!success && res.status !== 503);
      });
    },
  ];
  
  // Execute random operation
  const operation = operations[Math.floor(Math.random() * operations.length)];
  operation();
  
  // Monitor system metrics
  const metricsRes = http.get(`${BASE_URL}/api/v1/metrics/system`);
  if (metricsRes.status === 200) {
    const metrics = metricsRes.json();
    if (metrics.cpu) cpuUsage.add(metrics.cpu);
    if (metrics.memory) memoryUsage.add(metrics.memory);
  }
  
  // Variable think time based on load
  sleep(Math.random() * 2);
}

export function handleSummary(data) {
  return {
    'stress-test-summary.html': htmlReport(data),
    'stress-test-results.json': JSON.stringify(data, null, 2),
  };
}

function htmlReport(data) {
  const metrics = data.metrics;
  
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Stress Test Results</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; background: #f0f0f0; }
        .pass { color: green; }
        .fail { color: red; }
        .warning { color: orange; }
      </style>
    </head>
    <body>
      <h1>Stress Test Results</h1>
      <div class="metric">
        <h3>Response Times</h3>
        <p>P95: ${metrics.http_req_duration.values['p(95)']}ms</p>
        <p>P99: ${metrics.http_req_duration.values['p(99)']}ms</p>
      </div>
      <div class="metric">
        <h3>Error Rate</h3>
        <p class="${metrics.errors.rate < 0.1 ? 'pass' : metrics.errors.rate < 0.5 ? 'warning' : 'fail'}">
          ${(metrics.errors.rate * 100).toFixed(2)}%
        </p>
      </div>
      <div class="metric">
        <h3>System Resources</h3>
        <p>Peak CPU: ${metrics.cpu_usage?.values?.max || 'N/A'}%</p>
        <p>Peak Memory: ${metrics.memory_usage?.values?.max || 'N/A'}%</p>
      </div>
      <div class="metric">
        <h3>Breaking Point</h3>
        <p>System remained stable up to ${metrics.vus?.values?.max || 'N/A'} concurrent users</p>
      </div>
    </body>
    </html>
  `;
}