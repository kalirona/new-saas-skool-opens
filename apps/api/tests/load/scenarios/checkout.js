// Checkout / payment flow load test.
// Simulates viewing plans and initiating checkout sessions.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import {
  BASE_URL, errorRate, checkoutDuration, sharedThresholds,
  checkResponse, getAuthToken,
} from '../shared.js';

export const options = {
  scenarios: {
    checkout_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 15 },
        { duration: '3m', target: 15 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    ...sharedThresholds,
    checkout_duration_ms: ['p(95)<500'],
  },
};

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  group('Checkout Flow', () => {
    // 1. List available plans
    const start = Date.now();
    const plansRes = http.get(`${BASE_URL}/api/v1/plans/`, { headers: authHeaders });
    checkoutDuration.add(Date.now() - start);
    checkResponse(plansRes, 'list plans');

    // 2. Get plan details
    let planUuid = '';
    if (plansRes.status === 200) {
      const plans = plansRes.json() as any[];
      if (plans && plans.length > 0) {
        planUuid = plans[0].plan_uuid || plans[0].uuid || '';
      }
    }

    if (planUuid) {
      const detailStart = Date.now();
      const detailRes = http.get(`${BASE_URL}/api/v1/plans/${planUuid}`, {
        headers: authHeaders,
      });
      checkoutDuration.add(Date.now() - detailStart);
      checkResponse(detailRes, 'plan details');

      // 3. Create checkout session
      const checkoutStart = Date.now();
      const checkoutRes = http.post(
        `${BASE_URL}/api/v1/offers/${planUuid}/checkout`,
        JSON.stringify({
          success_url: `${BASE_URL}/payment/success`,
          cancel_url: `${BASE_URL}/payment/cancel`,
          org_id: 1,
        }),
        { headers: authHeaders },
      );
      checkoutDuration.add(Date.now() - checkoutStart);
      // Checkout may be 400 if Stripe not configured
      check(checkoutRes, {
        'checkout session responded': (r) => r.status === 200 || r.status === 400,
      });
      if (checkoutRes.status === 200) {
        const body = checkoutRes.json() as any;
        check(body, {
          'checkout has session_url': (_b: any) => Boolean(_b.session_url),
        });
      }
    }

    // 4. Payment history
    const histStart = Date.now();
    const historyRes = http.get(`${BASE_URL}/api/v1/payments/user`, {
      headers: authHeaders,
    });
    checkoutDuration.add(Date.now() - histStart);
    checkResponse(historyRes, 'payment history', 200);
  });

  sleep(2);
}
