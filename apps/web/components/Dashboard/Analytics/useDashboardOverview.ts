'use client'
import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { getAPIUrl } from '@services/config/config'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useOrg } from '@components/Contexts/OrgContext'

export interface MonthlyDataPoint {
  month: string
  count: number
}

export interface MetricSummary {
  total: number
  this_month: number
  growth_percent: number
}

export interface DiscussionActivity {
  total_discussions: number
  total_comments: number
  this_month_discussions: number
  this_month_comments: number
  growth_percent_discussions: number
  growth_percent_comments: number
}

export interface GrowthCharts {
  members: MonthlyDataPoint[]
  completions: MonthlyDataPoint[]
  discussions: MonthlyDataPoint[]
  comments: MonthlyDataPoint[]
  resources: MonthlyDataPoint[]
}

export interface DashboardOverview {
  org_id: number
  active_members: MetricSummary
  course_completions: MetricSummary
  discussion_activity: DiscussionActivity
  resources: MetricSummary
  growth_charts: GrowthCharts
}

export function useDashboardOverview() {
  const org = useOrg() as any
  const session = useLHSession() as any
  const token = session?.data?.tokens?.access_token
  const orgId = org?.id

  return useQuery({
    queryKey: queryKeys.analytics.overview(orgId ?? 0),
    queryFn: async (): Promise<DashboardOverview> => {
      const res = await fetch(
        `${getAPIUrl()}analytics/dashboard/overview?org_id=${orgId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error(`${res.status}`)
      return res.json()
    },
    enabled: !!(orgId && token),
    staleTime: 60_000,
  })
}
