import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class EventPage {
  constructor(private readonly page: Page) {}

  async open(eventUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/events/${eventUuid}`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickRsvp(): Promise<void> {
    await this.page.getByRole('button', { name: /rsvp|register|attend/i }).first().click()
  }

  async confirmRsvp(): Promise<void> {
    await this.page.getByRole('button', { name: /confirm|yes|rsvp/i }).first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async rsvpConfirmed(): Promise<void> {
    await expect(this.page.getByText(/registered|confirmed|attending/i).first()).toBeVisible({
      timeout: 10_000,
    })
  }
}
