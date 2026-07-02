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
  const eventTitle = `E2E Event ${suffix}`
  const seeded = await api.seedEvent(
    token, org, eventTitle,
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  )
  return { token, org, seeded, eventTitle, student: sharedStudent() }
}
