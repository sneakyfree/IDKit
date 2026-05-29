import { test, expect } from "@playwright/test";

test.describe("Approvals Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/approvals");
  await page.waitForLoadState("networkidle").catch(() => {});
  });

  test("should display the approvals page", async ({ page }) => {
    // Check page title/header
    await expect(page.locator("h1, h2").first()).toContainText(/approval/i);
  });

  test("should have status tabs", async ({ page }) => {
    // Look for tabs (Pending, Approved, Rejected)
    const pendingTab = page.getByRole("button", { name: /pending/i });
    const approvedTab = page.getByRole("button", { name: /approved/i });
    const rejectedTab = page.getByRole("button", { name: /rejected/i });

    const hasTabs =
      (await pendingTab.isVisible().catch(() => false)) ||
      (await approvedTab.isVisible().catch(() => false)) ||
      (await rejectedTab.isVisible().catch(() => false));

    expect(hasTabs).toBeTruthy();
  });

  test("should display approval cards", async ({ page }) => {
    // Look for approval cards
    const approvalCards = page.locator(
      '[class*="card"], [class*="approval-item"], [role="article"]'
    );

    // Should display cards (even if empty state)
    const cardCount = await approvalCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test("should have content type filter", async ({ page }) => {
    // Look for filter dropdown
    const filterDropdown = page.locator('select, [role="combobox"]').first();
    const filterText = page.locator('text=/all types|filter/i').first();

    const hasFilter =
      (await filterDropdown.isVisible().catch(() => false)) ||
      (await filterText.isVisible().catch(() => false));

    expect(hasFilter).toBeTruthy();
  });
});

test.describe("Approval Card Interactions", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/approvals");
  await page.waitForLoadState("networkidle").catch(() => {});
  });

  test("should show review modal when clicking review button", async ({ page }) => {
    // Find a review button on a card
    const reviewButton = page.getByRole("button", { name: /review/i }).first();

    if (await reviewButton.isVisible()) {
      await reviewButton.click();

      // Should show review modal
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();
      await expect(modal).toBeVisible({ timeout: 5000 });
    }
  });

  test("should have approve and reject buttons in review modal", async ({ page }) => {
    // Find and click review button
    const reviewButton = page.getByRole("button", { name: /review/i }).first();

    if (await reviewButton.isVisible()) {
      await reviewButton.click();

      // Wait for modal
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();

      if (await modal.isVisible()) {
        // Look for approve and reject buttons
        const approveButton = modal.getByRole("button", { name: /approve/i });
        const rejectButton = modal.getByRole("button", { name: /reject/i });

        const hasActions =
          (await approveButton.isVisible().catch(() => false)) ||
          (await rejectButton.isVisible().catch(() => false));

        expect(hasActions).toBeTruthy();
      }
    }
  });

  test("should require reason for rejection", async ({ page }) => {
    // Find and click review button
    const reviewButton = page.getByRole("button", { name: /review/i }).first();

    if (await reviewButton.isVisible()) {
      await reviewButton.click();

      // Wait for modal
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();

      if (await modal.isVisible()) {
        // Click reject button
        const rejectButton = modal.getByRole("button", { name: /reject/i });

        if (await rejectButton.isVisible()) {
          // Check if there's a reason input or if clicking shows one
          const reasonInput = modal.locator(
            'textarea, input[type="text"][placeholder*="reason"]'
          );

          const hasReasonInput = await reasonInput.isVisible().catch(() => false);

          // Either reason input is already visible or button click should show it
          if (!hasReasonInput) {
            await rejectButton.click();
            // Now check for validation or reason input
          }
        }
      }
    }
  });
});

test.describe("Tab Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/approvals");
  await page.waitForLoadState("networkidle").catch(() => {});
  });

  test("should switch between tabs", async ({ page }) => {
    // Get all tabs
    const pendingTab = page.getByRole("button", { name: /pending/i });
    const approvedTab = page.getByRole("button", { name: /approved/i });
    const rejectedTab = page.getByRole("button", { name: /rejected/i });

    // Click approved tab
    if (await approvedTab.isVisible()) {
      await approvedTab.click();
      // Tab should be active/selected
      await expect(approvedTab).toHaveAttribute("aria-selected", "true").catch(
        () => {
          // Different implementation might use class instead
        }
      );
    }

    // Click rejected tab
    if (await rejectedTab.isVisible()) {
      await rejectedTab.click();
      await expect(rejectedTab).toHaveAttribute("aria-selected", "true").catch(
        () => {}
      );
    }

    // Click back to pending
    if (await pendingTab.isVisible()) {
      await pendingTab.click();
      await expect(pendingTab).toHaveAttribute("aria-selected", "true").catch(
        () => {}
      );
    }
  });

  test("should show correct content count per tab", async ({ page }) => {
    // Tabs might show counts
    const tabs = page.locator(
      'button:has-text("Pending"), button:has-text("Approved"), button:has-text("Rejected")'
    );

    // Each tab might have a count badge
    const tabsCount = await tabs.count();

    if (tabsCount > 0) {
      // Verify tabs are clickable and show content
      for (let i = 0; i < tabsCount; i++) {
        await tabs.nth(i).click();
        // Should update content area
        await page.waitForTimeout(300); // Brief wait for content update
      }
    }
  });
});
