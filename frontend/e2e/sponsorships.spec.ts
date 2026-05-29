import { test, expect } from "@playwright/test";

/**
 * Sponsorship Management E2E Tests
 *
 * Tests sponsor tracking, deals, and deliverables.
 */

test.describe("Sponsorship Management", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/sponsorships");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display sponsorship page", async ({ page }) => {
        await expect(page).toHaveTitle(/Sponsorship|IDKit/);
        await expect(page.getByRole("heading", { name: /Sponsorship Management/i }).first()).toBeVisible();
    });

    test("should show stats cards", async ({ page }) => {
        await expect(page.getByText(/Total Revenue/i).first()).toBeVisible();
        await expect(page.getByText(/Active Deals/i).first()).toBeVisible();
        await expect(page.getByText(/Pending Payments/i).first()).toBeVisible();
        await expect(page.getByText(/Sponsors/i).first()).toBeVisible();
    });

    test("should have status filter buttons", async ({ page }) => {
        await expect(page.getByRole("button", { name: /^all$/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /active/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /negotiating/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /completed/i }).first()).toBeVisible();
    });

    test("should open add sponsor modal", async ({ page }) => {
        await page.getByRole("button", { name: /Add Sponsor/i }).first().click();
        await expect(page.getByRole("heading", { name: /Add Sponsor/i }).first()).toBeVisible();
        await expect(page.getByLabel(/Company Name/i)).toBeVisible();
    });

    test("should add a new sponsor", async ({ page }) => {
        await page.getByRole("button", { name: /Add Sponsor/i }).first().click();

        await page.getByLabel(/Company Name/i).fill("Test Brand Inc");
        await page.getByLabel(/Industry/i).fill("Technology");

        await page.getByRole("button", { name: /Add Sponsor$/i }).first().click();

        // Modal should close
        await expect(page.getByRole("heading", { name: /Add Sponsor/i })).not.toBeVisible();
    });

    test("should filter sponsors by status", async ({ page }) => {
        // Wait for initial load
        await page.waitForTimeout(1000);

        // Click negotiating filter
        await page.getByRole("button", { name: /negotiating/i }).first().click();
        await expect(page.getByRole("button", { name: /negotiating/i }).first()).toHaveClass(/bg-purple/);
    });
});
