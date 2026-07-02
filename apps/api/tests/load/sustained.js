// Combined sustained load test.
// Runs all six flow scenarios concurrently to detect memory leaks
// and ensure no performance degradation over a 30-minute sustained period.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import { Rate, Trend } from 'k6/metrics';
import {
  BASE_URL, errorRate, getAuthToken, randomString, checkResponse,
  loginDuration, communityDuration, aiDuration, checkoutDuration,
  eventDuration, resourceDuration,
} from './shared.js';

export const options = {
  scenarios: {
    sustained_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30m',
    },
  },
  thresholds: {
    errors: ['rate<0.01'],
    http_req_duration: ['p(95)<300', 'avg<150'],
    http_req_failed: ['rate<0.01'],
    login_duration_ms: ['p(95)<500'],
    community_browse_duration_ms: ['p(95)<300'],
    checkout_duration_ms: ['p(95)<500'],
    event_rsvp_duration_ms: ['p(95)<300'],
    resource_download_duration_ms: ['p(95)<1000'],
    // Memory leak detection: compare first 5m vs last 5m
    // (monitored externally via `k6 stats --timestamp`)
  },
};

// ── Flow implementations (same as individual scenarios) ──────────────────

function runLoginFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // Token verification
  const verifyRes = http.get(`${BASE_URL}/api/v1/auth/me`, { headers: authHeaders });
  checkResponse(verifyRes, 'token verification');
}

function runCommunityFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const listRes = http.get(`${BASE_URL}/api/v1/communities/`, { headers: authHeaders });
  checkResponse(listRes, 'list communities');

  if (listRes.status === 200) {
    const communities = listRes.json() as any[];
    if (communities && communities.length > 0) {
      const uuid = communities[0].community_uuid || communities[0].uuid || '';
      if (uuid) {
        http.get(`${BASE_URL}/api/v1/communities/${uuid}`, { headers: authHeaders });
        http.get(`${BASE_URL}/api/v1/communities/${uuid}/spaces`, { headers: authHeaders });
      }
    }
  }
}

function runCheckoutFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  http.get(`${BASE_URL}/api/v1/plans/`, { headers: authHeaders });
  http.get(`${BASE_URL}/api/v1/payments/user`, { headers: authHeaders });
}

function runEventFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const eventsRes = http.get(`${BASE_URL}/api/v1/events/`, { headers: authHeaders });
  if (eventsRes.status === 200) {
    const events = eventsRes.json() as any[];
    if (events && events.length > 0) {
      const uuid = events[0].event_uuid || events[0].uuid || '';
      if (uuid) {
        http.get(`${BASE_URL}/api/v1/events/${uuid}`, { headers: authHeaders });
      }
    }
  }
}

function runResourceFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  http.get(`${BASE_URL}/api/v1/courses/`, { headers: authHeaders });
  http.get(`${BASE_URL}/api/v1/content/`, { headers: authHeaders });
}

function runAiFlow(token: string) {
  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  http.post(
    `${BASE_URL}/api/v1/ai/generate-outline`,
    JSON.stringify({ topic: 'Test topic for sustained load', level: 'beginner' }),
    { headers: authHeaders },
  );
}

// ── Main ─────────────────────────────────────────────────────────────────

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  // Rotate through flows to simulate real user behavior
  const flow = __VU % 6;
  switch (flow) {
    case 0: runLoginFlow(token); break;
    case 1: runCommunityFlow(token); break;
    case 2: runAiFlow(token); break;
    case 3: runCheckoutFlow(token); break;
    case 4: runEventFlow(token); break;
    case 5: runResourceFlow(token); break;
  }

  // Health check every iteration
  const healthRes = http.get(`${BASE_URL}/api/v1/health/live`);
  check(healthRes, { 'health check ok': (r) => r.status === 200 });

  sleep(3);
}
