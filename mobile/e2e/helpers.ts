/**
 * E2E Test Helpers
 *
 * Common utilities and helper functions for E2E tests.
 */

import { device, element, by, waitFor, expect } from 'detox';
import { TestIDs } from './testIDs';

/**
 * Wait for an element to be visible
 */
export async function waitForElement(
  testID: string,
  timeout: number = 5000
): Promise<void> {
  await waitFor(element(by.id(testID)))
    .toBeVisible()
    .withTimeout(timeout);
}

/**
 * Wait for an element to disappear
 */
export async function waitForElementToDisappear(
  testID: string,
  timeout: number = 5000
): Promise<void> {
  await waitFor(element(by.id(testID)))
    .not.toBeVisible()
    .withTimeout(timeout);
}

/**
 * Tap an element by test ID
 */
export async function tapElement(testID: string): Promise<void> {
  await element(by.id(testID)).tap();
}

/**
 * Type text into an input field
 */
export async function typeText(
  testID: string,
  text: string,
  replace: boolean = false
): Promise<void> {
  const el = element(by.id(testID));
  if (replace) {
    await el.clearText();
  }
  await el.typeText(text);
}

/**
 * Scroll to an element within a scrollable container
 */
export async function scrollToElement(
  elementID: string,
  scrollViewID: string,
  direction: 'up' | 'down' | 'left' | 'right' = 'down',
  pixels: number = 200
): Promise<void> {
  await waitFor(element(by.id(elementID)))
    .toBeVisible()
    .whileElement(by.id(scrollViewID))
    .scroll(pixels, direction);
}

/**
 * Pull to refresh on a scrollable element
 */
export async function pullToRefresh(scrollViewID: string): Promise<void> {
  await element(by.id(scrollViewID)).swipe('down', 'slow', 0.5);
}

/**
 * Check if an element contains text
 */
export async function expectElementText(
  testID: string,
  expectedText: string
): Promise<void> {
  await expect(element(by.id(testID))).toHaveText(expectedText);
}

/**
 * Check if element is visible
 */
export async function expectVisible(testID: string): Promise<void> {
  await expect(element(by.id(testID))).toBeVisible();
}

/**
 * Check if element is not visible
 */
export async function expectNotVisible(testID: string): Promise<void> {
  await expect(element(by.id(testID))).not.toBeVisible();
}

/**
 * Sleep for a specified duration (use sparingly)
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Login helper
 */
export async function login(
  email: string = 'test@example.com',
  password: string = 'password123'
): Promise<void> {
  await waitForElement(TestIDs.Auth.loginScreen);
  await typeText(TestIDs.Auth.emailInput, email);
  await typeText(TestIDs.Auth.passwordInput, password);
  await tapElement(TestIDs.Auth.loginButton);
  await waitForElementToDisappear(TestIDs.Auth.loginScreen);
}

/**
 * Logout helper
 */
export async function logout(): Promise<void> {
  await tapElement(TestIDs.Nav.profileTab);
  await waitForElement(TestIDs.Profile.screen);
  await tapElement(TestIDs.Profile.settingsButton);
  await waitForElement(TestIDs.Settings.screen);
  await scrollToElement(
    TestIDs.Settings.logoutButton,
    TestIDs.Settings.screen
  );
  await tapElement(TestIDs.Settings.logoutButton);
  await tapElement(TestIDs.Common.confirmButton);
  await waitForElement(TestIDs.Auth.loginScreen);
}

/**
 * Navigate to a tab
 */
export async function navigateToTab(
  tab: 'home' | 'search' | 'create' | 'inbox' | 'profile'
): Promise<void> {
  const tabMap = {
    home: TestIDs.Nav.homeTab,
    search: TestIDs.Nav.searchTab,
    create: TestIDs.Nav.createTab,
    inbox: TestIDs.Nav.inboxTab,
    profile: TestIDs.Nav.profileTab,
  };
  await tapElement(tabMap[tab]);
}

/**
 * Create a post
 */
export async function createPost(content: string): Promise<void> {
  await navigateToTab('create');
  await waitForElement(TestIDs.Create.screen);
  await typeText(TestIDs.Create.textInput, content);
  await tapElement(TestIDs.Create.postButton);
  await waitForElementToDisappear(TestIDs.Create.screen);
}

/**
 * Wait for feed to load
 */
export async function waitForFeedToLoad(): Promise<void> {
  await waitForElementToDisappear(TestIDs.Feed.loadingSpinner);
  await waitForElement(TestIDs.Feed.container);
}

/**
 * Interact with a feed item
 */
export async function likeFeedItem(index: number = 0): Promise<void> {
  await waitForElement(TestIDs.Feed.itemAtIndex(index));
  // Tap within the feed item on the like button
  await element(by.id(TestIDs.Feed.likeButton).withAncestor(
    by.id(TestIDs.Feed.itemAtIndex(index))
  )).tap();
}

/**
 * Follow a user from their profile
 */
export async function followUser(): Promise<void> {
  await waitForElement(TestIDs.Profile.screen);
  const followButton = element(by.id(TestIDs.Profile.followButton));
  if (await followButton.isVisible()) {
    await followButton.tap();
  }
}

/**
 * Search for content
 */
export async function search(query: string): Promise<void> {
  await navigateToTab('search');
  await waitForElement(TestIDs.Search.screen);
  await typeText(TestIDs.Search.input, query);
  await element(by.id(TestIDs.Search.input)).tapReturnKey();
  await waitForElement(TestIDs.Search.resultsContainer);
}

/**
 * Handle permission dialogs (iOS/Android)
 */
export async function handlePermissionDialog(
  allow: boolean = true
): Promise<void> {
  try {
    if (device.getPlatform() === 'ios') {
      const buttonLabel = allow ? 'Allow' : "Don't Allow";
      await element(by.label(buttonLabel)).tap();
    } else {
      const buttonLabel = allow ? 'ALLOW' : 'DENY';
      await element(by.text(buttonLabel)).tap();
    }
  } catch {
    // Dialog may not appear, that's OK
  }
}

/**
 * Take a screenshot with a descriptive name
 */
export async function takeScreenshot(name: string): Promise<void> {
  await device.takeScreenshot(name);
}

/**
 * Reload the app (useful for testing offline scenarios)
 */
export async function reloadApp(): Promise<void> {
  await device.reloadReactNative();
}

/**
 * Test network offline mode
 */
export async function setOfflineMode(offline: boolean): Promise<void> {
  if (device.getPlatform() === 'ios') {
    // iOS: Use airplane mode or mock
    // Note: This requires additional setup in the app
  } else {
    // Android: Use adb to toggle network
    // Note: This requires shell access
  }
  // For now, rely on app's mock network state
}
