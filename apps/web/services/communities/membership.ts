import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
  getResponseMetadata,
} from '@services/utils/ts/requests'

export interface MembershipPlan {
  id: number
  org_id: number
  community_id: number
  plan_uuid: string
  name: string
  slug: string
  description: string | null
  price: number
  currency: string
  interval: string
  max_members: number
  is_free: boolean
  is_public: boolean
  trial_days: number
  display_order: number
  features: Record<string, any> | null
  status: string
  usergroup_id: number | null
  billing_provider: string | null
  billing_provider_plan_id: string | null
  creation_date: string
  update_date: string
}

export interface MembershipPlanCreate {
  name: string
  slug?: string
  description?: string | null
  price?: number
  currency?: string
  interval?: string
  max_members?: number
  is_free?: boolean
  is_public?: boolean
  trial_days?: number
  display_order?: number
  features?: Record<string, any> | null
  status?: string
  usergroup_id?: number | null
  billing_provider?: string | null
  billing_provider_plan_id?: string | null
}

export interface MembershipPlanUpdate {
  name?: string
  slug?: string
  description?: string | null
  price?: number
  currency?: string
  interval?: string
  max_members?: number
  is_free?: boolean
  is_public?: boolean
  trial_days?: number
  display_order?: number
  features?: Record<string, any> | null
  status?: string
  usergroup_id?: number | null
  billing_provider?: string | null
  billing_provider_plan_id?: string | null
}

export interface MembershipBenefit {
  id: number
  plan_id: number
  benefit_type: string
  benefit_value: Record<string, any> | null
  creation_date: string
  update_date: string
}

export interface MembershipBenefitData {
  benefit_type: string
  benefit_value: Record<string, any> | null
}

export interface CommunityMember {
  id: number
  community_id: number
  user_id: number
  org_id: number
  plan_id: number | null
  status: string
  joined_date: string
  creation_date: string
  update_date: string
}

export async function getMembershipPlans(
  community_uuid: string,
  access_token?: string
): Promise<MembershipPlan[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getAllMembershipPlansAdmin(
  community_uuid: string,
  access_token: string
): Promise<MembershipPlan[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/admin`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function createMembershipPlan(
  community_uuid: string,
  data: MembershipPlanCreate,
  access_token: string
): Promise<MembershipPlan> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans`,
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

export async function updateMembershipPlan(
  plan_uuid: string,
  data: MembershipPlanUpdate,
  access_token: string
): Promise<MembershipPlan> {
  const result: any = await fetch(
    `${getAPIUrl()}plans/${plan_uuid}`,
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

export async function deleteMembershipPlan(
  plan_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}plans/${plan_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getPlanBenefits(
  plan_uuid: string,
  access_token?: string
): Promise<MembershipBenefit[]> {
  const result: any = await fetch(
    `${getAPIUrl()}plans/${plan_uuid}/benefits`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function updatePlanBenefits(
  plan_uuid: string,
  benefits: MembershipBenefitData[],
  access_token: string
): Promise<MembershipBenefit[]> {
  const result: any = await fetch(
    `${getAPIUrl()}plans/${plan_uuid}/benefits`,
    RequestBodyWithAuthHeader('PUT', { benefits }, null, access_token)
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

export async function joinCommunity(
  community_uuid: string,
  plan_uuid: string | null,
  access_token: string
): Promise<CommunityMember> {
  const body: any = {}
  if (plan_uuid) body.plan_uuid = plan_uuid
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/join`,
    RequestBodyWithAuthHeader('POST', body, null, access_token)
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

export async function leaveCommunity(
  community_uuid: string,
  access_token: string
): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/leave`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getCommunityMembers(
  community_uuid: string,
  status?: string,
  access_token?: string
): Promise<CommunityMember[]> {
  let url = `${getAPIUrl()}communities/${community_uuid}/members`
  if (status) {
    url += `?status=${status}`
  }
  const result: any = await fetch(
    url,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function getUserMembership(
  community_uuid: string,
  access_token?: string
): Promise<CommunityMember | null> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/my-membership`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function duplicateMembershipPlan(
  plan_uuid: string,
  access_token: string
): Promise<MembershipPlan> {
  const result: any = await fetch(
    `${getAPIUrl()}plans/${plan_uuid}/duplicate`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
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

export async function reorderMembershipPlans(
  community_uuid: string,
  plan_uuids: string[],
  access_token: string
): Promise<MembershipPlan[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/reorder`,
    RequestBodyWithAuthHeader('PUT', { plan_uuids }, null, access_token)
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
