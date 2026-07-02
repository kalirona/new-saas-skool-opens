import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededResource {
  communityUuid: string
  spaceUuid: string
  spaceName: string
}

export async function seedSpaceWithResource(
  adminToken: string,
  org: Org,
  name: string,
): Promise<SeededResource> {
  const community = await req<any>('POST', `/communities/?org_id=${org.id}`, adminToken, {
    name,
    description: 'E2E resource download',
    public: true,
    community_type: 'free',
  })
  const space = await req<any>(
    'POST', `/communities/${community.community_uuid}/spaces`, adminToken,
    { name: 'Resources', visibility: 'members' },
  )
  return {
    communityUuid: community.community_uuid,
    spaceUuid: space.space_uuid,
    spaceName: space.name,
  }
}
