import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class CommunityPage {
  constructor(private readonly page: Page) {}

  async open(communityUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/community/${communityUuid}`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickJoin(): Promise<void> {
    await this.page.getByRole('button', { name: /join|subscribe|get.*membership/i }).first().click()
  }

  async selectPlan(): Promise<void> {
    await this.page.getByRole('button', { name: /select|choose|premium/i }).first().click()
  }

  async proceedToCheckout(): Promise<void> {
    await this.page.getByRole('button', { name: /checkout|continue|pay/i }).first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async checkoutPageLoaded(): Promise<void> {
    await expect(this.page).toHaveURL(/checkout|stripe|payment/, { timeout: 15_000 })
  }
}
