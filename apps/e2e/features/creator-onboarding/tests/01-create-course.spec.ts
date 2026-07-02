import { test, expect } from '../../../core/fixtures'
import { ADMIN_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { CreatorDashboardPage } from '../pages/dashboard'

test.use({ storageState: ADMIN_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('creator can navigate to dashboard and see their course', async ({ page }) => {
  const dashboard = new CreatorDashboardPage(page)
  await dashboard.goto()
  await dashboard.courseIsVisible(scenario.courseName)
})
