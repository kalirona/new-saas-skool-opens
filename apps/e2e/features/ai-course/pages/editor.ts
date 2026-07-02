import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class CourseEditorPage {
  constructor(private readonly page: Page) {}

  async open(courseUuid: string): Promise<void> {
    await this.page.goto(`${BASE_URL}/course/${courseUuid}/edit`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickAiGenerate(): Promise<void> {
    await this.page.getByRole('button', { name: /ai|generate/i }).first().click()
  }

  async fillAiPrompt(prompt: string): Promise<void> {
    await this.page.getByPlaceholder(/describe|enter.*topic|prompt/i).first().fill(prompt)
  }

  async submitAiGeneration(): Promise<void> {
    await this.page.getByRole('button', { name: /generate|create|go/i }).first().click()
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(3000)
  }

  async aiResultVisible(): Promise<void> {
    await expect(this.page.getByText(/outline|generated|suggested|module|lesson/i).first()).toBeVisible({
      timeout: 30_000,
    })
  }
}
