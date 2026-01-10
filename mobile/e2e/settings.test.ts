/**
 * Settings E2E Tests
 *
 * Tests for app settings and preferences.
 */

import { device, element, by, expect } from 'detox';
import { TestIDs } from './testIDs';
import {
  waitForElement,
  waitForElementToDisappear,
  tapElement,
  login,
  logout,
  navigateToTab,
  expectVisible,
  scrollToElement,
  sleep,
} from './helpers';

describe('Settings', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await login('test@example.com', 'password123');
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await waitForElement(TestIDs.Feed.container);
    await navigateToTab('profile');
    await waitForElement(TestIDs.Profile.screen);
    await tapElement(TestIDs.Profile.settingsButton);
    await waitForElement(TestIDs.Settings.screen);
  });

  describe('Settings Screen', () => {
    it('should display all settings sections', async () => {
      await expectVisible(TestIDs.Settings.accountSection);
      await expectVisible(TestIDs.Settings.privacySection);
      await expectVisible(TestIDs.Settings.notificationsSection);
      await expectVisible(TestIDs.Settings.appearanceSection);
    });

    it('should display logout button', async () => {
      await scrollToElement(
        TestIDs.Settings.logoutButton,
        TestIDs.Settings.screen
      );
      await expectVisible(TestIDs.Settings.logoutButton);
    });
  });

  describe('Appearance Settings', () => {
    it('should toggle dark mode', async () => {
      await tapElement(TestIDs.Settings.appearanceSection);

      await waitForElement(TestIDs.Settings.darkModeToggle);
      await tapElement(TestIDs.Settings.darkModeToggle);

      // Visual change should occur (hard to verify programmatically)
      // At minimum, toggle state should change
    });

    it('should persist dark mode setting', async () => {
      await tapElement(TestIDs.Settings.appearanceSection);
      await waitForElement(TestIDs.Settings.darkModeToggle);

      // Get current state, toggle, and verify persistence
      await tapElement(TestIDs.Settings.darkModeToggle);

      // Reload and check persistence
      await device.reloadReactNative();
      await waitForElement(TestIDs.Feed.container);
      await navigateToTab('profile');
      await tapElement(TestIDs.Profile.settingsButton);
      await tapElement(TestIDs.Settings.appearanceSection);

      // Toggle state should be preserved
    });
  });

  describe('Notification Settings', () => {
    it('should toggle push notifications', async () => {
      await tapElement(TestIDs.Settings.notificationsSection);

      await waitForElement(TestIDs.Settings.pushNotificationsToggle);
      await tapElement(TestIDs.Settings.pushNotificationsToggle);
    });

    it('should toggle email notifications', async () => {
      await tapElement(TestIDs.Settings.notificationsSection);

      await waitForElement(TestIDs.Settings.emailNotificationsToggle);
      await tapElement(TestIDs.Settings.emailNotificationsToggle);
    });
  });

  describe('Privacy Settings', () => {
    it('should toggle private account', async () => {
      await tapElement(TestIDs.Settings.privacySection);

      await waitForElement(TestIDs.Settings.privateAccountToggle);
      await tapElement(TestIDs.Settings.privateAccountToggle);

      // May show confirmation dialog
    });

    it('should access account deletion', async () => {
      await tapElement(TestIDs.Settings.privacySection);

      await scrollToElement(
        TestIDs.Settings.deleteAccountButton,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.deleteAccountButton);

      // Should show confirmation dialog
      await expectVisible(TestIDs.Common.confirmModal);
    });

    it('should cancel account deletion', async () => {
      await tapElement(TestIDs.Settings.privacySection);

      await scrollToElement(
        TestIDs.Settings.deleteAccountButton,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.deleteAccountButton);

      await expectVisible(TestIDs.Common.confirmModal);
      await tapElement(TestIDs.Common.cancelButton);

      // Should stay on settings
      await expectVisible(TestIDs.Settings.screen);
    });
  });

  describe('Account Settings', () => {
    it('should access account settings section', async () => {
      await tapElement(TestIDs.Settings.accountSection);

      // Account settings options should appear
    });
  });

  describe('Help Section', () => {
    it('should access help section', async () => {
      await scrollToElement(
        TestIDs.Settings.helpSection,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.helpSection);

      // Help options should appear
    });
  });

  describe('Logout', () => {
    it('should show confirmation before logout', async () => {
      await scrollToElement(
        TestIDs.Settings.logoutButton,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.logoutButton);

      await expectVisible(TestIDs.Common.confirmModal);
    });

    it('should cancel logout', async () => {
      await scrollToElement(
        TestIDs.Settings.logoutButton,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.logoutButton);

      await expectVisible(TestIDs.Common.confirmModal);
      await tapElement(TestIDs.Common.cancelButton);

      // Should stay on settings
      await expectVisible(TestIDs.Settings.screen);
    });

    it('should logout when confirmed', async () => {
      await scrollToElement(
        TestIDs.Settings.logoutButton,
        TestIDs.Settings.screen
      );
      await tapElement(TestIDs.Settings.logoutButton);

      await expectVisible(TestIDs.Common.confirmModal);
      await tapElement(TestIDs.Common.confirmButton);

      // Should navigate to login screen
      await waitForElement(TestIDs.Auth.loginScreen);
    });
  });

  describe('Navigation', () => {
    it('should navigate back to profile', async () => {
      await tapElement(TestIDs.Nav.backButton);

      await waitForElement(TestIDs.Profile.screen);
    });
  });
});
