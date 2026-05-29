import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright Configuration for IDKit E2E Tests
 *
 * Run with:
 *   npx playwright test              # Run all tests
 *   npx playwright test --ui         # Run with UI mode
 *   npx playwright test --headed     # Run with browser visible
 *   npx playwright test --project=chromium  # Run only in Chrome
 */

export default defineConfig({
  // Test directory
  testDir: "./e2e",

  // Timeout for each test
  timeout: 30000,

  // Timeout for each expect() call
  expect: {
    timeout: 5000,
  },

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if test.only is left in the code
  forbidOnly: !!process.env.CI,

  // Retry failed tests on CI
  retries: process.env.CI ? 2 : 0,

  // Number of workers
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["list"],
    ...(process.env.CI ? [["github"] as const] : []),
  ],

  // Global setup/teardown
  globalSetup: undefined,
  globalTeardown: undefined,

  // Shared settings for all projects
  use: {
    // Base URL for navigation
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",

    // Collect trace when retrying failed test
    trace: "on-first-retry",

    // Take screenshot on failure
    screenshot: "only-on-failure",

    // Record video on failure
    video: "on-first-retry",

    // Action timeout
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 15000,
  },

  // Projects for different browsers
  projects: [
    // Setup project for authentication
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/,
    },

    // Desktop browsers
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: ".auth/user.json",
      },
      dependencies: ["setup"],
    },
    {
      name: "firefox",
      use: {
        ...devices["Desktop Firefox"],
      },
      dependencies: ["setup"],
    },
    {
      name: "webkit",
      use: {
        ...devices["Desktop Safari"],
      },
      dependencies: ["setup"],
    },

    // Mobile browsers
    {
      name: "mobile-chrome",
      use: {
        ...devices["Pixel 5"],
      },
      dependencies: ["setup"],
    },
    {
      name: "mobile-safari",
      use: {
        ...devices["iPhone 13"],
      },
      dependencies: ["setup"],
    },

    // Accessibility testing project
    {
      name: "accessibility",
      use: {
        ...devices["Desktop Chrome"],
      },
      testMatch: /.*\.a11y\.spec\.ts/,
    },
  ],
});
