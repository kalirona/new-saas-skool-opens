// Shared k6 test configuration and helper functions.
// Imported by all scenario files.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import { Rate, Trend, Counter } from 'k6/metrics';

// ── Environment ──────────────────────────────────────────────────────────
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:9000';
export const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || 'admin@school.dev';
export const ADMIN_PASSWORD = __ENV.ADMIN_PASSWORD || 'E2eTestAdmin!234';
export const STUDENT_EMAIL = __ENV.STUDENT_EMAIL || 'student@test.com';
export const STUDENT_PASSWORD = __ENV.STUDENT_PASSWORD || 'TestPass!234';

// ── Custom metrics ───────────────────────────────────────────────────────
export const errorRate = new Rate('errors');
export const loginDuration = new Trend('login_duration_ms');
export const communityDuration = new Trend('community_browse_duration_ms');
export const aiDuration = new Trend('ai_generation_duration_ms');
export const checkoutDuration = new Trend('checkout_duration_ms');
export const eventDuration = new Trend('event_rsvp_duration_ms');
export const resourceDuration = new Trend('resource_download_duration_ms');
export const apiCalls = new Counter('api_calls_total');

// ── Shared thresholds ────────────────────────────────────────────────────
export const sharedThresholds = {
  errors: ['rate<0.01'],             // Error rate < 1%
  http_req_duration: ['p(95)<300'],  // p95 API latency < 300ms (excluding AI)
};

// ── Helpers ──────────────────────────────────────────────────────────────
let cachedToken = '';

export function getAuthToken(forceRefresh = false): string {
  if (cachedToken && !forceRefresh) return cachedToken;
  const url = `${BASE_URL}/api/v1/auth/login`;
  const payload = { username: ADMIN_EMAIL, password: ADMIN_PASSWORD };
  const res = http.post(url, JSON.stringify(payload), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res, { 'login succeeded': (r) => r.status === 200 });
  if (res.status === 200) {
    const body = res.json() as any;
    cachedToken = body.access_token || body.tokens?.access_token || '';
  }
  return cachedToken;
}

export function checkResponse(res: any, label: string, expectedStatus = 200) {
  const ok = check(res, {
    [`${label} status ${expectedStatus}`]: (r: any) => r.status === expectedStatus,
    [`${label} body present`]: (r: any) => r.body && r.body.length > 0,
  });
  if (!ok) errorRate.add(1);
  apiCalls.add(1);
}

export function randomString(len = 8): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < len; i++) result += chars[Math.floor(Math.random() * chars.length)];
  return result;
}
