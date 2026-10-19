import { expect, test } from '@playwright/test'

test('home shows the path and opens chapter 01', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Docker, from first container to production',
  )
  await expect(page.locator('#chapters ~ div ol > li, section:has(#chapters) ol > li')).toHaveCount(
    12,
  )
  await expect(page.getByRole('figure')).toContainText('took 10.6 s, exit code 137')

  await page.getByRole('link', { name: 'Start chapter 01' }).click()
  await expect(page).toHaveURL(/\/workshop\/01-containers-are-processes$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Containers are processes')
})

test('the cache simulator reinstalls as shipped and stays cached when fixed', async ({ page }) => {
  await page.goto('/')
  const status = page.getByRole('status').first()
  const runs = page.getByTestId('pip install runs')

  await page.getByRole('button', { name: 'Build', exact: true }).click()
  await page.getByRole('button', { name: 'Change app/main.py, rebuild' }).click()
  await expect(runs).toHaveText('2')
  await expect(status).toContainText('ran again anyway')

  await page.getByText('Fixed', { exact: true }).click()
  await page.getByRole('button', { name: 'Build', exact: true }).click()
  await page.getByRole('button', { name: 'Change app/main.py, rebuild' }).click()
  await expect(runs).toHaveText('1')
  await expect(status).toContainText('came from the cache')
})

test('a chapter renders, quizzes and pages on', async ({ page }) => {
  await page.goto('/workshop/09-graceful-shutdown')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('PID 1 and graceful shutdown')
  await expect(page.locator('main')).toContainText('took 10.6 s, exit code 137')

  const quiz = page.getByRole('region', { name: 'Two questions before you move on' })
  await quiz.getByRole('button', { name: /It crashed/ }).click()
  await expect(quiz.getByRole('status').first()).toContainText('Not quite.')

  await page.getByRole('link', { name: /Next/ }).click()
  await expect(page).toHaveURL(/10-health-checks$/)
})

test('nothing overflows the page sideways', async ({ page }) => {
  for (const url of ['/', '/workshop', '/workshop/06-compose', '/workshop/12-tags-and-digests']) {
    await page.goto(url)
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, url).toBeLessThanOrEqual(0)
  }
})

test('back to top appears after scrolling and returns to the top', async ({ page }) => {
  await page.goto('/workshop/03-build-cache')
  const button = page.getByRole('button', { name: 'Back to top' })
  await page.evaluate(() => window.scrollTo(0, 2500))
  await expect(button).toBeVisible()
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeLessThan(50)
})
