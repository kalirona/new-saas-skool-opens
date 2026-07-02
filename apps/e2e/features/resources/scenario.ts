import * as api from './api'
import { ADMIN_EMAIL, ADMIN_PASSWORD, uniqueSuffix } from '../../core/instance'
import { sharedStudent } from '../../core/sharedAuth'

let cachedAdminToken: string | null = null

async function adminToken(): Promise<string> {
  if (!cachedAdminToken) {
    cachedAdminToken = await api.login(ADMIN_EMAIL, ADMIN_PASSWORD)
  }
  return cachedAdminToken
}

export async function setupScenario() {
  const token = await adminToken()
  const org = await api.getOrg()
  const suffix = uniqueSuffix()
  const communityName = `E2E Resources ${suffix}`
  const seeded = await api.seedSpaceWithResource(token, org, communityName)
  return { token, org, seeded, communityName, student: sharedStudent() }
}
