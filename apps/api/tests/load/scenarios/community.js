// Community browsing load test.
// Simulates browsing communities, spaces, posts, and comments.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import {
  BASE_URL, errorRate, communityDuration, sharedThresholds,
  checkResponse, getAuthToken, randomString,
} from '../shared.js';

export const options = {
  scenarios: {
    community_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 30 },
        { duration: '4m', target: 30 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    ...sharedThresholds,
    community_browse_duration_ms: ['p(95)<300'],
  },
};

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  group('Community Browsing', () => {
    // 1. List communities
    const start = Date.now();
    const listRes = http.get(`${BASE_URL}/api/v1/communities/`, { headers: authHeaders });
    communityDuration.add(Date.now() - start);
    checkResponse(listRes, 'list communities');

    // 2. Get community details (if any exist)
    let communityUuid = '';
    if (listRes.status === 200) {
      const communities = listRes.json() as any[];
      if (communities && communities.length > 0) {
        communityUuid = communities[0].community_uuid || communities[0].uuid || '';
      }
    }

    if (communityUuid) {
      // 3. View community
      const viewStart = Date.now();
      const viewRes = http.get(`${BASE_URL}/api/v1/communities/${communityUuid}`, {
        headers: authHeaders,
      });
      communityDuration.add(Date.now() - viewStart);
      checkResponse(viewRes, 'view community');

      // 4. List spaces
      const spacesStart = Date.now();
      const spacesRes = http.get(`${BASE_URL}/api/v1/communities/${communityUuid}/spaces`, {
        headers: authHeaders,
      });
      communityDuration.add(Date.now() - spacesStart);
      checkResponse(spacesRes, 'list spaces');

      // 5. List posts
      const postsStart = Date.now();
      const postsRes = http.get(`${BASE_URL}/api/v1/communities/${communityUuid}/posts`, {
        headers: authHeaders,
      });
      communityDuration.add(Date.now() - postsStart);
      checkResponse(postsRes, 'list posts');
    }

    // 6. Search communities
    const searchStart = Date.now();
    const searchRes = http.get(`${BASE_URL}/api/v1/communities/search?q=test`, {
      headers: authHeaders,
    });
    communityDuration.add(Date.now() - searchStart);
    checkResponse(searchRes, 'search communities');
  });

  sleep(2);
}
