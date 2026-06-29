// LearnHouse Load Testing Scenarios
// Run: k6 run scenarios.js
// Options: k6 run --env BASE_URL=http://localhost:1338 --env ADMIN_TOKEN=xxx scenarios.js

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { SharedArray } from 'k6/data';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:1338';
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || '';

const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency_ms');
const dbQueryLatency = new Trend('db_query_latency_ms');
const healthRequests = new Counter('health_requests');

// ── 10 Creators (light load) ───────────────────────────────────────────

export const light_load = {
  stages: [
    { duration: '2m', target: 10 },  // ramp up to 10 VUs
    { duration: '5m', target: 10 },  // steady
    { duration: '1m', target: 0 },   // ramp down
  ],
  thresholds: {
    'api_latency_ms': ['avg<200', 'p(95)<500'],
    'errors': ['rate<0.01'],
  },
};

// ── 100 Creators (medium load) ─────────────────────────────────────────

export const medium_load = {
  stages: [
    { duration: '3m', target: 100 },
    { duration: '10m', target: 100 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    'api_latency_ms': ['avg<500', 'p(95)<1500'],
    'errors': ['rate<0.02'],
  },
};

// ── 1,000 Creators (high load) ─────────────────────────────────────────

export const high_load = {
  stages: [
    { duration: '5m', target: 1000 },
    { duration: '15m', target: 1000 },
    { duration: '3m', target: 0 },
  ],
  thresholds: {
    'api_latency_ms': ['avg<1000', 'p(95)<3000'],
    'errors': ['rate<0.05'],
  },
};

// ── 10,000 Concurrent Members (stress) ─────────────────────────────────

export const stress_test = {
  stages: [
    { duration: '5m', target: 5000 },
    { duration: '5m', target: 10000 },
    { duration: '10m', target: 10000 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    'api_latency_ms': ['avg<2000', 'p(95)<5000'],
    'errors': ['rate<0.10'],
  },
};

// ── Default options ────────────────────────────────────────────────────

export const options = {
  scenarios: {
    light_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: light_load.stages,
      tags: { scenario: 'light' },
      gracefulStop: '30s',
    },
  },
  // Uncomment to run all scenarios sequentially:
  // scenarios: {
  //   light: { executor: 'ramping-vus', stages: light_load.stages, startVUs: 0, gracefulStop: '30s' },
  //   medium: { executor: 'ramping-vus', stages: medium_load.stages, startVUs: 0, gracefulStop: '30s' },
  //   high: { executor: 'ramping-vus', stages: high_load.stages, startVUs: 0, gracefulStop: '30s' },
  //   stress: { executor: 'ramping-vus', stages: stress_test.stages, startVUs: 0, gracefulStop: '30s' },
  // },
};

// ── Headers ────────────────────────────────────────────────────────────

function authHeaders(token) {
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

// ── Public endpoints (no auth needed) ──────────────────────────────────

function publicEndpoints() {
  group('public health checks', () => {
    const endpoints = ['/api/v1/health', '/api/v1/health/live', '/api/v1/health/ready',
                       '/api/v1/health/database', '/api/v1/health/redis', '/api/v1/health/storage'];

    endpoints.forEach(endpoint => {
      const url = `${BASE_URL}${endpoint}`;
      const tStart = Date.now();
      const res = http.get(url, { tags: { endpoint } });
      const latency = Date.now() - tStart;
      apiLatency.add(latency);
      healthRequests.add(1);

      check(res, {
        [`${endpoint} status 200`]: (r) => r.status === 200,
      }) || errorRate.add(1);

      if (latency > 200) console.warn(`Slow ${endpoint}: ${latency}ms`);
      sleep(0.1);
    });
  });

  group('public content', () => {
    const res = http.get(`${BASE_URL}/`);
    check(res, { 'root endpoint ok': (r) => r.status === 200 }) || errorRate.add(1);
    apiLatency.add(res.timings.duration);
    sleep(0.5);
  });
}

// ── Authenticated endpoints (admin) ────────────────────────────────────

function authenticatedEndpoints(token) {
  const headers = authHeaders(token);

  group('org listings', () => {
    const res = http.get(`${BASE_URL}/api/v1/orgs`, { headers, tags: { endpoint: 'orgs' } });
    apiLatency.add(res.timings.duration);
    check(res, { 'orgs status 200': (r) => r.status === 200 }) || errorRate.add(1);
    sleep(0.3);
  });

  group('course listing', () => {
    const res = http.get(`${BASE_URL}/api/v1/courses`, { headers, tags: { endpoint: 'courses' } });
    apiLatency.add(res.timings.duration);
    check(res, { 'courses status 200': (r) => r.status === 200 }) || errorRate.add(1);
    sleep(0.3);
  });

  group('community listing', () => {
    const res = http.get(`${BASE_URL}/api/v1/communities`, { headers, tags: { endpoint: 'communities' } });
    apiLatency.add(res.timings.duration);
    check(res, { 'communities status 200': (r) => r.status === 200 }) || errorRate.add(1);
    sleep(0.3);
  });

  group('resource listing', () => {
    const res = http.get(`${BASE_URL}/api/v1/resources`, { headers, tags: { endpoint: 'resources' } });
    apiLatency.add(res.timings.duration);
    check(res, { 'resources status 200': (r) => r.status === 200 }) || errorRate.add(1);
    sleep(0.3);
  });
}

// ── Virtual user iteration ─────────────────────────────────────────────

export default function () {
  publicEndpoints();

  if (ADMIN_TOKEN) {
    authenticatedEndpoints(ADMIN_TOKEN);
  }

  // Brief think time between iterations
  sleep(1);
}

// ── Teardown ───────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`\n=== Load Test Complete ===`);
  console.log(`  Health requests: ${healthRequests.name}`);
  console.log(`  Error rate: ${errorRate.name}`);
}
