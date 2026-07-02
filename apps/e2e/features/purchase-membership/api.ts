import { req } from '../../core/client'
import type { Org } from '../../core/client'
export { login, getOrg, createStudent } from '../../core/client'

export interface SeededMembership {
  communityUuid: string
  planUuid: string
}

export async function seedPurchasablePlan(
  adminToken: string,
  org: Org,
  name: string,
): Promise<SeededMembership> {
  const community = await req<any>('POST', `/communities/?org_id=${org.id}`, adminToken, {
    name,
    description: 'E2E membership purchase',
    public: true,
    community_type: 'paid',
  })
  const plan = await req<any>(
    'POST', `/communities/${community.community_uuid}/plans`, adminToken,
    { name: 'Premium', price: 49.99, interval: 'monthly', currency: 'usd' },
  )
  return { communityUuid: community.community_uuid, planUuid: plan.plan_uuid }
}
