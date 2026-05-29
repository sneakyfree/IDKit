import { test, expect } from "@playwright/test";

/**
 * Contract Management E2E Tests
 *
 * Tests contract listing, creation, and management flows.
 */

test.describe("Contract Management", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/contracts");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display contracts page", async ({ page }) => {
        await expect(page).toHaveTitle(/Contract|IDKit/);
        await expect(page.getByRole("heading", { name: /Contract Management/i }).first()).toBeVisible();
    });

    test("should show stats cards", async ({ page }) => {
        await expect(page.getByText(/Active Contracts/i).first()).toBeVisible();
        await expect(page.getByText(/Pending Signature/i).first()).toBeVisible();
        await expect(page.getByText(/Total Contract Value/i).first()).toBeVisible();
    });

    test("should have status filter buttons", async ({ page }) => {
        await expect(page.getByRole("button", { name: /^all$/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /draft/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /pending/i }).first()).toBeVisible();
        await expect(page.getByRole("button", { name: /signed/i }).first()).toBeVisible();
    });

    test("should open create contract modal", async ({ page }) => {
        await page.getByRole("button", { name: /New Contract/i }).first().click();
        await expect(page.getByRole("heading", { name: /Create Contract/i }).first()).toBeVisible();
        await expect(page.getByLabel(/Contract Title/i)).toBeVisible();
        await expect(page.getByLabel(/Type/i)).toBeVisible();
    });

    test("should create a new contract", async ({ page }) => {
        await page.getByRole("button", { name: /New Contract/i }).first().click();

        await page.getByLabel(/Contract Title/i).fill("Test Sponsorship Deal");
        await page.getByLabel(/Start Date/i).fill("2026-02-01");

        await page.getByRole("button", { name: /^Create$/i }).first().click();

        // Modal should close
        await expect(page.getByRole("heading", { name: /Create Contract/i })).not.toBeVisible();
    });

    test("should filter contracts by status", async ({ page }) => {
        // Wait for initial load
        await page.waitForTimeout(1000);

        // Click pending filter
        await page.getByRole("button", { name: /pending/i }).first().click();
        await expect(page.getByRole("button", { name: /pending/i }).first()).toHaveClass(/bg-purple/);
    });
});
