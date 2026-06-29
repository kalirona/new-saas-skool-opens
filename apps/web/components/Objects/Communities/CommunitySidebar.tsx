'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { useTranslation } from 'react-i18next'
import {
  MessageCircle,
  Plus,
  Globe,
  Lock,
  Settings,
  Calendar,
  BookOpen,
  ChevronRight,
  LogIn,
  LogOut,
  Loader2,
  Hash,
  CreditCard,
  EyeOff,
} from 'lucide-react'
import { Community } from '@services/communities/communities'
import { getCommunityThumbnailMediaDirectory, getCourseThumbnailMediaDirectory } from '@services/media/media'
import { useCommunityRights } from '@components/Hooks/useCommunityRights'
import { useOrg } from '@components/Contexts/OrgContext'
import { getUriWithOrg } from '@services/config/config'
import { getCourseById } from '@services/courses/courses'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import dayjs from 'dayjs'
import { SafeImage } from '@components/Objects/SafeImage'
import { joinCommunity, leaveCommunity } from '@services/communities/membership'
import toast from 'react-hot-toast'
import Modal from '@components/Objects/StyledElements/Modal/Modal'
import { getSpaces, Space } from '@services/communities/spaces'
import ManageSpacesModal from '@components/Objects/Modals/Communities/ManageSpacesModal'

interface CommunitySidebarProps {
  community: Community
  discussionCount: number
  orgslug: string
  onCreateDiscussion?: () => void
  spaceDiscussionCounts?: Record<number, number>
}

