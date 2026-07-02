// Event RSVP load test.
// Simulates listing events, viewing event details, registering, and cancelling.

import { check, sleep, group } from 'k6';
import http from 'k6/http';
import {
  BASE_URL, errorRate, eventDuration, sharedThresholds,
  checkResponse, getAuthToken,
} from '../shared.js';

export const options = {
  scenarios: {
    event_light: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '3m', target: 20 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    ...sharedThresholds,
    event_rsvp_duration_ms: ['p(95)<300'],
  },
};

export default function () {
  const token = getAuthToken();
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  group('Event RSVP', () => {
    // 1. List upcoming events
    const start = Date.now();
    const eventsRes = http.get(`${BASE_URL}/api/v1/events/`, { headers: authHeaders });
    eventDuration.add(Date.now() - start);
    checkResponse(eventsRes, 'list events');

    // 2. View event details
    let eventUuid = '';
    if (eventsRes.status === 200) {
      const events = eventsRes.json() as any[];
      if (events && events.length > 0) {
        eventUuid = events[0].event_uuid || events[0].uuid || '';
      }
    }

    if (eventUuid) {
      const detailStart = Date.now();
      const detailRes = http.get(`${BASE_URL}/api/v1/events/${eventUuid}`, {
        headers: authHeaders,
      });
      eventDuration.add(Date.now() - detailStart);
      checkResponse(detailRes, 'event details');

      // 3. Register for event
      const rsvpStart = Date.now();
      const rsvpRes = http.post(
        `${BASE_URL}/api/v1/events/${eventUuid}/register`,
        null,
        { headers: authHeaders },
      );
      eventDuration.add(Date.now() - rsvpStart);
      check(rsvpRes, {
        'registration responded': (r) => r.status === 200 || r.status === 409,  // 409 = already registered
      });

      // 4. View attendees
      const attendStart = Date.now();
      const attendRes = http.get(`${BASE_URL}/api/v1/events/${eventUuid}/attendees`, {
        headers: authHeaders,
      });
      eventDuration.add(Date.now() - attendStart);
      checkResponse(attendRes, 'list attendees');

      // 5. Cancel registration
      const cancelStart = Date.now();
      const cancelRes = http.del(
        `${BASE_URL}/api/v1/events/${eventUuid}/register`,
        null,
        { headers: authHeaders },
      );
      eventDuration.add(Date.now() - cancelStart);
      checkResponse(cancelRes, 'cancel registration', 200);
    }
  });

  sleep(2);
}
