import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
  getResponseMetadata,
} from '@services/utils/ts/requests'

export interface Space {
  id: number
  community_id: number
  org_id: number
  space_uuid: string
  name: string
  icon: string | null
  description: string | null
  ordering: number
  visibility: string
  creation_date: string
  update_date: string
}

export interface SpaceCreate {
  name: string
  icon?: string | null
  description?: string | null
  ordering?: number
  visibility?: string
}

export interface SpaceUpdate {
  name?: string
  icon?: string | null
  description?: string | null
  ordering?: number
  visibility?: string
}

export async function getSpaces(
  community_uuid: string,
  access_token?: string
): Promise<Space[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/spaces`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getSpace(
  space_uuid: string,
  access_token?: string
): Promise<Space> {
  const result: any = await fetch(
    `${getAPIUrl()}spaces/${space_uuid}`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function createSpace(
  community_uuid: string,
  data: SpaceCreate,
  access_token: string
): Promise<Space> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/spaces`,
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

export async function updateSpace(
  space_uuid: string,
  data: SpaceUpdate,
  access_token: string
): Promise<Space> {
  const result: any = await fetch(
    `${getAPIUrl()}spaces/${space_uuid}`,
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

export async function deleteSpace(
  space_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}spaces/${space_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}
