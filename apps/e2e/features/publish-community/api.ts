import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededCommunity {
  communityUuid: string
  planUuid: string
}

export async function seedCommunityWithPlan(
  adminToken: string,
  org: Org,
  name: string,
): Promise<SeededCommunity> {
  const community = await req<any>('POST', `/communities/?org_id=${org.id}`, adminToken, {
    name,
    description: 'E2E paid community',
    public: false,
    community_type: 'paid',
  })
  const plan = await req<any>(
    'POST', `/communities/${community.community_uuid}/plans`, adminToken,
    { name: 'Monthly', price: 19.99, interval: 'monthly', currency: 'usd' },
  )
  return { communityUuid: community.community_uuid, planUuid: plan.plan_uuid }
}
