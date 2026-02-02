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
    });

    test("should display analytics overview", async ({ page }) => {
        // Check page loaded
        await expect(page.locator("h1")).toContainText("Analytics");

        // Check overview cards exist
        await expect(page.getByText("Followers")).toBeVisible();
        await expect(page.getByText("Views")).toBeVisible();
        await expect(page.getByText("Engagements")).toBeVisible();
    });

    test("should have time range selector", async ({ page }) => {
        // Check time range buttons
        await expect(page.getByRole("button", { name: /7 days/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /30 days/i })).toBeVisible();
        await expect(page.getByRole("button", { name: /90 days/i })).toBeVisible();

        // Click different time range
        await page.getByRole("button", { name: /7 days/i }).click();

        // Verify selection
        await expect(page.getByRole("button", { name: /7 days/i })).toHaveClass(/bg-white/);
    });

    test("should display platform breakdown", async ({ page }) => {
        // Check platform performance section
        await expect(page.getByText("Platform Performance")).toBeVisible();

        // Verify platform names shown
        const platformSection = page.locator("text=Platform Performance").locator("..");
        await expect(platformSection).toBeVisible();
    });

    test("should navigate to export page", async ({ page }) => {
        // Click export button
        await page.getByRole("link", { name: /export/i }).click();

        // Verify navigation
        await expect(page).toHaveURL("/analytics/export");
        await expect(page.locator("h1")).toContainText("Export Analytics");
    });

    test("should navigate to ROI calculator", async ({ page }) => {
        // Click ROI calculator link
        await page.getByRole("link", { name: /roi calculator/i }).click();

        // Verify navigation
        await expect(page).toHaveURL("/roi");
    });

    test("should navigate to payouts", async ({ page }) => {
        // Click payouts link
        await page.getByRole("link", { name: /payouts/i }).click();

        // Verify navigation  
        await expect(page).toHaveURL("/settings/payouts");
    });
});

test.describe("Analytics Export", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/analytics/export");
    });

    test("should display export options", async ({ page }) => {
        // Check page title
        await expect(page.locator("h1")).toContainText("Export");

        // Check format options
        await expect(page.getByText("CSV")).toBeVisible();
        await expect(page.getByText("JSON")).toBeVisible();

        // Check time period options
        await expect(page.getByText(/7 days/i)).toBeVisible();
        await expect(page.getByText(/30 days/i)).toBeVisible();
    });

    test("should toggle export format", async ({ page }) => {
        // Select JSON format
        await page.getByRole("button", { name: /json/i }).click();

        // Verify selection
        const jsonButton = page.getByRole("button", { name: /json/i });
        await expect(jsonButton).toHaveClass(/border-purple/);
    });

    test("should toggle time period", async ({ page }) => {
        // Select 90 days
        await page.getByRole("button", { name: /90 days/i }).click();

        // Verify selection
        await expect(page.getByRole("button", { name: /90 days/i })).toHaveClass(/bg-purple/);
    });

    test("should show export preview", async ({ page }) => {
        // Check preview section
        await expect(page.getByText("Export Preview")).toBeVisible();
    });

    test("should navigate back to analytics", async ({ page }) => {
        // Click back button
        await page.locator('a[href="/analytics"]').first().click();

        // Verify navigation
        await expect(page).toHaveURL("/analytics");
    });
});
