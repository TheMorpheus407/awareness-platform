import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const apiDuration = new Trend('api_duration');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    errors: ['rate<0.1'],                            // Error rate under 10%
    http_req_failed: ['rate<0.1'],                   // HTTP failure rate under 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://staging.bootstrap-awareness.de';

// Test data
const testUsers = Array.from({ length: 100 }, (_, i) => ({
  email: `loadtest${i}@example.com`,
  password: 'LoadTest123!',
}));

export function setup() {
  // Create test users if needed
  console.log('Setting up load test environment...');
  
  const setupRes = http.post(
    `${BASE_URL}/api/v1/test/setup`,
    JSON.stringify({ createTestUsers: true }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(setupRes, {
    'Setup successful': (r) => r.status === 200,
  });
  
  return { testUsers };
}

export default function (data) {
  // Select random test user
  const user = data.testUsers[Math.floor(Math.random() * data.testUsers.length)];
  
  // Scenario 1: User Login
  const loginStart = new Date();
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({
      username: user.email,
      password: user.password,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  loginDuration.add(new Date() - loginStart);
  
  const loginSuccess = check(loginRes, {
    'Login successful': (r) => r.status === 200,
    'Token received': (r) => r.json('access_token') !== undefined,
  });
  
  errorRate.add(!loginSuccess);
  
  if (!loginSuccess) return;
  
  const token = loginRes.json('access_token');
  const authHeaders = {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
  
  // Scenario 2: Browse Courses
  const apiStart = new Date();
  const coursesRes = http.get(`${BASE_URL}/api/v1/courses`, authHeaders);
  apiDuration.add(new Date() - apiStart);
  
  check(coursesRes, {
    'Courses loaded': (r) => r.status === 200,
    'Courses array received': (r) => Array.isArray(r.json('courses')),
  });
  
  sleep(1); // User think time
  
  // Scenario 3: View Course Details
  if (coursesRes.status === 200) {
    const courses = coursesRes.json('courses');
    if (courses.length > 0) {
      const course = courses[Math.floor(Math.random() * courses.length)];
      const courseRes = http.get(
        `${BASE_URL}/api/v1/courses/${course.id}`,
        authHeaders
      );
      
      check(courseRes, {
        'Course details loaded': (r) => r.status === 200,
      });
    }
  }
  
  sleep(2); // User think time
  
  // Scenario 4: Start Course
  const startCourseRes = http.post(
    `${BASE_URL}/api/v1/courses/1/start`,
    null,
    authHeaders
  );
  
  check(startCourseRes, {
    'Course started': (r) => r.status === 200 || r.status === 409, // 409 if already started
  });
  
  sleep(1);
  
  // Scenario 5: Submit Progress
  const progressRes = http.post(
    `${BASE_URL}/api/v1/courses/1/progress`,
    JSON.stringify({
      moduleId: 1,
      progress: Math.random() * 100,
      timeSpent: Math.floor(Math.random() * 300),
    }),
    authHeaders
  );
  
  check(progressRes, {
    'Progress saved': (r) => r.status === 200,
  });
  
  sleep(0.5);
  
  // Scenario 6: View Dashboard
  const dashboardRes = http.get(`${BASE_URL}/api/v1/dashboard`, authHeaders);
  
  check(dashboardRes, {
    'Dashboard loaded': (r) => r.status === 200,
    'Stats received': (r) => r.json('stats') !== undefined,
  });
  
  sleep(2);
}

export function teardown(data) {
  // Clean up test data
  console.log('Cleaning up load test environment...');
  
  const cleanupRes = http.post(
    `${BASE_URL}/api/v1/test/cleanup`,
    JSON.stringify({ removeTestUsers: true }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(cleanupRes, {
    'Cleanup successful': (r) => r.status === 200,
  });
}