import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
  getResponseMetadata,
} from '@services/utils/ts/requests'

export interface Event {
  id: number
  org_id: number
  author_id: number
  event_uuid: string
  title: string
  description: string | null
  event_date: string
  event_time: string | null
  timezone: string | null
  meeting_url: string | null
  visibility: string
  creation_date: string
  update_date: string
}

export interface EventCreate {
  title: string
  description?: string | null
  event_date: string
  event_time?: string | null
  timezone?: string | null
  meeting_url?: string | null
  visibility?: string
}

export interface EventUpdate {
  title?: string
  description?: string | null
  event_date?: string
  event_time?: string | null
  timezone?: string | null
  meeting_url?: string | null
  visibility?: string
}

export interface EventListResponse {
  events: Event[]
  total: number
  page: number
  limit: number
}

export async function getEvents(
  org_id: number,
  params: {
    page?: number
    limit?: number
    upcoming?: boolean
    search?: string
    sort_by?: string
  } = {},
  access_token?: string
): Promise<EventListResponse> {
  const { page = 1, limit = 20, upcoming = false, search, sort_by = 'date_asc' } = params
  let url = `${getAPIUrl()}events/org/${org_id}?page=${page}&limit=${limit}&upcoming=${upcoming}&sort_by=${sort_by}`
  if (search) url += `&search=${encodeURIComponent(search)}`
  const result: any = await fetch(url, RequestBodyWithAuthHeader('GET', null, null, access_token))
  const res = await errorHandling(result)
  return res
}

export async function getUpcomingEvents(
  org_id: number,
  limit: number = 5,
  access_token?: string
): Promise<Event[]> {
  const result: any = await fetch(
    `${getAPIUrl()}events/org/${org_id}/upcoming?limit=${limit}`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getEvent(
  event_uuid: string,
  access_token?: string
): Promise<Event> {
  const result: any = await fetch(
    `${getAPIUrl()}events/${event_uuid}`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function createEvent(
  org_id: number,
  data: EventCreate,
  access_token: string
): Promise<Event> {
  const result: any = await fetch(
    `${getAPIUrl()}events/org/${org_id}`,
    RequestBodyWithAuthHeader('POST', data, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) {
    const detail = res.data?.detail || res.data?.message || res.data
    let message: string
    if (typeof detail === 'string') {
      message = detail
    } else if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
      message = detail.message
    } else {
      message = JSON.stringify(detail)
    }
    const error: any = new Error(message)
    error.status = res.status
    error.detail = detail
    throw error
  }
  return res.data
}

export async function updateEvent(
  event_uuid: string,
  data: EventUpdate,
  access_token: string
): Promise<Event> {
  const result: any = await fetch(
    `${getAPIUrl()}events/${event_uuid}`,
    RequestBodyWithAuthHeader('PUT', data, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) {
    const detail = res.data?.detail || res.data?.message || res.data
    let message: string
    if (typeof detail === 'string') {
      message = detail
    } else if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
      message = detail.message
    } else {
      message = JSON.stringify(detail)
    }
    const error: any = new Error(message)
    error.status = res.status
    error.detail = detail
    throw error
  }
  return res.data
}

export async function deleteEvent(
  event_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}events/${event_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}
