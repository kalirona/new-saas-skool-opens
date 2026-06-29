'use client'
import { Users, BookOpen, MessageCircle, Folder, Calendar, Activity, Plus, ArrowUpRight, Sparkles, UserPlus, Clock } from 'lucide-react'
import React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { useTranslation } from 'react-i18next'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useOrg } from '@components/Contexts/OrgContext'
import { getAPIUrl } from '@services/config/config'
import { apiFetch } from '@services/utils/ts/requests'
import { usePlan } from '@components/Hooks/usePlan'
import { getOrgCourses } from '@services/courses/courses'
import { getCommunities } from '@services/communities/communities'
import { getUpcomingEvents } from '@services/events/events'
import { useDashboardOverview } from '@components/Dashboard/Analytics/useDashboardOverview'

const PLAN_COLORS: Record<string, { bg: string; text: string }> = {
  free: { bg: 'bg-gray-100', text: 'text-gray-600' },
  oss: { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  standard: { bg: 'bg-blue-100', text: 'text-blue-700' },
  pro: { bg: 'bg-purple-100', text: 'text-purple-700' },
  enterprise: { bg: 'bg-amber-100', text: 'text-amber-700' },
}

interface StatCardProps {
  icon: React.ComponentType<any>
  label: string
  value: number
  href: string
  isLoading: boolean
  iconColor: string
  iconBg: string
}

function StatCard({ icon: Icon, label, value, href, isLoading, iconColor, iconBg }: StatCardProps) {
  return (
    <Link
      href={href}
      className="bg-white rounded-xl nice-shadow px-5 py-4 hover:bg-gray-50 transition-colors group"
    >
      {isLoading ? (
        <div className="animate-pulse">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 bg-gray-100 rounded-lg" />
            <div className="h-2.5 bg-gray-100 rounded w-16" />
          </div>
          <div className="h-7 bg-gray-100 rounded w-10 mb-1.5" />
          <div className="h-2 bg-gray-50 rounded w-20" />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-2">
            <div className={`p-1.5 rounded-lg ${iconBg}`}>
              <Icon size={14} className={iconColor} />
            </div>
            <span className="text-xs font-medium text-gray-400">{label}</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {value.toLocaleString()}
          </div>
          <p className="text-[11px] text-gray-300 mt-0.5 flex items-center gap-1">
            <ArrowUpRight size={11} />
            {value === 0 ? 'No data yet' : 'Total count'}
          </p>
        </>
      )}
    </Link>
  )
}

function QuickActionCard({
  icon: Icon,
  title,
  description,
  href,
  iconColor,
  iconBg,
}: {
  icon: React.ComponentType<any>
  title: string
  description: string
  href: string
  iconColor: string
  iconBg: string
}) {
  return (
    <Link
      href={href}
      className="bg-white rounded-xl nice-shadow p-5 hover:bg-gray-50 transition-colors group flex flex-col gap-3"
    >
      <div className={`p-2.5 rounded-xl ${iconBg} w-fit`}>
        <Icon size={22} className={iconColor} />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-gray-700 group-hover:text-gray-900 transition-colors">
          {title}
        </h4>
        <p className="text-xs text-gray-400 mt-1">{description}</p>
      </div>
      <div className="flex items-center gap-1 text-xs font-medium text-gray-400 group-hover:text-gray-600 transition-colors mt-auto">
        <Plus size={12} />
        <span>Create</span>
      </div>
    </Link>
  )
}

export default function CreatorDashboardHome() {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const org = useOrg() as any

  const token = session?.data?.tokens?.access_token
  const orgId = org?.id
  const orgSlug = org?.slug
  const username = session?.data?.user?.username || ''

  const plan = usePlan()
  const planStyle = PLAN_COLORS[plan] || PLAN_COLORS.free

  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: [...queryKeys.org.users(orgId), 'creator-dash-count'],
    queryFn: () => apiFetch(`${getAPIUrl()}orgs/${orgId}/users?page=1&limit=1`, token),
    enabled: !!token && !!orgId,
    staleTime: 60_000,
  })

  const { data: overviewData, isLoading: overviewLoading } = useDashboardOverview()

  const { data: coursesData, isLoading: coursesLoading } = useQuery({
    queryKey: [...queryKeys.courses.list(orgSlug), 'creator-dash-count'],
    queryFn: () => getOrgCourses(orgSlug, null, token, true),
    enabled: !!token && !!orgSlug,
    staleTime: 60_000,
  })

  const { data: communitiesData, isLoading: communitiesLoading } = useQuery({
    queryKey: [...queryKeys.community.list(orgId), 'creator-dash-count'],
    queryFn: () => getCommunities(orgId, 1, 1, null, token),
    enabled: !!token && !!orgId,
    staleTime: 60_000,
  })

  const { data: resourcesData, isLoading: resourcesLoading } = useQuery({
    queryKey: [...queryKeys.resources.list(orgId), 'creator-dash-count'],
    queryFn: () => apiFetch(`${getAPIUrl()}resources/org/${orgId}?page=1&limit=1`, token),
    enabled: !!token && !!orgId,
    staleTime: 60_000,
  })

  const { data: eventsData, isLoading: eventsLoading } = useQuery({
    queryKey: [...queryKeys.events.upcoming(orgId), 'creator-dash-count'],
    queryFn: () => getUpcomingEvents(orgId, 1, token),
    enabled: !!token && !!orgId,
    staleTime: 60_000,
  })

  const { data: recentMembers, isLoading: recentMembersLoading } = useQuery({
    queryKey: [...queryKeys.org.users(orgId), 'creator-dash-recent'],
    queryFn: () => apiFetch(`${getAPIUrl()}orgs/${orgId}/users?page=1&limit=5&sort_order=desc`, token),
    enabled: !!token && !!orgId,
    staleTime: 60_000,
  })

  const totalMembers = membersData?.total ?? 0
  const activeMembers = overviewData?.active_members?.total ?? 0
  const courses: any[] = coursesData ?? []
  const communities: any[] = communitiesData ?? []
  const resourcesTotal = resourcesData?.total ?? 0
  const events: any[] = eventsData ?? []
  const recentMembersList: any[] = recentMembers?.items ?? []
  const discussionActivity = overviewData?.discussion_activity
  const courseCompletions = overviewData?.course_completions

  const statsCards = [
    {
      icon: Users,
      label: 'Total Members',
      value: totalMembers,
      href: '/dash/users/settings/users',
      isLoading: membersLoading,
      iconColor: 'text-indigo-500',
      iconBg: 'bg-indigo-50',
    },
    {
      icon: Activity,
      label: 'Active Members',
      value: activeMembers,
      href: '/dash/analytics',
      isLoading: overviewLoading,
      iconColor: 'text-green-500',
      iconBg: 'bg-green-50',
    },
    {
      icon: MessageCircle,
      label: 'Communities',
      value: communities.length,
      href: '/dash/communities',
      isLoading: communitiesLoading,
      iconColor: 'text-violet-500',
      iconBg: 'bg-violet-50',
    },
    {
      icon: BookOpen,
      label: 'Courses',
      value: courses.length,
      href: '/dash/courses',
      isLoading: coursesLoading,
      iconColor: 'text-blue-500',
      iconBg: 'bg-blue-50',
    },
    {
      icon: Folder,
      label: 'Resources',
      value: resourcesTotal,
      href: '/dash/resources',
      isLoading: resourcesLoading,
      iconColor: 'text-amber-500',
      iconBg: 'bg-amber-50',
    },
    {
      icon: Calendar,
      label: 'Events',
      value: events.length,
      href: '/dash/calendar',
      isLoading: eventsLoading,
      iconColor: 'text-rose-500',
      iconBg: 'bg-rose-50',
    },
  ]

  const quickActions = [
    {
      icon: MessageCircle,
      title: 'Create Community',
      description: 'Build a space for your members to connect and discuss',
      href: '/dash/communities?new=true',
      iconColor: 'text-violet-500',
      iconBg: 'bg-violet-50',
    },
    {
      icon: BookOpen,
      title: 'Create Course',
      description: 'Design and publish a new learning experience',
      href: '/dash/courses?new=true',
      iconColor: 'text-blue-500',
      iconBg: 'bg-blue-50',
    },
    {
      icon: Folder,
      title: 'Upload Resource',
      description: 'Share files, links, and learning materials',
      href: '/dash/resources?new=true',
      iconColor: 'text-amber-500',
      iconBg: 'bg-amber-50',
    },
    {
      icon: Calendar,
      title: 'Create Event',
      description: 'Schedule a live session, webinar, or meetup',
      href: '/dash/calendar?new=true',
      iconColor: 'text-rose-500',
      iconBg: 'bg-rose-50',
    },
  ]

  return (
    <div className="h-full w-full bg-background">
      <div className="px-4 sm:px-10 pt-8 pb-10">
        <div className="space-y-6 max-w-[1600px] mx-auto w-full">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {t('dashboard.home.welcome_back')}{username ? `, ${username}` : ''}
              </h1>
              <div className="flex items-center gap-2 mt-1.5">
                <span
                  className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full capitalize ${planStyle.bg} ${planStyle.text}`}
                >
                  {plan === 'oss' ? 'OSS' : `${plan} ${t('dashboard.home.plan')}`}
                </span>
                {org?.name && (
                  <span className="text-xs text-gray-400">{org.name}</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                href="/dash/analytics"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
              >
                <Sparkles size={14} />
                Analytics
              </Link>
            </div>
          </div>

          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
            {statsCards.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white rounded-xl nice-shadow overflow-hidden">
                <div className="flex items-center justify-between px-5 pt-4 pb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold text-gray-700">
                      Recent Activity
                    </h3>
                  </div>
                </div>
                <div className="divide-y divide-gray-50">
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <UserPlus size={14} className="text-indigo-500" />
                      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">New Members</h4>
                    </div>
                    {recentMembersLoading ? (
                      <div className="space-y-2">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="flex items-center gap-3 animate-pulse">
                            <div className="w-7 h-7 bg-gray-100 rounded-full shrink-0" />
                            <div className="flex-1">
                              <div className="h-2.5 bg-gray-100 rounded w-28 mb-1" />
                              <div className="h-2 bg-gray-50 rounded w-36" />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : recentMembersList.length === 0 ? (
                      <p className="text-xs text-gray-400 py-2 text-center">No members yet</p>
                    ) : (
                      <div className="space-y-2">
                        {recentMembersList.slice(0, 3).map((member: any) => {
                          const user = member.user
                          const displayName = user.first_name || user.last_name
                            ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                            : user.username
                          return (
                            <div key={user.user_uuid} className="flex items-center gap-3">
                              <div className="w-7 h-7 rounded-full bg-indigo-100 shrink-0 flex items-center justify-center">
                                <span className="text-[10px] font-semibold text-indigo-600">
                                  {(user.first_name?.[0] || user.username?.[0] || '').toUpperCase()}
                                </span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-700 truncate">{displayName}</p>
                                <p className="text-[10px] text-gray-400 truncate">{user.email}</p>
                              </div>
                              {member.joined_at && (
                                <span className="text-[10px] text-gray-400 shrink-0">
                                  <Clock size={10} className="inline mr-1" />
                                  {new Date(member.joined_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <MessageCircle size={14} className="text-violet-500" />
                      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Discussions</h4>
                    </div>
                    {overviewLoading ? (
                      <div className="space-y-2">
                        {[1, 2].map((i) => (
                          <div key={i} className="flex items-center gap-3 animate-pulse">
                            <div className="w-7 h-7 bg-gray-100 rounded-full shrink-0" />
                            <div className="flex-1">
                              <div className="h-2.5 bg-gray-100 rounded w-32 mb-1" />
                              <div className="h-2 bg-gray-50 rounded w-20" />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : discussionActivity ? (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between py-1">
                          <span className="text-xs text-gray-500">Total discussions</span>
                          <span className="text-sm font-semibold text-gray-900">{discussionActivity.total_discussions.toLocaleString()}</span>
                        </div>
                        <div className="flex items-center justify-between py-1">
                          <span className="text-xs text-gray-500">Total comments</span>
                          <span className="text-sm font-semibold text-gray-900">{discussionActivity.total_comments.toLocaleString()}</span>
                        </div>
                        <div className="flex items-center justify-between py-1">
                          <span className="text-xs text-gray-500">This month</span>
                          <span className="text-sm font-semibold text-gray-900">{discussionActivity.this_month_discussions.toLocaleString()}</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 py-2 text-center">No discussion data available</p>
                    )}
                  </div>

                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <BookOpen size={14} className="text-blue-500" />
                      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Course Enrollments</h4>
                    </div>
                    {overviewLoading ? (
                      <div className="space-y-2">
                        <div className="h-3 bg-gray-100 rounded w-24 animate-pulse" />
                        <div className="h-3 bg-gray-100 rounded w-32 animate-pulse" />
                      </div>
                    ) : courseCompletions ? (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between py-1">
                          <span className="text-xs text-gray-500">Total completions</span>
                          <span className="text-sm font-semibold text-gray-900">{courseCompletions.total.toLocaleString()}</span>
                        </div>
                        <div className="flex items-center justify-between py-1">
                          <span className="text-xs text-gray-500">This month</span>
                          <span className="text-sm font-semibold text-gray-900">{courseCompletions.this_month.toLocaleString()}</span>
                        </div>
                        {courseCompletions.growth_percent !== 0 && (
                          <div className="flex items-center justify-between py-1">
                            <span className="text-xs text-gray-500">Growth</span>
                            <span className={`text-sm font-semibold ${courseCompletions.growth_percent > 0 ? 'text-green-600' : 'text-red-500'}`}>
                              {courseCompletions.growth_percent > 0 ? '+' : ''}{courseCompletions.growth_percent}%
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 py-2 text-center">No enrollment data available</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <Sparkles size={14} className="text-gray-400" />
                  Quick Actions
                </h3>
                <div className="grid grid-cols-1 gap-3">
                  {quickActions.map((action) => (
                    <QuickActionCard key={action.title} {...action} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
