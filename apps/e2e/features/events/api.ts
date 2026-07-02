import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededEvent {
  eventUuid: string
}

export async function seedEvent(
  adminToken: string,
  org: Org,
  title: string,
  startDate: string,
): Promise<SeededEvent> {
  const event = await req<any>('POST', `/events/?org_id=${org.id}`, adminToken, {
    title,
    description: 'E2E test event',
    start_date: startDate,
    end_date: startDate,
    type: 'live',
    max_attendees: 100,
  })
  return { eventUuid: event.event_uuid }
}
