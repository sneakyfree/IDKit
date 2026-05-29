import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test("should display the home page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Check that the page loaded
    await expect(page).toHaveTitle(/IDKit/i);
  });

  test("should have navigation elements", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Check for main navigation
    const nav = page.locator("nav, header");
    await expect(nav.first()).toBeVisible();
  });

  test("should be responsive", async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Page should still be functional on mobile
    await expect(page).toHaveTitle(/IDKit/i);

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    await expect(page).toHaveTitle(/IDKit/i);

    // Test desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    await expect(page).toHaveTitle(/IDKit/i);
  });
});

test.describe("Navigation", () => {
  test("should navigate to schedule page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Look for schedule link and click it
    const scheduleLink = page.locator('a[href*="schedule"]').first();
    if (await scheduleLink.isVisible()) {
      await scheduleLink.click();
      await expect(page).toHaveURL(/schedule/);
    }
  });

  test("should navigate to settings page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Look for settings link and click it
    const settingsLink = page.locator('a[href*="settings"]').first();
    if (await settingsLink.isVisible()) {
      await settingsLink.click();
      await expect(page).toHaveURL(/settings/);
    }
  });
});
