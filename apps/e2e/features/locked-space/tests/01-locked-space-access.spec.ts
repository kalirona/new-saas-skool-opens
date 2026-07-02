import { test, expect } from '../../../core/fixtures'
import { STUDENT_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { LockedSpacePage } from '../pages/space'

test.use({ storageState: STUDENT_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('non-member sees locked space and can request access', async ({ page }) => {
  const lockedPage = new LockedSpacePage(page)
  await lockedPage.open(scenario.seeded.communityUuid)
  await lockedPage.clickLockedSpace()
  await lockedPage.accessDeniedVisible()
  await lockedPage.requestAccess()
  await lockedPage.requestSent()
})
