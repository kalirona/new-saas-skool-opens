import { test, expect } from '../../../core/fixtures'
import { ADMIN_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { CourseEditorPage } from '../pages/editor'

test.use({ storageState: ADMIN_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('creator generates course outline via AI', async ({ page }) => {
  const editor = new CourseEditorPage(page)
  await editor.open(scenario.seeded.courseUuid)
  await editor.clickAiGenerate()
  await editor.fillAiPrompt('Introduction to Python programming for beginners')
  await editor.submitAiGeneration()
  await editor.aiResultVisible()
})
