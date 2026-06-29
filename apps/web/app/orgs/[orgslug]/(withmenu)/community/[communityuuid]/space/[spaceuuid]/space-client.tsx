'use client'

import React, { useState } from 'react'
import GeneralWrapperStyled from '@components/Objects/StyledElements/Wrappers/GeneralWrapper'
import { Breadcrumbs } from '@components/Objects/Breadcrumbs/Breadcrumbs'
import { CommunitySidebar } from '@components/Objects/Communities/CommunitySidebar'
import { SpaceNav } from '@components/Objects/Communities/SpaceNav'
import { MessageCircle, Hash } from 'lucide-react'
import { getUriWithOrg } from '@services/config/config'
import { CommunityActionsMobile } from '@components/Objects/Communities/CommunityActionsMobile'
import { DiscussionList } from '@components/Objects/Communities/DiscussionList'
import { CreateDiscussionModal } from '@components/Objects/Modals/Communities/CreateDiscussionModal'
import { Community } from '@services/communities/communities'
import { Space } from '@services/communities/spaces'
import { DiscussionWithAuthor } from '@services/communities/discussions'
import { useMediaQuery } from 'usehooks-ts'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery } from '@tanstack/react-query'
import { getSpaces } from '@services/communities/spaces'

interface SpaceClientProps {
  community: Community
  space: Space
  initialDiscussions: DiscussionWithAuthor[]
  orgslug: string
  org_id: number
}

const SpaceClient = ({
  community,
  space,
  initialDiscussions,
  orgslug,
  org_id,
}: SpaceClientProps) => {
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const [isCreateDiscussionModalOpen, setIsCreateDiscussionModalOpen] = useState(false)
  const [selectedSpaceId, setSelectedSpaceId] = useState<number | null>(space.id)
  const isMobile = useMediaQuery('(max-width: 768px)')

  const { data: spaces = [], isLoading: spacesLoading } = useQuery({
    queryKey: ['community', community.community_uuid, 'spaces'],
    queryFn: () => getSpaces(community.community_uuid, accessToken),
    enabled: !!community.community_uuid && !!accessToken,
    staleTime: 60_000,
  })

  const spaceDiscussionCounts = React.useMemo(() => {
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
        <div className="pb-4">
          <Breadcrumbs items={[
            { label: 'Communities', href: getUriWithOrg(orgslug, '/communities'), icon: <MessageCircle size={14} /> },
            { label: community.name, href: getUriWithOrg(orgslug, `/community/${community.community_uuid.replace('community_', '')}`) },
            { label: space.name }
          ]} />
        </div>

        <div className="flex flex-col md:flex-row gap-6 pt-2">
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

          <div className="flex-1 min-w-0">
            {/* Space header */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">{space.icon || <Hash size={20} />}</span>
                <h1 className="text-xl font-bold text-gray-900">{space.name}</h1>
              </div>
              {space.description && (
                <p className="text-sm text-gray-500">{space.description}</p>
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

        {isMobile && <div className="h-24" />}
      </GeneralWrapperStyled>

      {isMobile && (
        <CommunityActionsMobile
          community={community}
          orgslug={orgslug}
          onCreateDiscussion={() => setIsCreateDiscussionModalOpen(true)}
        />
      )}

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

export default SpaceClient
