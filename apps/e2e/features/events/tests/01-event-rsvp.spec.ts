import { test, expect } from '../../../core/fixtures'
import { STUDENT_STATE } from '../../../core/sharedAuth'
import { setupScenario } from './scenario'
import { EventPage } from '../pages/event'

test.use({ storageState: STUDENT_STATE })

let scenario: Awaited<ReturnType<typeof setupScenario>>

test.beforeAll(async () => {
  scenario = await setupScenario()
})

test('student RSVPs to a live event', async ({ page }) => {
  const eventPage = new EventPage(page)
  await eventPage.open(scenario.seeded.eventUuid)
  await eventPage.clickRsvp()
  await eventPage.confirmRsvp()
  await eventPage.rsvpConfirmed()
})
