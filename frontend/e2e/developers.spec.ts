import { test, expect } from "@playwright/test";

/**
 * Developer Portal E2E Tests
 *
 * Tests API key management and developer documentation.
 */

test.describe("Developer Portal", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/developers");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display developer portal page", async ({ page }) => {
        await expect(page).toHaveTitle(/Developer Portal|IDKit/);
        await expect(page.getByRole("heading", { name: /Developer Portal/i }).first()).toBeVisible();
    });

    test("should show API keys tab by default", async ({ page }) => {
        await expect(page.getByRole("button", { name: /API Keys/i }).first()).toHaveClass(/bg-purple/);
    });

    test("should switch between tabs", async ({ page }) => {
        // API Keys tab
        await expect(page.getByRole("button", { name: /API Keys/i }).first()).toBeVisible();

        // API Docs tab
        await page.getByRole("button", { name: /API Docs/i }).first().click();
        await expect(page.getByText(/Base URL/i).first()).toBeVisible();

        // SDKs tab
        await page.getByRole("button", { name: /SDKs/i }).first().click();
        await expect(page.getByText(/JavaScript/i).first()).toBeVisible();
        await expect(page.getByText(/Python/i).first()).toBeVisible();
    });

    test("should open create API key modal", async ({ page }) => {
        await page.getByRole("button", { name: /Create API Key/i }).first().click();
        await expect(page.getByRole("heading", { name: /Create API Key/i }).first()).toBeVisible();
        await expect(page.getByLabel(/Key Name/i)).toBeVisible();
    });

    test("should display SDK installation commands", async ({ page }) => {
        await page.getByRole("button", { name: /SDKs/i }).first().click();
        await expect(page.getByText("npm install @idkit/sdk").first()).toBeVisible();
        await expect(page.getByText("pip install idkit").first()).toBeVisible();
    });

    test("should display API documentation endpoints", async ({ page }) => {
        await page.getByRole("button", { name: /API Docs/i }).first().click();
        await expect(page.getByText("/api/v1/content").first()).toBeVisible();
        await expect(page.getByText("/api/v1/analytics").first()).toBeVisible();
    });
});
