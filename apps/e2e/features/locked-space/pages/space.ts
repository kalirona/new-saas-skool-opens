import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class LockedSpacePage {
  constructor(private readonly page: Page) {}

  async open(communityUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/community/${communityUuid}`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickLockedSpace(): Promise<void> {
    await this.page.getByText(/members only/i).first().click()
  }

  async accessDeniedVisible(): Promise<void> {
    await expect(this.page.getByText(/access denied|locked|members only/i).first()).toBeVisible({ timeout: 10_000 })
  }

  async requestAccess(): Promise<void> {
    await this.page.getByRole('button', { name: /request.*access|join/i }).first().click()
  }

  async requestSent(): Promise<void> {
    await expect(this.page.getByText(/request sent|pending/i).first()).toBeVisible({ timeout: 10_000 })
  }
}
