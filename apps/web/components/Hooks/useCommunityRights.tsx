'use client'
import { getCommunityRights } from '@services/communities/communities'
import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { MembershipPlanInfo, UserMembershipInfo } from '@services/communities/communities'

export interface CommunityRights {
  community_uuid: string
  user_id: number
  is_anonymous: boolean
  permissions: {
    read: boolean
    create: boolean
    update: boolean
    delete: boolean
    create_discussion: boolean
  }
  ownership: {
    is_admin: boolean
    is_maintainer_role: boolean
  }
  access: {
    via_public: boolean
    via_usergroups: number[]
    has_usergroup_restriction: boolean
  }
  membership: {
    has_plans: boolean
    available_plans: MembershipPlanInfo[]
    user_membership: UserMembershipInfo | null
  }
}

export function useCommunityRights(communityuuid: string) {
  const session = useLHSession() as any
  const access_token = session?.data?.tokens?.access_token

  const { data: rights, error, isLoading } = useQuery<CommunityRights>({
    queryKey: queryKeys.community.rights(communityuuid),
    queryFn: () => getCommunityRights(communityuuid, access_token),
    enabled: !!communityuuid && !!access_token,
    staleTime: 60_000,
  })

  return {
    rights,
    error,
    isLoading,
    hasPermission: (permission: keyof CommunityRights['permissions']) => {
      return rights?.permissions?.[permission] ?? false
    },
    isAdmin: rights?.ownership?.is_admin ?? false,
    isMaintainer: rights?.ownership?.is_maintainer_role ?? false,
    canCreateDiscussion: rights?.permissions?.create_discussion ?? false,
    canManageCommunity: (rights?.ownership?.is_admin || rights?.ownership?.is_maintainer_role) ?? false,
    hasPlans: rights?.membership?.has_plans ?? false,
    availablePlans: rights?.membership?.available_plans ?? [],
    userMembership: rights?.membership?.user_membership ?? null,
    isMember: rights?.membership?.user_membership?.status === 'active',
  }
}
