import { Page, expect } from '@playwright/test'
import { BASE_URL } from '../../../core/instance'

export class CreatorDashboardPage {
  constructor(private readonly page: Page) {}

  async goto(): Promise<void> {
    await this.page.goto(`${BASE_URL}/creator`)
    await expect(this.page.locator('main')).toBeVisible({ timeout: 15_000 })
  }

  async clickCreateCourse(): Promise<void> {
    await this.page.getByRole('button', { name: /create.*course/i }).first().click()
  }

  async fillCourseForm(name: string, description: string): Promise<void> {
    await this.page.getByLabel(/course name/i).fill(name)
    await this.page.getByLabel(/description/i).fill(description)
  }

  async submitCourseForm(): Promise<void> {
    await this.page.getByRole('button', { name: /save|create|publish/i }).first().click()
    await this.page.waitForLoadState('networkidle')
  }

  async courseIsVisible(courseName: string): Promise<void> {
    await expect(this.page.getByText(courseName).first()).toBeVisible({ timeout: 10_000 })
  }
}
