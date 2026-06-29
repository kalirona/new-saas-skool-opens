import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
} from '@services/utils/ts/requests'

export interface Notification {
  id: number
  org_id: number
  user_id: number
  actor_id: number | null
  notification_uuid: string
  notification_type: string
  title: string
  message: string | null
  is_read: boolean
  resource_uuid: string | null
  parent_resource_uuid: string | null
  link: string | null
  creation_date: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  page: number
  limit: number
}

export async function getNotifications(
  params: {
    page?: number
    limit?: number
    unread_only?: boolean
  } = {},
  access_token?: string
): Promise<NotificationListResponse> {
  const { page = 1, limit = 20, unread_only = false } = params
  let url = `${getAPIUrl()}notifications?page=${page}&limit=${limit}&unread_only=${unread_only}`
  const result: any = await fetch(url, RequestBodyWithAuthHeader('GET', null, null, access_token))
  const res = await errorHandling(result)
  return res
}

export async function getUnreadCount(access_token?: string): Promise<number> {
  const result: any = await fetch(
    `${getAPIUrl()}notifications/unread-count`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res.count
}

export async function markAsRead(
  notification_uuid: string,
  access_token: string
): Promise<Notification> {
  const result: any = await fetch(
    `${getAPIUrl()}notifications/${notification_uuid}/read`,
    RequestBodyWithAuthHeader('PUT', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function markAllAsRead(access_token: string): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}notifications/read-all`,
    RequestBodyWithAuthHeader('PUT', null, null, access_token)
  )
  await errorHandling(result)
}
