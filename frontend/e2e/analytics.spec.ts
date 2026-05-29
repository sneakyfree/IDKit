import { test, expect } from "@playwright/test";

/**
 * E2E Tests for Analytics Dashboard
 * 
 * Tests for analytics overview, export functionality, and navigation.
 */

test.describe("Analytics Dashboard", () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to analytics page
        await page.goto("/analytics");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display analytics overview", async ({ page }) => {
        // Check page loaded
        await expect(page.locator("h1")).toContainText("Analytics");

        // Check overview cards exist
        await expect(page.getByText("Followers").first()).toBeVisible();
        await expect(page.getByText("Views").first()).toBeVisible();
        await expect(page.getByText("Engagements").first()).toBeVisible();
    });

    test("should have time range selector", async ({ page }) => {
        // Check time range buttons
        await expect(page.getByRole("button", { name: /7 days/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /30 days/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /90 days/i }).first()).toBeVisible();

        // Click different time range
        await page.getByRole("button", { name: /7 days/i }).first().click();

        // Verify selection
        await expect(page.getByRole("button", { name: /7 days/i }).first()).toHaveClass(/bg-white/);
    });

    test("should display platform breakdown", async ({ page }) => {
        // Check platform performance section
        await expect(page.getByText("Platform Performance").first()).toBeVisible();

        // Verify platform names shown
        const platformSection = page.locator("text=Platform Performance").locator("..");
        await expect(platformSection).toBeVisible();
    });

    test("should navigate to export page", async ({ page }) => {
        // Click export button
        await page.getByRole("link", { name: /export/i }).first().click();

        // Verify navigation
        await expect(page).toHaveURL("/analytics/export");
        await expect(page.locator("h1")).toContainText("Export Analytics");
    });

    test("should navigate to ROI calculator", async ({ page }) => {
        // Click ROI calculator link
        await page.getByRole("link", { name: /roi calculator/i }).first().click();

        // Verify navigation
        await expect(page).toHaveURL("/roi");
    });

    test("should navigate to payouts", async ({ page }) => {
        // Click payouts link
        await page.getByRole("link", { name: /payouts/i }).first().click();

        // Verify navigation  
        await expect(page).toHaveURL("/settings/payouts");
    });
});

test.describe("Analytics Export", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/analytics/export");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display export options", async ({ page }) => {
        // Check page title
        await expect(page.locator("h1")).toContainText("Export");

        // Check format options
        await expect(page.getByText("CSV").first()).toBeVisible();
        await expect(page.getByText("JSON").first()).toBeVisible();

        // Check time period options
        await expect(page.getByText(/7 days/i).first()).toBeVisible();
        await expect(page.getByText(/30 days/i).first()).toBeVisible();
    });

    test("should toggle export format", async ({ page }) => {
        // Select JSON format
        await page.getByRole("button", { name: /json/i }).first().click();

        // Verify selection
        const jsonButton = page.getByRole("button", { name: /json/i });
        await expect(jsonButton).toHaveClass(/border-purple/);
    });

    test("should toggle time period", async ({ page }) => {
        // Select 90 days
        await page.getByRole("button", { name: /90 days/i }).first().click();

        // Verify selection
        await expect(page.getByRole("button", { name: /90 days/i }).first()).toHaveClass(/bg-purple/);
    });

    test("should show export preview", async ({ page }) => {
        // Check preview section
        await expect(page.getByText("Export Preview").first()).toBeVisible();
    });

    test("should navigate back to analytics", async ({ page }) => {
        // Click back button
        await page.locator('a[href="/analytics"]').first().click();

        // Verify navigation
        await expect(page).toHaveURL("/analytics");
    });
});
