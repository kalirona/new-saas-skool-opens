import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededLockedSpace {
  communityUuid: string
  spaceUuid: string
}

export async function seedLockedSpace(
  adminToken: string,
  org: Org,
  name: string,
): Promise<SeededLockedSpace> {
  const community = await req<any>('POST', `/communities/?org_id=${org.id}`, adminToken, {
    name,
    description: 'E2E locked space',
    public: true,
    community_type: 'free',
  })
  const space = await req<any>(
    'POST', `/communities/${community.community_uuid}/spaces`, adminToken,
    { name: 'Members Only', visibility: 'members' },
  )
  return { communityUuid: community.community_uuid, spaceUuid: space.space_uuid }
}
