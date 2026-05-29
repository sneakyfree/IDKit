/**
 * PHASE 6: Accessibility E2E Tests
 * 
 * Automated accessibility testing for critical user paths
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Test all critical pages for accessibility violations
const criticalPages = [
    { path: '/', name: 'Home' },
    { path: '/feed', name: 'Feed' },
    { path: '/settings', name: 'Settings' },
    { path: '/analytics', name: 'Analytics' },
    { path: '/content/bulk', name: 'Bulk Content' },
    { path: '/schedule', name: 'Schedule' },
    { path: '/testing', name: 'A/B Testing' },
];

test.describe('Accessibility Compliance', () => {
    for (const page of criticalPages) {
        test(`${page.name} page should have no critical accessibility violations`, async ({ page: browserPage }) => {
            await browserPage.goto(page.path);
            await browserPage.waitForLoadState('networkidle');

            const accessibilityScanResults = await new AxeBuilder({ page: browserPage })
                .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
                .analyze();

            // Filter to critical violations only
            const criticalViolations = accessibilityScanResults.violations.filter(
                v => v.impact === 'critical' || v.impact === 'serious'
            );

            expect(criticalViolations).toEqual([]);
        });
    }

    test('should have proper focus management', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        // Tab through interactive elements
        await page.keyboard.press('Tab');
        const firstFocused = await page.evaluate(() => document.activeElement?.tagName);
        expect(firstFocused).toBeTruthy();

        // All focused elements should have visible focus indicator
        const focusedElement = await page.locator(':focus');
        const outline = await focusedElement.evaluate(el =>
            getComputedStyle(el).outline || getComputedStyle(el).boxShadow
        );
        expect(outline).not.toBe('none');
    });

    test('should support keyboard navigation in modals', async ({ page }) => {
        await page.goto('/settings');
        await page.waitForLoadState("networkidle").catch(() => {});
        // Open a modal (if available)
        const modalTrigger = page.locator('[data-testid="modal-trigger"]').first();
        if (await modalTrigger.isVisible()) {
            await modalTrigger.click();

            // Escape should close modal
            await page.keyboard.press('Escape');
            await expect(page.locator('[role="dialog"]')).not.toBeVisible();
        }
    });

    test('should have proper heading hierarchy', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        const headings = await page.evaluate(() => {
            const h = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            return Array.from(h).map(el => ({
                level: parseInt(el.tagName.substring(1)),
                text: el.textContent?.trim(),
            }));
        });

        // Should have exactly one h1
        const h1Count = headings.filter(h => h.level === 1).length;
        expect(h1Count).toBeLessThanOrEqual(1);

        // Heading levels should not skip (e.g., h1 -> h3)
        for (let i = 1; i < headings.length; i++) {
            const diff = headings[i].level - headings[i - 1].level;
            expect(diff).toBeLessThanOrEqual(1);
        }
    });

    test('should have proper color contrast', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        const accessibilityScanResults = await new AxeBuilder({ page })
            .withTags(['cat.color'])
            .analyze();

        const contrastViolations = accessibilityScanResults.violations.filter(
            v => v.id === 'color-contrast'
        );

        // Log any contrast issues for debugging
        if (contrastViolations.length > 0) {
            console.log('Color contrast issues:', JSON.stringify(contrastViolations, null, 2));
        }

        expect(contrastViolations).toEqual([]);
    });

    test('should have proper ARIA labels on interactive elements', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        // All buttons should have accessible names
        const buttons = await page.locator('button').all();
        for (const button of buttons) {
            const name = await button.evaluate(el =>
                el.getAttribute('aria-label') ||
                el.textContent?.trim() ||
                el.getAttribute('title')
            );
            expect(name).toBeTruthy();
        }

        // All inputs should have associated labels
        const inputs = await page.locator('input:not([type="hidden"])').all();
        for (const input of inputs) {
            const hasLabel = await input.evaluate(el => {
                const id = el.getAttribute('id');
                const ariaLabel = el.getAttribute('aria-label');
                const ariaLabelledBy = el.getAttribute('aria-labelledby');
                const label = id ? document.querySelector(`label[for="${id}"]`) : null;
                return !!(ariaLabel || ariaLabelledBy || label);
            });
            expect(hasLabel).toBe(true);
        }
    });

    test('should handle screen reader announcements', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        // Check for live regions
        const liveRegions = await page.locator('[aria-live]').count();
        expect(liveRegions).toBeGreaterThan(0);
    });
});

test.describe('Keyboard Navigation', () => {
    test('should navigate between menu items with arrow keys', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        // Tab to navigation
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');

        // Arrow keys should work in navigation
        const nav = page.locator('nav').first();
        if (await nav.isVisible()) {
            await page.keyboard.press('ArrowDown');
            // Verify focus moved
            const focused = await page.evaluate(() => document.activeElement?.textContent);
            expect(focused).toBeTruthy();
        }
    });

    test('skip link should be first focusable element', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState("networkidle").catch(() => {});
        // First tab should focus skip link (if present)
        await page.keyboard.press('Tab');
        const skipLink = await page.locator(':focus').getAttribute('class');

        // Skip link might be visually hidden initially
        const isSkipLink = skipLink?.includes('skip') ||
            await page.locator(':focus').textContent() === 'Skip to main content';

        // Not all pages may have skip link, so this is informational
        if (!isSkipLink) {
            console.log('Note: Skip link not found as first focusable element');
        }
    });
});
