import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class ResourceSpacePage {
  constructor(private readonly page: Page) {}

  async open(communityUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/community/${communityUuid}`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickResourcesSpace(): Promise<void> {
    await this.page.getByText(/resources/i).first().click()
  }

  async resourceListVisible(): Promise<void> {
    await expect(this.page.getByText(/resource|file|download/i).first()).toBeVisible({ timeout: 10_000 })
  }

  async clickDownload(): Promise<void> {
    const [download] = await Promise.all([
      this.page.waitForEvent('download', { timeout: 10_000 }).catch(() => null),
      this.page.getByRole('button', { name: /download/i }).first().click(),
    ])
    if (download) {
      await download.cancel()
    }
  }
}
