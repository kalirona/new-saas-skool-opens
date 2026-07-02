// Resource download load test.
// Simulates browsing resources, viewing file listings, and downloading.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import {
  BASE_URL, errorRate, resourceDuration, sharedThresholds,
  checkResponse, getAuthToken,
} from '../shared.js';

export const options = {
  scenarios: {
    resource_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 25 },
        { duration: '4m', target: 25 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    ...sharedThresholds,
    resource_download_duration_ms: ['p(95)<1000'],  // Downloads include transfer time
  },
};

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  group('Resource Downloads', () => {
    // 1. List content / courses (to find course resources)
    const start = Date.now();
    const coursesRes = http.get(`${BASE_URL}/api/v1/courses/`, { headers: authHeaders });
    resourceDuration.add(Date.now() - start);
    checkResponse(coursesRes, 'list courses');

    // 2. Get resource listings (if accessible)
    let spaceUuid = '';
    const communitiesRes = http.get(`${BASE_URL}/api/v1/communities/`, {
      headers: authHeaders,
    });
    if (communitiesRes.status === 200) {
      const communities = communitiesRes.json() as any[];
      if (communities && communities.length > 0) {
        const commUuid = communities[0].community_uuid || communities[0].uuid || '';
        if (commUuid) {
          const spacesStart = Date.now();
          const spacesRes = http.get(`${BASE_URL}/api/v1/communities/${commUuid}/spaces`, {
            headers: authHeaders,
          });
          resourceDuration.add(Date.now() - spacesStart);
          checkResponse(spacesRes, 'list spaces');

          if (spacesRes.status === 200) {
            const spaces = spacesRes.json() as any[];
            if (spaces && spaces.length > 0) {
              spaceUuid = spaces[0].space_uuid || spaces[0].uuid || '';
            }
          }
        }
      }
    }

    // 3. View resources in a space
    if (spaceUuid) {
      const resourcesStart = Date.now();
      const resourcesRes = http.get(
        `${BASE_URL}/api/v1/spaces/${spaceUuid}/resources`,
        { headers: authHeaders },
      );
      resourceDuration.add(Date.now() - resourcesStart);
      checkResponse(resourcesRes, 'list resources');
    }

    // 4. Download content file
    const contentStart = Date.now();
    const contentRes = http.get(
      `${BASE_URL}/api/v1/content/`,
      { headers: authHeaders },
    );
    resourceDuration.add(Date.now() - contentStart);
    // Content may 404 if no content exists — that's ok for load testing
    check(contentRes, {
      'content endpoint responded': (r) => r.status < 500,
    });

    // 5. Health check during download activity
    const healthStart = Date.now();
    const healthRes = http.get(`${BASE_URL}/api/v1/health/live`);
    resourceDuration.add(Date.now() - healthStart);
    checkResponse(healthRes, 'health during load');
  });

  sleep(2);
}
