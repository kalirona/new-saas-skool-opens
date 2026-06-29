'use client'

import React, { useState, useMemo } from 'react'
import GeneralWrapperStyled from '@components/Objects/StyledElements/Wrappers/GeneralWrapper'
import { Breadcrumbs } from '@components/Objects/Breadcrumbs/Breadcrumbs'
import { CommunitySidebar } from '@components/Objects/Communities/CommunitySidebar'
import { SpaceNav } from '@components/Objects/Communities/SpaceNav'
import { MessageCircle } from 'lucide-react'
import { getUriWithOrg } from '@services/config/config'
import { CommunityActionsMobile } from '@components/Objects/Communities/CommunityActionsMobile'
import { DiscussionList } from '@components/Objects/Communities/DiscussionList'
import { CreateDiscussionModal } from '@components/Objects/Modals/Communities/CreateDiscussionModal'
import { Community } from '@services/communities/communities'
import { DiscussionWithAuthor } from '@services/communities/discussions'
import { useMediaQuery } from 'usehooks-ts'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery } from '@tanstack/react-query'
import { getSpaces, Space } from '@services/communities/spaces'

interface CommunityClientProps {
  community: Community
  initialDiscussions: DiscussionWithAuthor[]
  orgslug: string
  org_id: number
}

const CommunityClient = ({
  community,
  initialDiscussions,
  orgslug,
  org_id,
}: CommunityClientProps) => {
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const [isCreateDiscussionModalOpen, setIsCreateDiscussionModalOpen] = useState(false)
  const [selectedSpaceId, setSelectedSpaceId] = useState<number | null>(null)
  const isMobile = useMediaQuery('(max-width: 768px)')

  const { data: spaces = [], isLoading: spacesLoading } = useQuery<Space[]>({
    queryKey: ['community', community.community_uuid, 'spaces'],
    queryFn: () => getSpaces(community.community_uuid, accessToken),
    enabled: !!community.community_uuid && !!accessToken,
    staleTime: 60_000,
  })

  const spaceDiscussionCounts = useMemo(() => {
    const counts: Record<number, number> = {}
    for (const d of initialDiscussions) {
      if (d.space_id != null) {
        counts[d.space_id] = (counts[d.space_id] || 0) + 1
      }
    }
    return counts
  }, [initialDiscussions])

  return (
    <>
      <GeneralWrapperStyled>
        {/* Breadcrumbs */}
        <div className="pb-4">
          <Breadcrumbs items={[
            { label: 'Communities', href: getUriWithOrg(orgslug, '/communities'), icon: <MessageCircle size={14} /> },
            { label: community.name }
          ]} />
        </div>

        {/* Forum Layout - Sidebar Left, Content Right */}
        <div className="flex flex-col md:flex-row gap-6 pt-2">
          {/* Left Sidebar - Community Info (Monitor only) */}
          <div className="hidden md:block w-full md:w-72 lg:w-80 flex-shrink-0">
            <div className="sticky top-24">
              <CommunitySidebar
                community={community}
                discussionCount={initialDiscussions.length}
                orgslug={orgslug}
                onCreateDiscussion={() => setIsCreateDiscussionModalOpen(true)}
                spaceDiscussionCounts={spaceDiscussionCounts}
              />
            </div>
          </div>

          {/* Main Content - Discussions Feed */}
          <div className="flex-1 min-w-0">
            {/* Mobile only shows community name */}
            <div className="md:hidden mb-4">
              <h1 className="text-xl font-bold text-gray-900">{community.name}</h1>
              {community.description && (
                <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                  {community.description}
                </p>
              )}
            </div>

            {/* Space Navigation */}
            {spaces.length > 0 && (
              <div className="mb-3">
                <SpaceNav
                  spaces={spaces}
                  selectedSpaceId={selectedSpaceId}
                  onSelectSpace={setSelectedSpaceId}
                  isLoading={spacesLoading}
                />
              </div>
            )}

            {/* Discussions List */}
            <div className="bg-white nice-shadow rounded-lg overflow-hidden">
              <DiscussionList
                communityUuid={community.community_uuid}
                orgslug={orgslug}
                onCreateClick={() => setIsCreateDiscussionModalOpen(true)}
                initialDiscussions={initialDiscussions}
                spaceId={selectedSpaceId}
              />
            </div>
          </div>
        </div>

        {/* Bottom padding for mobile action bar */}
        {isMobile && <div className="h-24" />}
      </GeneralWrapperStyled>

      {/* Mobile Actions Bar */}
      {isMobile && (
        <CommunityActionsMobile
          community={community}
          orgslug={orgslug}
          onCreateDiscussion={() => setIsCreateDiscussionModalOpen(true)}
        />
      )}

      {/* Modals */}
      <CreateDiscussionModal
        isOpen={isCreateDiscussionModalOpen}
        onClose={() => setIsCreateDiscussionModalOpen(false)}
        communityUuid={community.community_uuid}
        orgSlug={orgslug}
        spaces={spaces}
        selectedSpaceId={selectedSpaceId}
      />
    </>
  )
}

export default CommunityClient
