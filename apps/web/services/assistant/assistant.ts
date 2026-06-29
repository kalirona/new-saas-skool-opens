/** Frontend API service for the AI assistant. */

import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader, errorHandling } from '@services/utils/ts/requests'

export type AssistantCapability = 'qa' | 'summarize' | 'generate' | 'moderate'

/* ── Q&A ──────────────────────────────────────────────────────────────── */

export interface QARequest {
  question: string
  discussion_context?: string | null
  course_context?: string | null
  max_sources?: number
}

export interface QAResponse {
  answer: string
  sources: string[]
  confidence: 'high' | 'medium' | 'low'
}

/* ── Summarize ───────────────────────────────────────────────────────── */

export type SummaryType = 'thread' | 'discussion' | 'post'

export interface SummarizeRequest {
  content: string
  summary_type?: SummaryType
  max_length?: number
  include_key_points?: boolean
}

export interface SummarizeResponse {
  summary: string
  key_points: string[]
  word_count: number
}

/* ── Generate ─────────────────────────────────────────────────────────── */

export type ContentTone = 'professional' | 'casual' | 'encouraging' | 'neutral'
export type ContentTypeName = 'post' | 'reply' | 'announcement' | 'discussion_prompt'

export interface GenerateRequest {
  content_type: ContentTypeName
  topic: string
  tone?: ContentTone
  context?: string | null
  max_length?: number
}

export interface GenerateResponse {
  content: string
  title_suggestion?: string | null
  word_count: number
}

/* ── Moderate ─────────────────────────────────────────────────────────── */

export type ModerationCategory =
  | 'toxicity'
  | 'spam'
  | 'harassment'
  | 'hate_speech'
  | 'nsfw'
  | 'self_harm'
  | 'violence'

export interface ModerateRequest {
  content: string
  categories?: ModerationCategory[]
}

export interface ModerationResult {
  category: ModerationCategory
  flagged: boolean
  score: number
  explanation?: string | null
}

export interface ModerateResponse {
  is_flagged: boolean
  results: ModerationResult[]
  summary?: string | null
}

/* ── Top-level wrapper ────────────────────────────────────────────────── */

export interface AssistantRequest {
  capability: AssistantCapability
  org_id: number
  language?: string
  qa?: QARequest | null
  summarize?: SummarizeRequest | null
  generate?: GenerateRequest | null
  moderate?: ModerateRequest | null
}

export interface AssistantResponse {
  capability: AssistantCapability
  qa?: QAResponse | null
  summarize?: SummarizeResponse | null
  generate?: GenerateResponse | null
  moderate?: ModerateResponse | null
  credits_used: number
}

/**
 * Run an AI assistant capability.
 */
export async function runAssistant(
  req: AssistantRequest,
  access_token?: string
): Promise<AssistantResponse> {
  const result: any = await fetch(
    `${getAPIUrl()}ai/assistant/run`,
    RequestBodyWithAuthHeader('POST', req, null, access_token)
  )
  return await errorHandling(result)
}
