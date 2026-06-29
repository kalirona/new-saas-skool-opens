import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
  getResponseMetadata,
} from '@services/utils/ts/requests'

export interface Tag {
  id: number
  org_id: number
  tag_uuid: string
  name: string
  color: string | null
  creation_date: string
}

export interface TagCreate {
  name: string
  color?: string | null
}

export async function getTags(
  org_id: number,
  access_token?: string
): Promise<Tag[]> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/org/${org_id}/tags`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function createTag(
  org_id: number,
  data: TagCreate,
  access_token: string
): Promise<Tag> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/org/${org_id}/tags`,
    RequestBodyWithAuthHeader('POST', data, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) {
    const detail = res.data?.detail || res.data?.message || res.data
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    const error: any = new Error(message)
    error.status = res.status
    error.detail = detail
    throw error
  }
  return res.data
}

export async function deleteTag(
  tag_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/tags/${tag_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getResourceTags(
  resource_uuid: string,
  access_token?: string
): Promise<Tag[]> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}/tags`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function addTagToResource(
  resource_uuid: string,
  tag_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}/tags/${tag_uuid}`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function removeTagFromResource(
  resource_uuid: string,
  tag_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}/tags/${tag_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}
