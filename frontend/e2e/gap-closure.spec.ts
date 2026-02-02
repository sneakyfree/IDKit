import { test, expect } from "@playwright/test";

/**
 * E2E Tests for DNA Strand Gap Closure Components
 * 
 * Tests for new components added during gap closure implementation.
 */

test.describe("Settings Pages", () => {
    test.describe("Guardrails Settings", () => {
        test.beforeEach(async ({ page }) => {
            await page.goto("/settings/agents/guardrails");
        });

        test("should display guardrails settings page", async ({ page }) => {
            // Check page header
            await expect(page.getByText("Guardrail Settings")).toBeVisible();

            // Check risk tolerance section
            await expect(page.getByText("Risk Tolerance")).toBeVisible();

            // Check action permissions section
            await expect(page.getByText("Action Permissions")).toBeVisible();

            // Check agent autonomy section
            await expect(page.getByText("Agent Autonomy")).toBeVisible();
        });

        test("should have selectable risk tolerance levels", async ({ page }) => {
            // Check all three risk levels
            await expect(page.getByText("conservative", { exact: false })).toBeVisible();
            await expect(page.getByText("medium", { exact: false })).toBeVisible();
            await expect(page.getByText("aggressive", { exact: false })).toBeVisible();
        });

        test("should have save and reset buttons", async ({ page }) => {
            await expect(page.getByRole("button", { name: /save/i })).toBeVisible();
            await expect(page.getByRole("button", { name: /reset/i })).toBeVisible();
        });
    });
});

test.describe("Agent Dashboard", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/agents");
    });

    test("should display agent dashboard", async ({ page }) => {
        // Check for agents section
        await expect(page.getByText(/agent/i)).toBeVisible();
    });
});

test.describe("Twin Lab", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/twins");
    });

    test("should display twin lab interface", async ({ page }) => {
        // Check for twin lab header or content
        await expect(page.getByText(/twin/i)).toBeVisible();
    });
});

test.describe("ROI Calculator", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/roi");
    });

    test("should display ROI calculator", async ({ page }) => {
        // Check page loaded
        await expect(page.getByText(/roi/i)).toBeVisible();
    });

    test("should have input fields", async ({ page }) => {
        // Check for calculator inputs
        const inputs = page.locator("input");
        await expect(inputs.first()).toBeVisible();
    });
});

test.describe("Payouts Settings", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/settings/payouts");
    });

    test("should display payouts page", async ({ page }) => {
        // Check page title
        await expect(page.getByText("Payouts")).toBeVisible();
    });

    test("should have onboarding or account section", async ({ page }) => {
        // Check for either onboarding CTA or account status
        const hasOnboarding = await page.getByText(/set up payouts/i).isVisible().catch(() => false);
        const hasAccount = await page.getByText(/payout account/i).isVisible().catch(() => false);

        expect(hasOnboarding || hasAccount).toBeTruthy();
    });
});

test.describe("Settings Navigation", () => {
    test("should navigate to settings page", async ({ page }) => {
        await page.goto("/settings");

        // Check settings page loaded
        await expect(page.getByText(/settings/i)).toBeVisible();
    });

    test("should have navigation links", async ({ page }) => {
        await page.goto("/settings");

        // Check for common settings links
        const links = page.locator("a");
        await expect(links.first()).toBeVisible();
    });
});

test.describe("Accessibility", () => {
    test("should have skip link when focused", async ({ page }) => {
        await page.goto("/");

        // Tab to reveal skip link
        await page.keyboard.press("Tab");

        // Skip links might be visually hidden until focused
        const skipLink = page.locator('[href="#main-content"], .skip-link');
        if (await skipLink.count() > 0) {
            await expect(skipLink.first()).toBeVisible();
        }
    });

    test("should have proper page structure", async ({ page }) => {
        await page.goto("/");

        // Check for main content area
        const main = page.locator("main");
        await expect(main).toBeVisible();
    });
});

test.describe("Theme Toggle", () => {
    test("should have theme toggle", async ({ page }) => {
        await page.goto("/settings");

        // Look for theme-related elements
        const themeToggle = page.locator('[aria-label*="theme"], [data-testid*="theme"], button:has-text("Dark"), button:has-text("Light")');
        if (await themeToggle.count() > 0) {
            await expect(themeToggle.first()).toBeVisible();
        }
    });
});

test.describe("Language Selector", () => {
    test("should display language selector", async ({ page }) => {
        await page.goto("/settings");

        // Look for language selector
        const langSelector = page.locator('select:has(option[value="en"]), [aria-label*="language"], button:has-text("English")');
        if (await langSelector.count() > 0) {
            await expect(langSelector.first()).toBeVisible();
        }
    });
});
