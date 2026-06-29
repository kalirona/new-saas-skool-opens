/**
 * Single source of truth for client-side per-feature metadata.
 *
 * Drives the FeatureGate component (locked/disabled views) and any UI that
 * needs the canonical icon + label + upsell plan for a feature. The gate's
 * actual `required_plan` still comes from the backend's resolved_features —
 * this file only owns presentation + the *upsell* plan we suggest in the UI
 * (which may differ from the gate's minimum requirement, e.g. Boards gates at
 * Personal but we upsell Free users to Standard).
 */

import { BookOpen, Presentation, BarChart3, ChartLine, MessageCircle, Box, CreditCard, Folder, Globe, Key, Zap, ListChecks, Mic, Bot, ShieldCheck, Users, ScrollText, GitForkHorizontal } from 'lucide-react'
import type { LucideProps } from 'lucide-react'
import type { ComponentType } from 'react'

import { PlanLevel } from '@services/plans/plans'

export type FeatureKey =
  | 'boards'
  | 'playgrounds'
  | 'communities'
  | 'podcasts'
  | 'ai'
  | 'analytics'
  | 'course_analytics'
  | 'payments'
  | 'usergroups'
  | 'custom_domains'
  | 'roles'
  | 'api_access'
  | 'webhooks'
  | 'certifications'
  | 'audit_logs'
  | 'sso'
  | 'scorm'
  | 'seo'
  // Features that are never plan-gated but can be admin-toggled off. Listed
  // here so FeatureGate can render the disabled card with the right icon.
  | 'courses'
  | 'folders'
  | 'trail'

export interface FeatureMeta {
  /** i18n key for the short title shown in the locked card (e.g. "Standard Feature"). */
  titleKey: string
  /** i18n key for the explanation paragraph. */
  descriptionKey: string
  /** Lucide icon component. */
  Icon: ComponentType<LucideProps>
  /**
   * Plan tier displayed in the upsell badge. Independent of the gate's actual
   * minimum requirement — used for marketing alignment (e.g. Boards gates at
   * Personal but we suggest Standard so the user lands on the tier the
   * pricing page presents as the "real" plan for those features).
   */
  upsellPlan: PlanLevel
}

export const FEATURE_METADATA: Record<FeatureKey, FeatureMeta> = {
  boards: {
    titleKey: 'common.plans.feature_restricted.boards.title',
    descriptionKey: 'common.plans.feature_restricted.boards.description',
    Icon: Presentation,
    upsellPlan: 'standard',
  },
  playgrounds: {
    titleKey: 'common.plans.feature_restricted.playgrounds.title',
    descriptionKey: 'common.plans.feature_restricted.playgrounds.description',
    Icon: Box,
    upsellPlan: 'standard',
  },
  communities: {
    titleKey: 'common.plans.feature_restricted.communities.title',
    descriptionKey: 'common.plans.feature_restricted.communities.description',
    Icon: MessageCircle,
    upsellPlan: 'standard',
  },
  podcasts: {
    titleKey: 'common.plans.feature_restricted.podcasts.title',
    descriptionKey: 'common.plans.feature_restricted.podcasts.description',
    Icon: Mic,
    upsellPlan: 'standard',
  },
  ai: {
    titleKey: 'common.plans.feature_restricted.ai.title',
    descriptionKey: 'common.plans.feature_restricted.ai.description',
    Icon: Bot,
    upsellPlan: 'standard',
  },
  analytics: {
    titleKey: 'common.plans.feature_restricted.analytics.title',
    descriptionKey: 'common.plans.feature_restricted.analytics.description',
    Icon: BarChart3,
    upsellPlan: 'standard',
  },
  course_analytics: {
    titleKey: 'common.plans.feature_restricted.course_analytics.title',
    descriptionKey: 'common.plans.feature_restricted.course_analytics.description',
    Icon: ChartLine,
    upsellPlan: 'pro',
  },
  payments: {
    titleKey: 'common.plans.feature_restricted.payments.title',
    descriptionKey: 'common.plans.feature_restricted.payments.description',
    Icon: CreditCard,
    upsellPlan: 'standard',
  },
  usergroups: {
    titleKey: 'common.plans.feature_restricted.usergroups.title',
    descriptionKey: 'common.plans.feature_restricted.usergroups.description',
    Icon: Users,
    upsellPlan: 'standard',
  },
  custom_domains: {
    titleKey: 'common.plans.feature_restricted.custom_domains.title',
    descriptionKey: 'common.plans.feature_restricted.custom_domains.description',
    Icon: Globe,
    upsellPlan: 'pro',
  },
  roles: {
    titleKey: 'common.plans.feature_restricted.roles.title',
    descriptionKey: 'common.plans.feature_restricted.roles.description',
    Icon: ShieldCheck,
    upsellPlan: 'pro',
  },
  api_access: {
    titleKey: 'common.plans.feature_restricted.api_access.title',
    descriptionKey: 'common.plans.feature_restricted.api_access.description',
    Icon: Key,
    upsellPlan: 'pro',
  },
  webhooks: {
    titleKey: 'common.plans.feature_restricted.webhooks.title',
    descriptionKey: 'common.plans.feature_restricted.webhooks.description',
    Icon: Zap,
    upsellPlan: 'pro',
  },
  certifications: {
    titleKey: 'common.plans.feature_restricted.certifications.title',
    descriptionKey: 'common.plans.feature_restricted.certifications.description',
    Icon: ScrollText,
    upsellPlan: 'pro',
  },
  audit_logs: {
    titleKey: 'common.plans.feature_restricted.audit_logs.title',
    descriptionKey: 'common.plans.feature_restricted.audit_logs.description',
    Icon: ListChecks,
    upsellPlan: 'enterprise',
  },
  sso: {
    titleKey: 'common.plans.feature_restricted.sso.title',
    descriptionKey: 'common.plans.feature_restricted.sso.description',
    Icon: Key,
    upsellPlan: 'enterprise',
  },
  scorm: {
    titleKey: 'common.plans.feature_restricted.scorm.title',
    descriptionKey: 'common.plans.feature_restricted.scorm.description',
    Icon: Box,
    upsellPlan: 'enterprise',
  },
  seo: {
    titleKey: 'common.plans.feature_restricted.seo.title',
    descriptionKey: 'common.plans.feature_restricted.seo.description',
    Icon: Globe,
    upsellPlan: 'standard',
  },
  // Non-plan-gated; upsellPlan kept at 'free' so the upgrade card never fires.
  // Only the admin-disabled state is reachable for these features.
  courses: {
    titleKey: 'common.features.disabled.names.courses',
    descriptionKey: 'common.features.disabled.public.description',
    Icon: BookOpen,
    upsellPlan: 'free',
  },
  folders: {
    titleKey: 'common.features.disabled.names.folders',
    descriptionKey: 'common.features.disabled.public.description',
    Icon: Folder,
    upsellPlan: 'free',
  },
  trail: {
    titleKey: 'common.features.disabled.names.trail',
    descriptionKey: 'common.features.disabled.public.description',
    Icon: GitForkHorizontal,
    upsellPlan: 'free',
  },
}

export function getFeatureMeta(feature: FeatureKey): FeatureMeta {
  return FEATURE_METADATA[feature]
}
