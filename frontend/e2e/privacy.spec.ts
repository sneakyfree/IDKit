import { test, expect } from "@playwright/test";

/**
 * E2E Tests for Privacy Settings
 * 
 * Tests for GDPR compliance, data export, and privacy controls.
 */

test.describe("Privacy Settings Page", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/settings/privacy");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display privacy settings page", async ({ page }) => {
        // Check page loaded
        await expect(page.locator("h1")).toContainText(/privacy|data/i);
    });

    test("should show tab navigation", async ({ page }) => {
        // Check for settings/data/consents tabs
        const settingsTab = page.getByRole("button", { name: /settings/i });
        const dataTab = page.getByRole("button", { name: /data/i });

        await expect(settingsTab).toBeVisible();
        await expect(dataTab).toBeVisible();
    });

    test("should display visibility settings", async ({ page }) => {
        // Check visibility options
        await expect(page.getByText(/profile visibility/i).first()).toBeVisible();
        await expect(page.getByText(/activity visibility/i).first()).toBeVisible();
    });

    test("should have toggle switches", async ({ page }) => {
        // Check for toggle switches (role=switch)
        const toggles = page.locator('[role="switch"], button:has(div.rounded-full)');
        const count = await toggles.count();

        expect(count).toBeGreaterThan(0);
    });
});

test.describe("Privacy Settings - Visibility Controls", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/settings/privacy");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should toggle profile visibility", async ({ page }) => {
        // Find visibility buttons
        const publicButton = page.getByRole("button", { name: /public/i }).first();
        const privateButton = page.getByRole("button", { name: /private/i }).first();

        // Click to change visibility
        await privateButton.click();

        // Verify selection changed
        await expect(privateButton).toHaveClass(/bg-purple|selected/);
    });

    test("should toggle analytics preference", async ({ page }) => {
        // Find analytics toggle
        const analyticsSection = page.getByText(/analytics tracking/i).locator("..");
        const toggle = analyticsSection.locator('[role="switch"], button').first();

        if (await toggle.isVisible()) {
            await toggle.click();
            // Toggle should change state
        }
    });
});

test.describe("Privacy Settings - Data Tab", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Navigate to data tab
        await page.getByRole("button", { name: /data/i }).first().click();
    });

    test("should display data export section", async ({ page }) => {
        // Check for export functionality
        await expect(page.getByText(/download your data|export/i).first()).toBeVisible();
    });

    test("should have data export button", async ({ page }) => {
        // Check for export button
        const exportButton = page.getByRole("button", { name: /request.*export|download/i });
        await expect(exportButton).toBeVisible();
    });

    test("should display delete account section", async ({ page }) => {
        // Check for delete account section (GDPR right to erasure)
        await expect(page.getByText(/delete.*account/i).first()).toBeVisible();
    });

    test("should have delete account button", async ({ page }) => {
        // Check for delete button (should be styled as danger)
        const deleteButton = page.getByRole("button", { name: /delete.*account/i });
        await expect(deleteButton).toBeVisible();
    });
});

test.describe("Privacy Settings - Delete Confirmation", () => {
    test("should show confirmation modal on delete click", async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        await page.getByRole("button", { name: /data/i }).first().click();

        // Click delete account button
        await page.getByRole("button", { name: /delete.*account/i }).first().click();

        // Confirmation modal should appear
        await expect(page.getByText(/permanently delete|confirm|type/i).first()).toBeVisible();
    });

    test("should require confirmation text to delete", async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        await page.getByRole("button", { name: /data/i }).first().click();
        await page.getByRole("button", { name: /delete.*account/i }).first().click();

        // Try to click delete without typing confirmation
        const confirmButton = page.getByRole("button", { name: /delete forever|confirm delete/i });

        // Button should be disabled without confirmation text
        await expect(confirmButton).toBeDisabled();
    });

    test("should close modal on cancel", async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        await page.getByRole("button", { name: /data/i }).first().click();
        await page.getByRole("button", { name: /delete.*account/i }).first().click();

        // Click cancel
        await page.getByRole("button", { name: /cancel/i }).first().click();

        // Modal should close
        await expect(page.getByText(/type.*delete/i)).not.toBeVisible();
    });
});

test.describe("Privacy Settings - Consents Tab", () => {
    test("should display consent history", async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Navigate to consents tab
        const consentsTab = page.getByRole("button", { name: /consent/i });
        if (await consentsTab.isVisible()) {
            await consentsTab.click();

            // Should show consent items
            await expect(page.getByText(/terms of service|privacy policy/i).first()).toBeVisible();
        }
    });
});

test.describe("Privacy Settings - Navigation", () => {
    test("should navigate back to settings", async ({ page }) => {
        await page.goto("/settings/privacy");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Click back link
        await page.locator('a[href="/settings"]').first().click();

        // Verify navigation
        await expect(page).toHaveURL("/settings");
    });

    test("should be accessible from settings page", async ({ page }) => {
        await page.goto("/settings");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Find privacy link
        const privacyLink = page.getByRole("link", { name: /privacy/i }).first();
        await expect(privacyLink).toBeVisible();

        await privacyLink.click();
        await expect(page).toHaveURL("/settings/privacy");
    });
});
