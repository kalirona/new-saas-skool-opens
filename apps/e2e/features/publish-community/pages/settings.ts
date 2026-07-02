import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class CommunitySettingsPage {
  constructor(private readonly page: Page) {}

  async open(communityUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/community/${communityUuid}/settings`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async togglePublic(): Promise<void> {
    const toggle = this.page.getByRole('switch', { name: /public/i })
    const isOn = await toggle.isChecked()
    if (!isOn) await toggle.click()
  }

  async saveSettings(): Promise<void> {
    await this.page.getByRole('button', { name: /save|update/i }).first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async publishSuccessVisible(): Promise<void> {
    await expect(this.page.getByText(/published|public|live/i).first()).toBeVisible({ timeout: 10_000 })
  }
}
