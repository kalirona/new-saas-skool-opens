import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededOnboarding {
  courseId: number
  courseUuid: string
}

export async function seedCourse(
  adminToken: string,
  org: Org,
  courseName: string,
): Promise<SeededOnboarding> {
  const course = await req<any>('POST', `/courses/?org_id=${org.id}`, adminToken, {
    name: courseName,
    description: 'Creator onboarding E2E course',
  })
  return { courseId: course.id, courseUuid: course.course_uuid }
}
