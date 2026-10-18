import { expect, test } from '@playwright/test'

test('home shows the manifest and opens chapter 01', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Docker without the magic.')
  const manifest = page.locator('section', { has: page.locator('#chapters') })
  await expect(manifest.locator('ol > li')).toHaveCount(9)
  await expect(manifest).toContainText('The ten-second goodbye')
  await expect(page.getByRole('figure').first()).toContainText('PAYMENT_TOKEN=tp-prod-4f9a2c71')

  await page.getByRole('link', { name: 'Start chapter 01' }).click()
  await expect(page).toHaveURL(/\/workshop\/01-layers-and-the-cache$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Layers and the build cache')
})

test('the build cache reinstalls as shipped and skips the install when fixed', async ({ page }) => {
  await page.goto('/#build')
  const sim = page.locator('#build')
  const time = sim.getByTestId('Build time')
  const output = sim.getByRole('list', { name: 'Build output' })

  await sim.getByRole('button', { name: 'Build', exact: true }).click()
  await expect(time).toHaveText('96.3')
  await sim.getByRole('button', { name: 'Edit app.py, rebuild' }).click()
  await expect(time).toHaveText('96.3')
  await expect(output.locator('li').nth(3)).toContainText('Ran')
  await expect(sim.getByRole('status')).toContainText('pip install ran again anyway')

  await sim.getByText('Fixed', { exact: true }).click()
  await expect(time).toHaveText('0.0')
  await sim.getByRole('button', { name: 'Build', exact: true }).click()
  await sim.getByRole('button', { name: 'Edit app.py, rebuild' }).click()
  await expect(time).toHaveText('0.3')
  await expect(output.locator('li').nth(3)).toContainText('Cached')

  await sim.getByRole('button', { name: 'Edit requirements.txt, rebuild' }).click()
  await expect(sim.getByRole('status')).toContainText('cache doing its job')

  await sim.getByRole('button', { name: 'Move RUN pip install -r requirements.txt up' }).click()
  await sim.getByRole('button', { name: 'Move RUN pip install -r requirements.txt up' }).click()
  await sim.getByRole('button', { name: 'Build', exact: true }).click()
  await expect(output).toContainText('could not open requirements file')
})

test('Pip quizzes you, and closes with Escape', async ({ page }) => {
  await page.goto('/workshop/05-pid-one-and-signals')
  await page.getByRole('button', { name: 'Ask Pip' }).click()
  const panel = page.getByRole('region', { name: "Pip's notes" })
  await expect(panel).toContainText('exit code 137')

  await panel.getByRole('button', { name: 'It dies, as any process would' }).click()
  const verdict = panel.getByRole('status').first()
  await expect(verdict).toContainText('Not quite.')
  await expect(
    panel.getByRole('button', { name: /the kernel does not deliver default-action signals/ }),
  ).toBeDisabled()
  // The explanation is dark text on the white panel.
  const colours = await verdict.evaluate((node) => ({
    text: getComputedStyle(node).color,
    card: getComputedStyle(node.closest('section') as Element).backgroundColor,
  }))
  expect(colours).toEqual({ text: 'rgb(53, 71, 90)', card: 'rgb(255, 255, 255)' })

  await page.keyboard.press('Escape')
  await expect(panel).toBeHidden()
  await expect(page.getByRole('button', { name: 'Ask Pip' })).toBeVisible()
})

test('chapters render and page through in order', async ({ page }) => {
  await page.goto('/workshop')
  await expect(page.locator('main ol > li')).toHaveCount(9)

  await page.locator('main ol > li').nth(4).click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('PID 1 and signals')
  await expect(page.locator('main')).toContainText('docker stop took 10.0 s; exit code 137')
  await expect(page.locator('main pre').first()).toBeVisible()
  await page.getByRole('link', { name: /Next/ }).click()
  await expect(page).toHaveURL(/06-container-networking$/)
  await expect(
    page.getByRole('heading', { level: 2, name: /Where a published port/ }),
  ).toBeVisible()
})

test('nothing scrolls sideways, and code scrolls inside its block', async ({ page }) => {
  const paths = [
    '/',
    '/workshop',
    '/workshop/05-pid-one-and-signals',
    '/workshop/09-resource-limits',
  ]
  for (const path of paths) {
    await page.goto(path)
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, path).toBeLessThanOrEqual(0)
  }
  const pre = page.locator('.code-block pre').first()
  const fits = await pre.evaluate((node) => node.getBoundingClientRect().right <= window.innerWidth)
  expect(fits).toBe(true)
})

test('buttons and controls are easy to tap', async ({ page, isMobile }) => {
  test.skip(!isMobile, 'tap targets matter on a phone')
  for (const path of ['/', '/workshop/05-pid-one-and-signals']) {
    await page.goto(path)
    await page.getByRole('button', { name: 'Ask Pip' }).click()
    const small = await page.evaluate(() =>
      [...document.querySelectorAll('button, summary, label:has(input), header a, nav a')]
        .filter((node) => {
          const box = node.getBoundingClientRect()
          const shown = getComputedStyle(node).visibility !== 'hidden' && box.width > 0
          return shown && node.getAttribute('aria-hidden') !== 'true' && box.height < 40
        })
        .map((node) => (node.textContent || node.getAttribute('aria-label') || '').trim()),
    )
    expect(small, path).toEqual([])
    await page.keyboard.press('Escape')
  }
})

test('back to top returns to the top', async ({ page }) => {
  await page.goto('/workshop/09-resource-limits')
  const button = page.getByRole('button', { name: 'Back to top' })
  await page.evaluate(() => window.scrollTo(0, 3000))
  await expect(button).toBeVisible()
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0)
})

test('keyboard focus is visible', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  await page.keyboard.press('Tab')
  const outline = await page.evaluate(() => {
    const node = document.activeElement as Element
    return getComputedStyle(node).outlineStyle
  })
  expect(outline).not.toBe('none')
})
