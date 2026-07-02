import { test, expect } from '../../../core/fixtures'
import { ADMIN_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { CommunitySettingsPage } from '../pages/settings'

test.use({ storageState: ADMIN_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('admin publishes a paid community with membership plan', async ({ page }) => {
  const settings = new CommunitySettingsPage(page)
  await settings.open(scenario.seeded.communityUuid)
  await settings.togglePublic()
  await settings.saveSettings()
  await settings.publishSuccessVisible()
})