export function CommunitySidebar({
  community,
  discussionCount,
  orgslug,
  onCreateDiscussion,
  spaceDiscussionCounts,
}: CommunitySidebarProps) {
  const { t } = useTranslation()
  const { canManageCommunity, canCreateDiscussion, hasPlans, availablePlans, isMember } = useCommunityRights(community.community_uuid)
  const org = useOrg() as any
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()
  const [joinModalOpen, setJoinModalOpen] = useState(false)
  const [joining, setJoining] = useState(false)
  const [leaving, setLeaving] = useState(false)

  const handleJoin = async (planUuid: string | null) => {
    setJoining(true)
    try {
      await joinCommunity(community.community_uuid, planUuid, accessToken)
      toast.success(t('communities.join_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.community.rights(community.community_uuid) })
      setJoinModalOpen(false)
    } catch (err: any) {
      toast.error(err.message || t('communities.join_error'))
    } finally {
      setJoining(false)
    }
  }

  const handleLeave = async () => {
    setLeaving(true)
    try {
      await leaveCommunity(community.community_uuid, accessToken)
      toast.success(t('communities.leave_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.community.rights(community.community_uuid) })
    } catch (err: any) {
      toast.error(err.message || t('communities.leave_error'))
    } finally {
      setLeaving(false)
    }
  }

  // Fetch linked course if community has a course_id
  const { data: linkedCourse } = useQuery({
    queryKey: queryKeys.community.byCourse(String(community.course_id ?? '')),
    queryFn: () => getCourseById(String(community.course_id), null, accessToken),
    enabled: !!(community.course_id && accessToken),
    staleTime: 60_000,
  })

  const createdDate = dayjs(community.creation_date).format('MMM D, YYYY')

  const thumbnailUrl = community.thumbnail_image && org?.org_uuid
    ? getCommunityThumbnailMediaDirectory(
        org.org_uuid,
        community.community_uuid,
        community.thumbnail_image
      )
    : null

  const courseThumbnailUrl = linkedCourse?.thumbnail_image && org?.org_uuid
    ? getCourseThumbnailMediaDirectory(
        org.org_uuid,
        linkedCourse.course_uuid,
        linkedCourse.thumbnail_image
      )
    : null

  return (
    <div className="space-y-4">
      {/* Community Info Card */}
      <div className="bg-white nice-shadow rounded-lg overflow-hidden">
        {/* Header with community name */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            {thumbnailUrl ? (
              <SafeImage
                src={thumbnailUrl}
                alt={community.name}
                className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
              />
            ) : (
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                <MessageCircle className="w-5 h-5 text-gray-400" />
              </div>
            )}
            <div className="min-w-0">
              <h2 className="font-semibold text-gray-900 truncate">{community.name}</h2>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                {community.community_type === 'open' && (
                  <>
                    <Globe size={12} className="text-green-500" />
                    <span>{t('communities.public')}</span>
                  </>
                )}
                {community.community_type === 'paid' && (
                  <>
                    <CreditCard size={12} className="text-indigo-500" />
                    <span>{t('communities.paid') || 'Paid'}</span>
                  </>
                )}
                {community.community_type === 'invite_only' && (
                  <>
                    <Lock size={12} className="text-amber-500" />
                    <span>{t('communities.invite_only') || 'Invite Only'}</span>
                  </>
                )}
                {community.community_type === 'hidden' && (
                  <>
                    <EyeOff size={12} className="text-gray-400" />
                    <span>{t('communities.hidden') || 'Hidden'}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        {community.description && (
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-sm text-gray-600 leading-relaxed">
              {community.description}
            </p>
          </div>
        )}

        {/* Stats */}
        <div className="px-4 py-3 space-y-2">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <MessageCircle size={14} className="text-gray-400" />
            <span>{discussionCount} {discussionCount === 1 ? t('communities.discussion') : t('communities.discussions')}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar size={14} className="text-gray-400" />
            <span>{t('communities.created')} {createdDate}</span>
          </div>
        </div>

        {/* Linked Course */}
        {linkedCourse && (
          <div className="px-4 py-3 border-t border-gray-100">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              {t('communities.linked_course')}
            </div>
            <Link
              href={getUriWithOrg(orgslug, `/course/${linkedCourse.course_uuid.replace('course_', '')}`)}
              className="group block"
            >
              <div className="flex items-center gap-3 p-2 -mx-2 rounded-lg hover:bg-gray-50 transition-colors">
                {courseThumbnailUrl ? (
                  <SafeImage
                    src={courseThumbnailUrl}
                    alt={linkedCourse.name}
                    className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                    <BookOpen size={20} className="text-gray-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors truncate">
                    {linkedCourse.name}
                  </h4>
                  {linkedCourse.description && (
                    <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">
                      {linkedCourse.description}
                    </p>
                  )}
                </div>
                <ChevronRight size={16} className="text-gray-400 group-hover:text-indigo-600 transition-colors flex-shrink-0" />
              </div>
            </Link>
          </div>
        )}

        {/* Spaces */}
        <SpacesSection
          communityUuid={community.community_uuid}
          accessToken={accessToken}
          orgslug={orgslug}
          spaceDiscussionCounts={spaceDiscussionCounts}
          canManageCommunity={canManageCommunity}
        />

        {/* Actions */}
        <div className="p-4 border-t border-gray-100 space-y-2">
          {canCreateDiscussion && onCreateDiscussion && (
            <button
              onClick={onCreateDiscussion}
              className="w-full py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer bg-neutral-900 text-white hover:bg-neutral-800 text-sm"
            >
              <Plus className="w-4 h-4" />
              <span>{t('communities.new_discussion')}</span>
            </button>
          )}

          {!canManageCommunity && !isMember && (
            hasPlans ? (
              <button
                onClick={() => setJoinModalOpen(true)}
                disabled={joining}
                className="w-full py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer bg-indigo-600 text-white hover:bg-indigo-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {joining ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <LogIn className="w-4 h-4" />
                )}
                <span>{t('communities.join')}</span>
              </button>
            ) : community.community_type === 'open' && (
              <button
                onClick={() => handleJoin(null)}
                disabled={joining}
                className="w-full py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer bg-indigo-600 text-white hover:bg-indigo-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {joining ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <LogIn className="w-4 h-4" />
                )}
                <span>{t('communities.join')}</span>
              </button>
            )
          )}

          {isMember && (
            <button
              onClick={handleLeave}
              disabled={leaving}
              className="w-full py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {leaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogOut className="w-4 h-4" />
              )}
              <span>{t('communities.leave')}</span>
            </button>
          )}

          {(canManageCommunity || isMember) && (
            <Link
              href={getUriWithOrg(orgslug, '/dash/communities')}
              className="w-full bg-white text-neutral-600 border border-neutral-200 py-2.5 rounded-lg font-medium hover:bg-neutral-50 transition-colors flex items-center justify-center gap-2 text-sm"
            >
              <Settings className="w-4 h-4" />
              {t('communities.manage')}
            </Link>
          )}
        </div>
      </div>

      {/* Join Plan MousePointer2 Modal */}
      <Modal
        isDialogOpen={joinModalOpen}
        onOpenChange={() => setJoinModalOpen(!joinModalOpen)}
        minHeight="no-min"
        minWidth="md"
        dialogContent={
          <div className="space-y-3">
            <p className="text-sm text-gray-500 mb-4">
              {t('communities.select_plan_to_join')}
            </p>
            {availablePlans.map((plan) => (
              <button
                key={plan.plan_uuid}
                onClick={() => handleJoin(plan.plan_uuid)}
                disabled={joining}
                className="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-left"
              >
                <div>
                  <h4 className="font-medium text-gray-900">{plan.name}</h4>
                  {plan.description && (
                    <p className="text-sm text-gray-500 mt-0.5">{plan.description}</p>
                  )}
                </div>
                <div className="text-right flex-shrink-0 ml-4">
                  <div className="text-lg font-bold text-gray-900">
                    {plan.price === 0
                      ? t('dashboard.courses.communities.settings.plans.free_plan')
                      : `${plan.price} ${plan.currency.toUpperCase()}`}
                  </div>
                  <div className="text-xs text-gray-400 capitalize">{plan.interval}</div>
                </div>
              </button>
            ))}
          </div>
        }
        dialogTitle={t('communities.join_community')}
        dialogDescription=""
      />

      {/* Quick Tips Card */}
      <div className="bg-white nice-shadow rounded-lg overflow-hidden p-4">
        <h3 className="font-medium text-gray-900 mb-2 text-sm">{t('communities.community_guidelines')}</h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          {t('communities.community_guidelines_text')}
        </p>
      </div>
    </div>
  )
}

function SpacesSection({
  communityUuid,
  accessToken,
  orgslug,
  spaceDiscussionCounts,
  canManageCommunity,
}: {
  communityUuid: string
  accessToken?: string
  orgslug: string
  spaceDiscussionCounts?: Record<number, number>
  canManageCommunity?: boolean
}) {
  const { t } = useTranslation()
  const [manageModalOpen, setManageModalOpen] = useState(false)
  const { data: spaces = [] } = useQuery<Space[]>({
    queryKey: ['community', communityUuid, 'spaces'],
    queryFn: () => getSpaces(communityUuid, accessToken),
    enabled: !!communityUuid && !!accessToken,
    staleTime: 60_000,
  })

  if (spaces.length === 0) return null

  return (
    <div className="border-t border-gray-100">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {t('communities.spaces') || 'Spaces'}
          </h3>
          {canManageCommunity && (
            <button onClick={() => setManageModalOpen(true)} className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
              {t('communities.manage_spaces') || 'Manage'}
            </button>
          )}
        </div>
        <div className="space-y-1">
          <Link
            href={getUriWithOrg(orgslug, `/community/${communityUuid.replace('community_', '')}`)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
          >
            <Hash size={14} className="text-gray-400 shrink-0" />
            <span className="flex-1">{t('communities.all_discussions') || 'All Discussions'}</span>
          </Link>
          {spaces.map((space) => (
            <Link
              key={space.id}
              href={getUriWithOrg(orgslug, `/community/${communityUuid.replace('community_', '')}/space/${space.space_uuid.replace('space_', '')}`)}
              className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors group"
            >
              <span className="text-base shrink-0">{space.icon || '💬'}</span>
              <span className="flex-1 truncate">{space.name}</span>
              {spaceDiscussionCounts?.[space.id] !== undefined && (
                <span className="text-xs text-gray-400 group-hover:text-gray-600">
                  {spaceDiscussionCounts[space.id]}
                </span>
              )}
            </Link>
          ))}
        </div>
      </div>
      <ManageSpacesModal
        isOpen={manageModalOpen}
        onClose={() => setManageModalOpen(false)}
        communityUuid={communityUuid}
      />
    </div>
  )
}

export default CommunitySidebar
