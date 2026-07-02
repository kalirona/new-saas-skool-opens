import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededAICourse {
  courseId: number
  courseUuid: string
}

export async function seedCourse(
  adminToken: string,
  org: Org,
  name: string,
): Promise<SeededAICourse> {
  const course = await req<any>('POST', `/courses/?org_id=${org.id}`, adminToken, {
    name,
    description: 'E2E AI course generation',
  })
  return { courseId: course.id, courseUuid: course.course_uuid }
}
