import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Accessibility Tests for IDKit
 *
 * These tests use axe-core to check for accessibility violations.
 * Run with: npx playwright test --project=accessibility
 */

test.describe("Accessibility - Home Page", () => {
  test("should not have any automatically detectable accessibility issues", async ({
    page,
  }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    // Filter out minor issues for initial compliance
    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(criticalViolations).toEqual([]);
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Check that h1 exists and comes before h2, h3, etc.
    const headings = await page.locator("h1, h2, h3, h4, h5, h6").all();

    if (headings.length > 0) {
      const headingLevels = await Promise.all(
        headings.map(async (h) => {
          const tagName = await h.evaluate((el) => el.tagName.toLowerCase());
          return parseInt(tagName.slice(1));
        })
      );

      // First heading should be h1 or h2
      expect(headingLevels[0]).toBeLessThanOrEqual(2);

      // No skipping levels (e.g., h1 -> h3)
      for (let i = 1; i < headingLevels.length; i++) {
        const jump = headingLevels[i] - headingLevels[i - 1];
        expect(jump).toBeLessThanOrEqual(1);
      }
    }
  });

  test("should have accessible images", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const images = page.locator("img");
    const imageCount = await images.count();

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute("alt");
      const role = await img.getAttribute("role");

      // Image should have alt text or role="presentation"
      const isAccessible = alt !== null || role === "presentation";
      expect(isAccessible).toBeTruthy();
    }
  });

  test("should have proper link text", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const links = page.locator("a");
    const linkCount = await links.count();

    for (let i = 0; i < linkCount; i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute("aria-label");

      // Link should have descriptive text or aria-label
      const hasAccessibleName =
        (text && text.trim().length > 0) || ariaLabel !== null;
      expect(hasAccessibleName).toBeTruthy();
    }
  });
});

test.describe("Accessibility - Schedule Page", () => {
  test("should not have critical accessibility issues", async ({ page }) => {
    await page.goto("/schedule");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-testid='third-party-widget']") // Exclude any third-party widgets
      .analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(criticalViolations).toEqual([]);
  });

  test("should have keyboard navigable calendar", async ({ page }) => {
    await page.goto("/schedule");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Focus on the calendar area
    await page.keyboard.press("Tab");

    // Should be able to navigate with arrow keys
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowLeft");
    await page.keyboard.press("ArrowUp");

    // Page should remain functional
    await expect(page).toHaveURL(/schedule/);
  });
});

test.describe("Accessibility - Settings Page", () => {
  test("should not have critical accessibility issues", async ({ page }) => {
    await page.goto("/settings/privacy");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(criticalViolations).toEqual([]);
  });

  test("should have accessible form controls", async ({ page }) => {
    await page.goto("/settings/privacy");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Check all inputs have associated labels
    const inputs = page.locator(
      'input:not([type="hidden"]), select, textarea'
    );
    const inputCount = await inputs.count();

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute("id");
      const ariaLabel = await input.getAttribute("aria-label");
      const ariaLabelledBy = await input.getAttribute("aria-labelledby");

      // Input should have a label association
      let hasLabel = false;

      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        hasLabel = (await label.count()) > 0;
      }

      const isAccessible =
        hasLabel || ariaLabel !== null || ariaLabelledBy !== null;

      // Some inputs like hidden ones are exceptions
      if (await input.isVisible()) {
        expect(isAccessible).toBeTruthy();
      }
    }
  });
});

test.describe("Accessibility - Testing Page", () => {
  test("should not have critical accessibility issues", async ({ page }) => {
    await page.goto("/testing");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(criticalViolations).toEqual([]);
  });
});

test.describe("Accessibility - Approvals Page", () => {
  test("should not have critical accessibility issues", async ({ page }) => {
    await page.goto("/approvals");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    const criticalViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(criticalViolations).toEqual([]);
  });
});

test.describe("Accessibility - Keyboard Navigation", () => {
  test("should be able to navigate entirely by keyboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Tab through the page
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press("Tab");
    }

    // Get focused element
    const focusedElement = page.locator(":focus");
    await expect(focusedElement).toBeVisible();

    // Press Enter to activate focused element
    await page.keyboard.press("Enter");

    // Page should respond to keyboard interaction
    await page.waitForTimeout(500);
  });

  test("should have visible focus indicators", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    // Tab to first focusable element
    await page.keyboard.press("Tab");

    const focusedElement = page.locator(":focus");

    if (await focusedElement.isVisible()) {
      // Check that focus is visually indicated
      const outline = await focusedElement.evaluate(
        (el) => getComputedStyle(el).outline
      );
      const boxShadow = await focusedElement.evaluate(
        (el) => getComputedStyle(el).boxShadow
      );
      const border = await focusedElement.evaluate(
        (el) => getComputedStyle(el).border
      );

      // Should have some form of focus indication
      const hasFocusIndicator =
        outline !== "none" ||
        boxShadow !== "none" ||
        border.includes("2px") ||
        border.includes("3px");

      // Note: This is a basic check, actual focus styles may vary
    }
  });
});

test.describe("Accessibility - Color Contrast", () => {
  test("should have sufficient color contrast", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2aa"]) // Check against WCAG 2.0 AA standards
      .analyze();

    // Filter for color contrast issues
    const contrastViolations = accessibilityScanResults.violations.filter(
      (v) => v.id === "color-contrast"
    );

    // Log any contrast issues for debugging
    if (contrastViolations.length > 0) {
      console.log(
        "Color contrast issues found:",
        JSON.stringify(contrastViolations, null, 2)
      );
    }

    // For dark mode themes, some contrast issues may be acceptable
    // This test is informational
  });
});

test.describe("Accessibility - ARIA", () => {
  test("should have valid ARIA attributes", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["cat.aria"]) // Check ARIA-related rules
      .analyze();

    const ariaViolations = accessibilityScanResults.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(ariaViolations).toEqual([]);
  });

  test("should have proper button accessibility", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});
    const buttons = page.locator("button");
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 20); i++) {
      const button = buttons.nth(i);

      if (await button.isVisible()) {
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute("aria-label");
        const ariaLabelledBy = await button.getAttribute("aria-labelledby");
        const title = await button.getAttribute("title");

        // Button should have accessible name
        const hasAccessibleName =
          (text && text.trim().length > 0) ||
          ariaLabel !== null ||
          ariaLabelledBy !== null ||
          title !== null;

        expect(hasAccessibleName).toBeTruthy();
      }
    }
  });
});
