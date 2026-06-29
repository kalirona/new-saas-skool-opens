/** Frontend API service for AI course generation. */

import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader, errorHandling, getResponseMetadata } from '@services/utils/ts/requests'

export interface GeneratedQuizQuestion {
  question: string
  type: string
  answers: { answer_id: string; answer: string; correct: boolean }[]
}

export interface GeneratedQuiz {
  title: string
  questions: GeneratedQuizQuestion[]
}

export interface GeneratedLesson {
  title: string
  description: string
  estimated_minutes: number
}

export interface GeneratedModule {
  title: string
  description: string
  lessons: GeneratedLesson[]
}

export interface GeneratedCourse {
  title: string
  description: string
  learnings: string[]
  tags: string[]
  modules: GeneratedModule[]
}

export interface CourseStructureResponse {
  course: GeneratedCourse
  credits_used: number
}

export interface LessonContentResponse {
  content: Record<string, unknown>
  credits_used: number
}

export interface QuizResponse {
  quiz: GeneratedQuiz
  credits_used: number
}

/**
 * Generate a full course structure (modules, lessons, descriptions) from a topic.
 */
export async function generateCourseStructure(
  org_id: number,
  topic: string,
  language = 'en',
  access_token?: string
): Promise<CourseStructureResponse> {
  const result: any = await fetch(
    `${getAPIUrl()}ai/generation/course`,
    RequestBodyWithAuthHeader('POST', { org_id, topic, language }, null, access_token)
  )
  return await errorHandling(result)
}

/**
 * Generate ProseMirror lesson content for a single lesson.
 */
export async function generateLessonContent(
  org_id: number,
  params: {
    lesson_title: string
    lesson_description: string
    module_title: string
    course_title: string
    language?: string
    include_quiz?: boolean
  },
  access_token?: string
): Promise<LessonContentResponse> {
  const result: any = await fetch(
    `${getAPIUrl()}ai/generation/lesson-content`,
    RequestBodyWithAuthHeader('POST', { org_id, ...params }, null, access_token)
  )
  return await errorHandling(result)
}

/**
 * Generate a standalone quiz for a lesson.
 */
export async function generateQuiz(
  org_id: number,
  params: {
    lesson_title: string
    lesson_description: string
    module_title: string
    course_title: string
    language?: string
    num_questions?: number
  },
  access_token?: string
): Promise<QuizResponse> {
  const result: any = await fetch(
    `${getAPIUrl()}ai/generation/quiz`,
    RequestBodyWithAuthHeader('POST', { org_id, ...params }, null, access_token)
  )
  return await errorHandling(result)
}
