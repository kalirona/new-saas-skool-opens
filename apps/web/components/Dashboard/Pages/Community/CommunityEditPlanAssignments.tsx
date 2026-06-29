'use client'
import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useOrg } from '@components/Contexts/OrgContext'
import { useCommunity } from '@components/Contexts/CommunityContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader, errorHandling } from '@services/utils/ts/requests'
import { Loader2, BookOpen, Hash, FileType, Calendar, Plus, Trash2, Unlock, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import * as planService from '@services/communities/plan_assignments'

type ResourceTab = 'courses' | 'spaces' | 'resources' | 'events'

export function CommunityEditPlanAssignments() {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const org = useOrg() as any
  const communityState = useCommunity()
  const community = communityState?.community
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<ResourceTab>('courses')
  const [selectedPlanUuid, setSelectedPlanUuid] = useState<string | null>(null)

  const { data: plans = [], isLoading: plansLoading } = useQuery({
    queryKey: queryKeys.community.plans(community?.community_uuid ?? ''),
    queryFn: async () => {
      const result: any = await fetch(
        `${getAPIUrl()}communities/${community!.community_uuid}/plans`,
        RequestBodyWithAuthHeader('GET', null, null, accessToken)
      )
      return await errorHandling(result)
    },
    enabled: !!community?.community_uuid && !!accessToken,
    staleTime: 60_000,
  })

  useEffect(() => {
    if (plans.length > 0 && !selectedPlanUuid) {
      setSelectedPlanUuid(plans[0].plan_uuid)
    }
  }, [plans, selectedPlanUuid])

  if (!community) return null
  if (plansLoading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>

  return (
    <div className="sm:mx-10 mx-0">
      <div className="h-6"></div>
      <div className="bg-white rounded-xl nice-shadow">
        <div className="flex flex-col gap-0">
          <div className="flex flex-col bg-gray-50 -space-y-1 px-5 py-3 mx-3 my-3 rounded-md">
            <h1 className="font-bold text-xl text-gray-800">
              {t('dashboard.courses.communities.settings.plan_assignments.title') || 'Plan Assignments'}
            </h1>
            <h2 className="text-gray-500 text-md">
              {t('dashboard.courses.communities.settings.plan_assignments.subtitle') || 'Assign courses, spaces, resources, and events to membership plans'}
            </h2>
          </div>

          {plans.length === 0 ? (
            <div className="px-5 pb-5 text-sm text-gray-500">
              {t('dashboard.courses.communities.settings.plan_assignments.no_plans') || 'Create a membership plan first in the Plans tab.'}
            </div>
          ) : (
            <>
              <div className="flex gap-2 px-5 pb-4 flex-wrap">
                {plans.map((plan: any) => (
                  <button
                    key={plan.plan_uuid}
                    onClick={() => setSelectedPlanUuid(plan.plan_uuid)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedPlanUuid === plan.plan_uuid
                        ? 'bg-gray-900 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {plan.name}
                  </button>
                ))}
              </div>

              {selectedPlanUuid && (
                <>
                  <div className="flex border-b border-gray-200 px-5">
                    {([
                      { key: 'courses' as ResourceTab, icon: BookOpen, label: 'Courses' },
                      { key: 'spaces' as ResourceTab, icon: Hash, label: 'Spaces' },
                      { key: 'resources' as ResourceTab, icon: FileType, label: 'Resources' },
                      { key: 'events' as ResourceTab, icon: Calendar, label: 'Events' },
                    ]).map((tab) => {
                      const Icon = tab.icon
                      return (
                        <button
                          key={tab.key}
                          onClick={() => setActiveTab(tab.key)}
                          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === tab.key
                              ? 'border-gray-900 text-gray-900'
                              : 'border-transparent text-gray-500 hover:text-gray-700'
                          }`}
                        >
                          <Icon size={16} />
                          {tab.label}
                        </button>
                      )
                    })}
                  </div>

                  <div className="p-5">
                    {activeTab === 'courses' && (
                      <ResourceAssignment
                        communityUuid={community.community_uuid}
                        planUuid={selectedPlanUuid}
                        resourceType="courses"
                        fetchAssigned={planService.getPlanCourses}
                        assign={planService.assignCourseToPlan}
                        remove={planService.removeCourseFromPlan}
                        accessToken={accessToken}
                        orgId={org?.id}
                      />
                    )}
                    {activeTab === 'spaces' && (
                      <ResourceAssignment
                        communityUuid={community.community_uuid}
                        planUuid={selectedPlanUuid}
                        resourceType="spaces"
                        fetchAssigned={planService.getPlanSpaces}
                        assign={planService.assignSpaceToPlan}
                        remove={planService.removeSpaceFromPlan}
                        communityFilter={community.community_uuid}
                        accessToken={accessToken}
                        orgId={org?.id}
                      />
                    )}
                    {activeTab === 'resources' && (
                      <ResourceAssignment
                        communityUuid={community.community_uuid}
                        planUuid={selectedPlanUuid}
                        resourceType="resources"
                        fetchAssigned={planService.getPlanResources}
                        assign={planService.assignResourceToPlan}
                        remove={planService.removeResourceFromPlan}
                        accessToken={accessToken}
                        orgId={org?.id}
                      />
                    )}
                    {activeTab === 'events' && (
                      <ResourceAssignment
                        communityUuid={community.community_uuid}
                        planUuid={selectedPlanUuid}
                        resourceType="events"
                        fetchAssigned={planService.getPlanEvents}
                        assign={planService.assignEventToPlan}
                        remove={planService.removeEventFromPlan}
                        accessToken={accessToken}
                        orgId={org?.id}
                      />
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface ResourceAssignmentProps {
  communityUuid: string
  planUuid: string
  resourceType: string
  fetchAssigned: (cu: string, pu: string, at?: string) => Promise<any[]>
  assign: (cu: string, pu: string, ru: string, at: string) => Promise<any>
  remove: (cu: string, pu: string, ru: string, at: string) => Promise<void>
  communityFilter?: string
  accessToken?: string
  orgId?: number | string
}

function ResourceAssignment({
  communityUuid,
  planUuid,
  resourceType,
  fetchAssigned,
  assign,
  remove,
  communityFilter,
  accessToken,
  orgId,
}: ResourceAssignmentProps) {
  const { t } = useTranslation()
  const [assignedIds, setAssignedIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(false)

  const { data: assigned = [], isLoading: assignedLoading } = useQuery({
    queryKey: ['plan', planUuid, resourceType, 'assigned'],
    queryFn: () => fetchAssigned(communityUuid, planUuid, accessToken),
    enabled: !!planUuid && !!accessToken,
    staleTime: 30_000,
  })

  useEffect(() => {
    if (assigned.length > 0) {
      setAssignedIds(new Set(assigned.map((a: any) => a.resource_id || a.course_id || a.space_id || a.event_id)))
    }
  }, [assigned])

  const handleToggle = async (resourceUuid: string, resourceId: number) => {
    setLoading(true)
    try {
      if (assignedIds.has(resourceId)) {
        await remove(communityUuid, planUuid, resourceUuid, accessToken!)
        setAssignedIds((prev) => { const n = new Set(prev); n.delete(resourceId); return n })
        toast.success('Removed')
      } else {
        await assign(communityUuid, planUuid, resourceUuid, accessToken!)
        setAssignedIds((prev) => new Set(prev).add(resourceId))
        toast.success('Assigned')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update')
    } finally {
      setLoading(false)
    }
  }

  if (assignedLoading) return <div className="flex justify-center p-6"><Loader2 className="animate-spin" /></div>

  return (
    <div className="text-sm text-gray-500">
      {t('dashboard.courses.communities.settings.plan_assignments.select_hint') || 'Select which resources this plan grants access to:'}
      <div className="mt-4 space-y-2">
        <AssignedResourceList
          resourceType={resourceType}
          assignedIds={assignedIds}
          onToggle={handleToggle}
          loading={loading}
          orgId={orgId}
          accessToken={accessToken}
        />
      </div>
    </div>
  )
}

function AssignedResourceList({
  resourceType,
  assignedIds,
  onToggle,
  loading,
  orgId,
  accessToken,
}: {
  resourceType: string
  assignedIds: Set<number>
  onToggle: (uuid: string, id: number) => Promise<void>
  loading: boolean
  orgId?: number | string
  accessToken?: string
}) {
  const { data: items = [], isLoading } = useQuery({
    queryKey: ['all', resourceType, orgId],
    queryFn: async () => {
      let url = ''
      if (resourceType === 'courses') url = `${getAPIUrl()}courses/org_slug/${orgId}/page/1/limit/100`
      else if (resourceType === 'spaces') url = `${getAPIUrl()}spaces/org/${orgId}`
      else if (resourceType === 'resources') url = `${getAPIUrl()}resources/org/${orgId}`
      else if (resourceType === 'events') url = `${getAPIUrl()}events/org/${orgId}`
      const result: any = await fetch(url, RequestBodyWithAuthHeader('GET', null, null, accessToken))
      return await errorHandling(result)
    },
    enabled: !!orgId && !!accessToken,
    staleTime: 60_000,
  })

  if (isLoading) return <div className="flex justify-center p-4"><Loader2 className="animate-spin" size={16} /></div>
  if (items.length === 0) return <div className="text-gray-400 italic">No {resourceType} found</div>

  return (
    <div className="max-h-80 overflow-y-auto space-y-1">
      {items.map((item: any) => {
        const id = item.id
        const isAssigned = assignedIds.has(id)
        const name = item.name || item.title || `Item #${id}`
        const uuid = item.course_uuid || item.space_uuid || item.resource_uuid || item.event_uuid
        return (
          <div
            key={id}
            className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-colors ${
              isAssigned ? 'border-indigo-200 bg-indigo-50' : 'border-gray-100 hover:border-gray-200'
            }`}
          >
            <div className="flex items-center gap-2">
              {isAssigned ? <Lock size={14} className="text-indigo-500" /> : <Unlock size={14} className="text-gray-400" />}
              <span className={`text-sm ${isAssigned ? 'text-indigo-700 font-medium' : 'text-gray-700'}`}>{name}</span>
            </div>
            <button
              onClick={() => onToggle(uuid, id)}
              disabled={loading}
              className={`text-xs px-3 py-1 rounded-md font-medium transition-colors ${
                isAssigned
                  ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              {isAssigned ? 'Remove' : 'Assign'}
            </button>
          </div>
        )
      })}
    </div>
  )
}

export default CommunityEditPlanAssignments
