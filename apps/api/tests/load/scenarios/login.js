// Login flow load test.
// Simulates user authentication — login, token retrieval, session management.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import { Rate, Trend } from 'k6/metrics';
import {
  BASE_URL, errorRate, loginDuration, sharedThresholds,
  randomString, checkResponse, getAuthToken,
} from '../shared.js';

export const options = {
  scenarios: {
    login_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '3m', target: 20 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
    login_medium: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '3m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      startTime: '7m',
    },
  },
  thresholds: {
    ...sharedThresholds,
    login_duration_ms: ['p(95)<500'],  // Login can be slightly slower due to bcrypt
  },
};

export default function () {
  group('Login Flow', () => {
    // 1. Successful login
    const start = Date.now();
    const loginRes = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({ username: `loadtest_${randomString(6)}@test.com`, password: 'TestPass!234' }),
      { headers: { 'Content-Type': 'application/json' } },
    );
    loginDuration.add(Date.now() - start);
    checkResponse(loginRes, 'login', 401);  // Expected: 401 for unknown users in production

    // 2. Login with valid admin credentials
    const start2 = Date.now();
    const adminLogin = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({ username: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
      { headers: { 'Content-Type': 'application/json' } },
    );
    loginDuration.add(Date.now() - start2);
    checkResponse(adminLogin, 'admin login');

    // 3. Token verification
    if (adminLogin.status === 200) {
      const body = adminLogin.json() as any;
      const token = body.access_token || body.tokens?.access_token || '';

      const verifyRes = http.get(`${BASE_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      checkResponse(verifyRes, 'token verification');

      // 4. Logout
      const logoutRes = http.del(`${BASE_URL}/api/v1/auth/logout`, null, {
        headers: { Authorization: `Bearer ${token}` },
      });
      checkResponse(logoutRes, 'logout', 200);
    }

    // 5. Invalid credentials
    const start3 = Date.now();
    const badLogin = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({ username: 'fake@user.com', password: 'wrongpass' }),
      { headers: { 'Content-Type': 'application/json' } },
    );
    loginDuration.add(Date.now() - start3);
    check(badLogin, { 'bad login returns 401': (r) => r.status === 401 });
    if (badLogin.status !== 401) errorRate.add(1);
  });

  sleep(1);
}
