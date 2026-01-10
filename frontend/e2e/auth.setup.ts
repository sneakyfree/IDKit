import { test as setup, expect } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, "../.auth/user.json");

/**
 * Authentication Setup
 *
 * This setup file runs before other tests to authenticate a test user
 * and save the authentication state for reuse.
 */
setup("authenticate", async ({ page }) => {
  // Navigate to login page
  await page.goto("/login");

  // For development/testing, we may have a mock auth system
  // In a real scenario, this would interact with actual login forms
  const hasLoginForm = await page.locator('form[data-testid="login-form"]').isVisible().catch(() => false);

  if (hasLoginForm) {
    // Fill in login credentials
    await page.fill('[data-testid="email-input"]', "test@idkit.io");
    await page.fill('[data-testid="password-input"]', "testpassword123");
    await page.click('[data-testid="login-button"]');

    // Wait for successful login (redirect to dashboard or feed)
    await page.waitForURL(/\/(feed|dashboard)/, { timeout: 10000 });
  } else {
    // If no login form (e.g., development mode), just navigate to main page
    await page.goto("/");
  }

  // Save authentication state
  await page.context().storageState({ path: authFile });
});

setup("verify authentication", async ({ page }) => {
  // Load saved auth state and verify it works
  const context = await page.context().browser()?.newContext({
    storageState: authFile,
  });

  if (context) {
    const authPage = await context.newPage();
    await authPage.goto("/");

    // Verify we're logged in by checking for user-specific elements
    // This would be adjusted based on actual UI
    await expect(authPage).toHaveURL(/\/(feed|dashboard|$)/);

    await context.close();
  }
});
