// AI generation load test.
// Simulates AI course outline and content generation requests.
// Note: AI endpoints are expected to be slower — thresholds are adjusted.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import {
  BASE_URL, errorRate, aiDuration, sharedThresholds,
  checkResponse, getAuthToken, randomString,
} from '../shared.js';

export const options = {
  scenarios: {
    ai_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 5 },
        { duration: '3m', target: 5 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    ...sharedThresholds,
    ai_generation_duration_ms: ['p(95)<30000'],  // AI is slow — 30s p95
    http_req_duration: ['p(95)<30000'],           // Override default
  },
};

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const suffix = randomString(4);

  group('AI Generation', () => {
    // 1. Generate course outline
    const start = Date.now();
    const outlineRes = http.post(
      `${BASE_URL}/api/v1/ai/generate-outline`,
      JSON.stringify({
        topic: `Introduction to ${suffix} — a beginner's guide`,
        level: 'beginner',
        language: 'en',
      }),
      { headers: authHeaders },
    );
    aiDuration.add(Date.now() - start);
    checkResponse(outlineRes, 'generate outline', 200);
    sleep(1);

    // 2. Generate lesson content (if outline succeeded)
    if (outlineRes.status === 200) {
      const contentStart = Date.now();
      const contentRes = http.post(
        `${BASE_URL}/api/v1/ai/generate-content`,
        JSON.stringify({
          topic: `Lesson 1: Getting started with ${suffix}`,
          format: 'markdown',
          tone: 'educational',
        }),
        { headers: authHeaders },
      );
      aiDuration.add(Date.now() - contentStart);
      checkResponse(contentRes, 'generate content', 200);
      sleep(1);
    }

    // 3. Generate assessment
    const assessStart = Date.now();
    const assessRes = http.post(
      `${BASE_URL}/api/v1/ai/courseplanning/assessment`,
      JSON.stringify({
        topic: `Core concepts of ${suffix}`,
        num_questions: 5,
        difficulty: 'beginner',
      }),
      { headers: authHeaders },
    );
    aiDuration.add(Date.now() - assessStart);
    checkResponse(assessRes, 'generate assessment', 200);
  });

  sleep(3);
}
