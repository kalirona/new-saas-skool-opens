import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  RequestBodyFormWithAuthHeader,
  errorHandling,
  getResponseMetadata,
} from '@services/utils/ts/requests'

export const RESOURCE_TYPES = ['pdf', 'video', 'link', 'download', 'template'] as const
export type ResourceType = typeof RESOURCE_TYPES[number]

export interface Resource {
  id: number
  org_id: number
  author_id: number
  folder_id: number | null
  community_id: number | null
  space_id: number | null
  resource_uuid: string
  title: string
  description: string | null
  resource_type: ResourceType
  url: string | null
  file_id: string | null
  file_size: number | null
  file_mime: string | null
  file_format: string | null
  thumbnail_image: string | null
  visibility: string
  locked: boolean
  content: string | null
  metadata: Record<string, any> | null
  embed_url: string | null
  category: string | null
  featured: boolean
  pinned: boolean
  creation_date: string
  update_date: string
}

export interface ResourceDetail extends Resource {
  community_name?: string | null
  community_uuid?: string | null
  community_thumbnail?: string | null
  author_username?: string | null
  author_avatar?: string | null
  author_first_name?: string | null
  author_last_name?: string | null
  org_uuid?: string | null
  user_has_access?: boolean
  required_plan_name?: string | null
}

export interface ResourceCreate {
  title: string
  description?: string | null
  resource_type: ResourceType
  url?: string | null
  file_id?: string | null
  file_size?: number | null
  file_mime?: string | null
  file_format?: string | null
  thumbnail_image?: string | null
  visibility?: string
  locked?: boolean
  content?: string | null
  metadata?: Record<string, any> | null
  embed_url?: string | null
  category?: string | null
  featured?: boolean
  pinned?: boolean
  folder_id?: number | null
  community_id?: number | null
  space_id?: number | null
}

export interface ResourceUpdate {
  title?: string
  description?: string | null
  resource_type?: ResourceType
  url?: string | null
  file_id?: string | null
  file_size?: number | null
  file_mime?: string | null
  file_format?: string | null
  thumbnail_image?: string | null
  visibility?: string
  locked?: boolean
  content?: string | null
  metadata?: Record<string, any> | null
  embed_url?: string | null
  category?: string | null
  featured?: boolean
  pinned?: boolean
  folder_id?: number | null
  community_id?: number | null
  space_id?: number | null
}

export interface ResourceListResponse {
  resources: Resource[]
  total: number
  page: number
  limit: number
}

export type ResourceSortBy = 'newest' | 'oldest' | 'title'

export async function getResources(
  org_id: number,
  params: {
    page?: number
    limit?: number
    resource_type?: string | null
    folder_id?: number | null
    tag_id?: number | null
    search?: string | null
    sort_by?: ResourceSortBy
    category?: string | null
    featured?: boolean | null
    pinned?: boolean | null
    community_id?: number | null
    space_id?: number | null
  } = {},
  access_token?: string
): Promise<ResourceListResponse> {
  const { page = 1, limit = 20, resource_type, folder_id, tag_id, search, sort_by = 'newest', category, featured, pinned, community_id, space_id } = params
  let url = `${getAPIUrl()}resources/org/${org_id}?page=${page}&limit=${limit}&sort_by=${sort_by}`
  if (resource_type) url += `&resource_type=${resource_type}`
  if (folder_id !== undefined && folder_id !== null) url += `&folder_id=${folder_id}`
  if (tag_id !== undefined && tag_id !== null) url += `&tag_id=${tag_id}`
  if (search) url += `&search=${encodeURIComponent(search)}`
  if (category) url += `&category=${encodeURIComponent(category)}`
  if (featured !== undefined && featured !== null) url += `&featured=${featured}`
  if (pinned !== undefined && pinned !== null) url += `&pinned=${pinned}`
  if (community_id !== undefined && community_id !== null) url += `&community_id=${community_id}`
  if (space_id !== undefined && space_id !== null) url += `&space_id=${space_id}`
  const result: any = await fetch(url, RequestBodyWithAuthHeader('GET', null, null, access_token))
  const res = await errorHandling(result)
  return res
}

export async function getResource(
  resource_uuid: string,
  access_token?: string
): Promise<ResourceDetail> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function createResource(
  org_id: number,
  data: ResourceCreate,
  access_token: string
): Promise<Resource> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/org/${org_id}`,
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

export async function updateResource(
  resource_uuid: string,
  data: ResourceUpdate,
  access_token: string
): Promise<Resource> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}`,
    RequestBodyWithAuthHeader('PUT', data, null, access_token)
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

export async function deleteResource(
  resource_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function uploadResourceThumbnail(
  resource_uuid: string,
  formData: FormData,
  org_uuid: string,
  access_token: string
): Promise<Resource> {
  const result: any = await fetch(
    `${getAPIUrl()}resources/${resource_uuid}/thumbnail?org_uuid=${org_uuid}`,
    RequestBodyFormWithAuthHeader('PUT', formData, null, access_token)
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
