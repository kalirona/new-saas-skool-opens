import { test, expect } from '../../../core/fixtures'
import { STUDENT_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { ResourceSpacePage } from '../pages/space'

test.use({ storageState: STUDENT_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('student opens resources space and triggers download', async ({ page }) => {
  const resourcePage = new ResourceSpacePage(page)
  await resourcePage.open(scenario.seeded.communityUuid)
  await resourcePage.clickResourcesSpace()
  await resourcePage.resourceListVisible()
  await resourcePage.clickDownload()
})
