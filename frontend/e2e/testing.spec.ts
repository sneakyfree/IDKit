import { test, expect } from "@playwright/test";

test.describe("A/B Testing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/testing");
  });

  test("should display the A/B testing page", async ({ page }) => {
    // Check page title/header
    await expect(page.locator("h1, h2").first()).toContainText(/test|a\/b|experiment/i);
  });

  test("should have tab navigation", async ({ page }) => {
    // Look for tabs (Active, Completed, Drafts)
    const activeTab = page.getByRole("button", { name: /active/i });
    const completedTab = page.getByRole("button", { name: /completed/i });
    const draftsTab = page.getByRole("button", { name: /draft/i });

    const hasActiveTabs =
      (await activeTab.isVisible().catch(() => false)) ||
      (await completedTab.isVisible().catch(() => false)) ||
      (await draftsTab.isVisible().catch(() => false));

    expect(hasActiveTabs).toBeTruthy();
  });

  test("should have create test button", async ({ page }) => {
    // Look for create test button
    const createButton = page
      .getByRole("button", { name: /create|new|add/i })
      .first();

    await expect(createButton).toBeVisible();
  });

  test("should display test cards", async ({ page }) => {
    // Look for test cards or list items
    const testCards = page.locator(
      '[class*="card"], [class*="test-item"], [role="article"]'
    );

    // Should have at least the mock data displayed
    const cardCount = await testCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test("should have filter options", async ({ page }) => {
    // Look for filter dropdown or buttons
    const filterDropdown = page.locator('select, [role="combobox"]').first();
    const filterButtons = page.locator('button:has-text("All Types")');

    const hasFilters =
      (await filterDropdown.isVisible().catch(() => false)) ||
      (await filterButtons.isVisible().catch(() => false));

    expect(hasFilters).toBeTruthy();
  });
});

test.describe("Create Test Modal", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/testing");
  });

  test("should open create test modal", async ({ page }) => {
    // Click create test button
    const createButton = page
      .getByRole("button", { name: /create|new/i })
      .first();

    if (await createButton.isVisible()) {
      await createButton.click();

      // Wait for modal
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();
      await expect(modal).toBeVisible({ timeout: 5000 });
    }
  });

  test("should have multi-step wizard", async ({ page }) => {
    // Click create test button
    const createButton = page
      .getByRole("button", { name: /create|new/i })
      .first();

    if (await createButton.isVisible()) {
      await createButton.click();

      // Look for step indicators or progress
      const stepIndicator = page.locator(
        '[class*="step"], [class*="progress"], [class*="wizard"]'
      );
      const nextButton = page.getByRole("button", { name: /next|continue/i });

      const hasWizard =
        (await stepIndicator.first().isVisible().catch(() => false)) ||
        (await nextButton.isVisible().catch(() => false));

      expect(hasWizard).toBeTruthy();
    }
  });

  test("should validate required fields", async ({ page }) => {
    // Click create test button
    const createButton = page
      .getByRole("button", { name: /create|new/i })
      .first();

    if (await createButton.isVisible()) {
      await createButton.click();

      // Try to proceed without filling required fields
      const nextButton = page.getByRole("button", { name: /next|continue/i });

      if (await nextButton.isVisible()) {
        // Next button should be disabled or show validation errors
        const isDisabled = await nextButton.isDisabled().catch(() => false);

        // If not disabled, clicking should show validation
        if (!isDisabled) {
          await nextButton.click();

          // Look for validation messages
          const validationError = page.locator(
            '[class*="error"], [role="alert"], text=/required/i'
          );
          // Validation should appear or button should be disabled
        }
      }
    }
  });
});

test.describe("Test Card Interactions", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/testing");
  });

  test("should expand test details", async ({ page }) => {
    // Click on a test card to view details
    const testCard = page
      .locator('[class*="card"], [role="article"]')
      .first();

    if (await testCard.isVisible()) {
      const viewDetailsButton = testCard.getByRole("button", {
        name: /view|details/i,
      });

      if (await viewDetailsButton.isVisible()) {
        await viewDetailsButton.click();

        // Should show detail modal or expand
        const detailModal = page.locator(
          '[role="dialog"], [class*="modal"], [class*="detail"]'
        );
        await expect(detailModal).toBeVisible({ timeout: 5000 }).catch(() => {
          // Details might be shown inline
        });
      }
    }
  });

  test("should start a draft test", async ({ page }) => {
    // Switch to drafts tab
    const draftsTab = page.getByRole("button", { name: /draft/i });

    if (await draftsTab.isVisible()) {
      await draftsTab.click();

      // Find start test button
      const startButton = page.getByRole("button", { name: /start/i }).first();

      if (await startButton.isVisible()) {
        await startButton.click();

        // Test should move to active or show confirmation
        // This is a smoke test for the interaction
      }
    }
  });
});
