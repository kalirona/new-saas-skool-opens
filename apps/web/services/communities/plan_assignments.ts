import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader, errorHandling, getResponseMetadata } from '@services/utils/ts/requests'

export interface PlanAssignment {
  id: number
  plan_id: number
  resource_id: number
  creation_date: string
  update_date: string
}

export async function getPlanCourses(community_uuid: string, plan_uuid: string, access_token?: string): Promise<PlanAssignment[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/courses`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function assignCourseToPlan(community_uuid: string, plan_uuid: string, course_uuid: string, access_token: string): Promise<PlanAssignment> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/courses/${course_uuid}`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) throw new Error(res.data?.detail || 'Failed to assign course')
  return res.data
}

export async function removeCourseFromPlan(community_uuid: string, plan_uuid: string, course_uuid: string, access_token: string): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/courses/${course_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  await errorHandling(result)
}

export async function getPlanSpaces(community_uuid: string, plan_uuid: string, access_token?: string): Promise<PlanAssignment[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/spaces`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function assignSpaceToPlan(community_uuid: string, plan_uuid: string, space_uuid: string, access_token: string): Promise<PlanAssignment> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/spaces/${space_uuid}`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) throw new Error(res.data?.detail || 'Failed to assign space')
  return res.data
}

export async function removeSpaceFromPlan(community_uuid: string, plan_uuid: string, space_uuid: string, access_token: string): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/spaces/${space_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  await errorHandling(result)
}

export async function getPlanResources(community_uuid: string, plan_uuid: string, access_token?: string): Promise<PlanAssignment[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/resources`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function assignResourceToPlan(community_uuid: string, plan_uuid: string, resource_uuid: string, access_token: string): Promise<PlanAssignment> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/resources/${resource_uuid}`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) throw new Error(res.data?.detail || 'Failed to assign resource')
  return res.data
}

export async function removeResourceFromPlan(community_uuid: string, plan_uuid: string, resource_uuid: string, access_token: string): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/resources/${resource_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  await errorHandling(result)
}

export async function getPlanEvents(community_uuid: string, plan_uuid: string, access_token?: string): Promise<PlanAssignment[]> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/events`,
    RequestBodyWithAuthHeader('GET', null, null, access_token)
  )
  const res = await errorHandling(result)
  return res
}

export async function assignEventToPlan(community_uuid: string, plan_uuid: string, event_uuid: string, access_token: string): Promise<PlanAssignment> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/events/${event_uuid}`,
    RequestBodyWithAuthHeader('POST', null, null, access_token)
  )
  const res = await getResponseMetadata(result)
  if (!res.success) throw new Error(res.data?.detail || 'Failed to assign event')
  return res.data
}

export async function removeEventFromPlan(community_uuid: string, plan_uuid: string, event_uuid: string, access_token: string): Promise<void> {
  const result: any = await fetch(
    `${getAPIUrl()}communities/${community_uuid}/plans/${plan_uuid}/events/${event_uuid}`,
    RequestBodyWithAuthHeader('DELETE', null, null, access_token)
  )
  await errorHandling(result)
}
