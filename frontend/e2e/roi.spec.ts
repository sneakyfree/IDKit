import { test, expect } from "@playwright/test";

/**
 * E2E Tests for ROI Calculator
 * 
 * Tests for ROI overview, cost tracking, and history views.
 */

test.describe("ROI Calculator", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/roi");
    });

    test("should display ROI calculator page", async ({ page }) => {
        // Check page loaded
        await expect(page.locator("h1")).toContainText("ROI");
    });

    test("should show tab navigation", async ({ page }) => {
        // Check tabs exist
        await expect(page.getByRole("button", { name: /overview/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /costs/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /history/i })).toBeVisible();
    });

    test("should display overview metrics", async ({ page }) => {
        // Click overview tab (default)
        await page.getByRole("button", { name: /overview/i }).click();

        // Check key metrics are displayed
        await expect(page.getByText(/revenue/i)).toBeVisible();
        await expect(page.getByText(/costs/i)).toBeVisible();
    });

    test("should switch to costs tab", async ({ page }) => {
        // Click costs tab
        await page.getByRole("button", { name: /costs/i }).click();

        // Verify costs content is visible
        await expect(page.getByText(/expenses/i)).toBeVisible();
    });

    test("should switch to history tab", async ({ page }) => {
        // Click history tab
        await page.getByRole("button", { name: /history/i }).click();

        // Verify history content or empty state
        // Either shows reports or "No ROI reports" message
        const pageContent = page.locator("main");
        await expect(pageContent).toBeVisible();
    });

    test("should have add cost button in costs tab", async ({ page }) => {
        // Navigate to costs tab
        await page.getByRole("button", { name: /costs/i }).click();

        // Check for add button
        const addButton = page.getByRole("button", { name: /add/i });
        await expect(addButton).toBeVisible();
    });

    test("should open add cost modal", async ({ page }) => {
        // Navigate to costs tab
        await page.getByRole("button", { name: /costs/i }).click();

        // Click add button
        await page.getByRole("button", { name: /add/i }).click();

        // Check modal opened (form should be visible)
        await expect(page.getByPlaceholder(/description/i)).toBeVisible();
    });

    test("should have cost category options", async ({ page }) => {
        // Navigate to costs tab and open add modal
        await page.getByRole("button", { name: /costs/i }).click();
        await page.getByRole("button", { name: /add/i }).click();

        // Check category selector exists
        const categorySelect = page.locator("select, [role='listbox']").first();
        await expect(categorySelect).toBeVisible();
    });
});

test.describe("ROI Calculator - Cost Entry", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/roi");
        await page.getByRole("button", { name: /costs/i }).click();
    });

    test("should fill and submit cost entry form", async ({ page }) => {
        // Open add cost modal
        await page.getByRole("button", { name: /add/i }).click();

        // Fill in the form
        await page.getByPlaceholder(/description/i).fill("Test Equipment");

        // Find and fill amount field
        const amountInput = page.locator('input[type="number"]').first();
        await amountInput.fill("99.99");

        // Submit form
        await page.getByRole("button", { name: /save|add|submit/i }).click();

        // Verify submission (modal closes or success message)
        await expect(page.getByPlaceholder(/description/i)).not.toBeVisible({ timeout: 5000 });
    });

    test("should show cost entry validation", async ({ page }) => {
        // Open add modal
        await page.getByRole("button", { name: /add/i }).click();

        // Try to submit empty form
        await page.getByRole("button", { name: /save|add|submit/i }).click();

        // Form should still be visible (not submitted)
        await expect(page.getByPlaceholder(/description/i)).toBeVisible();
    });
});

test.describe("ROI Calculator - Navigation", () => {
    test("should navigate back from ROI page", async ({ page }) => {
        await page.goto("/roi");

        // Find and click back navigation
        const backLink = page.locator('a[href="/analytics"], button:has-text("Back")').first();
        if (await backLink.isVisible()) {
            await backLink.click();
            // Should navigate to analytics or previous page
        }
    });

    test("should be accessible from analytics", async ({ page }) => {
        // Start from analytics
        await page.goto("/analytics");

        // Click ROI link
        await page.getByRole("link", { name: /roi/i }).click();

        // Verify we're on ROI page
        await expect(page).toHaveURL("/roi");
    });
});
