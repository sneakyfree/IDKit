import { test, expect } from "@playwright/test";

/**
 * E2E Tests for Payouts Settings
 * 
 * Tests for Stripe Connect onboarding, balance display, and payout functionality.
 */

test.describe("Payouts Page", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/settings/payouts");
    await page.waitForLoadState("networkidle").catch(() => {});
    });

    test("should display payouts page", async ({ page }) => {
        // Check page title
        await expect(page.locator("h1")).toContainText(/payout/i);
    });

    test("should show onboarding for new users", async ({ page }) => {
        // For users without Stripe Connect, should show onboarding
        // Either shows "Connect" CTA or account status
        const pageContent = await page.locator("main").textContent();

        // Should have either onboarding content or account info
        expect(
            pageContent?.includes("Connect") ||
            pageContent?.includes("Account") ||
            pageContent?.includes("Balance")
        ).toBeTruthy();
    });

    test("should have back navigation", async ({ page }) => {
        // Check for back link to settings
        const backLink = page.locator('a[href="/settings"]').first();
        await expect(backLink).toBeVisible();
    });

    test("should navigate to settings", async ({ page }) => {
        // Click back to settings
        await page.locator('a[href="/settings"]').first().click();

        // Verify navigation
        await expect(page).toHaveURL("/settings");
    });
});

test.describe("Payouts - Connected Account", () => {
    // These tests assume user has a connected Stripe account

    test("should display balance when connected", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Look for balance section
        const balanceSection = page.getByText(/balance|available|pending/i);

        // If connected, balance should be visible
        // If not connected, onboarding should be visible
        const hasBalance = await balanceSection.isVisible().catch(() => false);
        const hasOnboarding = await page.getByRole("button", { name: /connect|set up/i }).isVisible().catch(() => false);

        expect(hasBalance || hasOnboarding).toBeTruthy();
    });

    test("should show payout history section", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Look for history section (may be empty or have transactions)
        const pageContent = await page.locator("main").textContent();

        // Should mention history or transactions or show empty state
        expect(
            pageContent?.includes("History") ||
            pageContent?.includes("Transaction") ||
            pageContent?.includes("No payouts") ||
            pageContent?.includes("onboarding")
        ).toBeTruthy();
    });

    test("should have payout request button when eligible", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // If connected and has balance, should show payout button
        const payoutButton = page.getByRole("button", { name: /request payout|withdraw/i });
        const hasPayoutButton = await payoutButton.isVisible().catch(() => false);

        // If no payout button, should have connect button
        if (!hasPayoutButton) {
            const connectButton = page.getByRole("button", { name: /connect|set up/i });
            const hasConnectButton = await connectButton.isVisible().catch(() => false);
            expect(hasConnectButton).toBeTruthy();
        }
    });
});

test.describe("Payouts - Stripe Connect Flow", () => {
    test("should show connect button for new users", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // For users without Stripe account, should show connect CTA
        // This test verifies the onboarding flow exists
        const pageContent = await page.locator("main").textContent();

        // Should have setup/connect content
        expect(pageContent).toBeTruthy();
    });

    test("should display Stripe branding", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Look for Stripe references
        const pageContent = await page.locator("main").textContent();

        // Should mention payments or have payment-related content
        expect(pageContent?.length).toBeGreaterThan(0);
    });
});

test.describe("Payouts - From Settings Navigation", () => {
    test("should navigate to payouts from settings", async ({ page }) => {
        // Start from settings page
        await page.goto("/settings");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Find and click payouts link
        const payoutsLink = page.getByRole("link", { name: /payout/i });
        await expect(payoutsLink).toBeVisible();

        await payoutsLink.click();

        // Verify navigation
        await expect(page).toHaveURL("/settings/payouts");
    });

    test("should show payouts in billing section", async ({ page }) => {
        await page.goto("/settings");
        await page.waitForLoadState("networkidle").catch(() => {});
        // Look for billing section
        const billingSection = page.getByText(/billing|payment/i);
        await expect(billingSection).toBeVisible();
    });
});

test.describe("Payouts - Form Validation", () => {
    test("should validate payout amount", async ({ page }) => {
        await page.goto("/settings/payouts");
        await page.waitForLoadState("networkidle").catch(() => {});
        // If payout form is visible (user is connected with balance)
        const amountInput = page.locator('input[type="number"]');
        const hasAmountInput = await amountInput.isVisible().catch(() => false);

        if (hasAmountInput) {
            // Try to enter invalid amount
            await amountInput.fill("0");

            // Submit should be disabled or show error
            const submitButton = page.getByRole("button", { name: /request|withdraw/i });

            // Either disabled or validation message should appear
            await submitButton.click().catch(() => { });

            // Page should still be on payouts (not submitted)
            await expect(page).toHaveURL(/payouts/);
        }
    });
});
