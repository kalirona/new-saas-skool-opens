import { test, expect } from '../../../core/fixtures'
import { STUDENT_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { CommunityPage } from '../pages/community'

test.use({ storageState: STUDENT_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('student views a paid community and navigates to checkout', async ({ page }) => {
  const communityPage = new CommunityPage(page)
  await communityPage.open(scenario.seeded.communityUuid)
  await communityPage.clickJoin()
  await communityPage.selectPlan()
  await communityPage.proceedToCheckout()
  await communityPage.checkoutPageLoaded()
})
