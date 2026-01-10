/**
 * Authentication E2E Tests
 *
 * Tests for login, registration, and logout flows.
 */

import { device, element, by, expect } from 'detox';
import { TestIDs } from './testIDs';
import {
  waitForElement,
  typeText,
  tapElement,
  login,
  logout,
  expectVisible,
  expectNotVisible,
  waitForElementToDisappear,
} from './helpers';

describe('Authentication', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  describe('Login Flow', () => {
    it('should display the login screen on app launch', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await expectVisible(TestIDs.Auth.emailInput);
      await expectVisible(TestIDs.Auth.passwordInput);
      await expectVisible(TestIDs.Auth.loginButton);
    });

    it('should show error for invalid credentials', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await typeText(TestIDs.Auth.emailInput, 'invalid@example.com');
      await typeText(TestIDs.Auth.passwordInput, 'wrongpassword');
      await tapElement(TestIDs.Auth.loginButton);

      await waitForElement(TestIDs.Auth.errorMessage);
      await expect(element(by.id(TestIDs.Auth.errorMessage))).toHaveText(
        'Invalid email or password'
      );
    });

    it('should login successfully with valid credentials', async () => {
      await login('test@example.com', 'password123');
      await waitForElement(TestIDs.Feed.container);
      await expectVisible(TestIDs.Nav.bottomNav);
    });

    it('should show validation error for empty email', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await typeText(TestIDs.Auth.passwordInput, 'password123');
      await tapElement(TestIDs.Auth.loginButton);

      await waitForElement(TestIDs.Auth.errorMessage);
    });

    it('should show validation error for empty password', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await typeText(TestIDs.Auth.emailInput, 'test@example.com');
      await tapElement(TestIDs.Auth.loginButton);

      await waitForElement(TestIDs.Auth.errorMessage);
    });

    it('should navigate to forgot password screen', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.forgotPassword);

      // Verify forgot password screen is shown
      await expect(element(by.text('Reset Password'))).toBeVisible();
    });
  });

  describe('Registration Flow', () => {
    it('should navigate to registration screen', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.switchToRegister);

      await waitForElement(TestIDs.Auth.registerScreen);
      await expectVisible(TestIDs.Auth.emailInput);
      await expectVisible(TestIDs.Auth.passwordInput);
      await expectVisible(TestIDs.Auth.confirmPasswordInput);
      await expectVisible(TestIDs.Auth.registerButton);
    });

    it('should show error when passwords do not match', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.switchToRegister);
      await waitForElement(TestIDs.Auth.registerScreen);

      await typeText(TestIDs.Auth.emailInput, 'newuser@example.com');
      await typeText(TestIDs.Auth.passwordInput, 'password123');
      await typeText(TestIDs.Auth.confirmPasswordInput, 'password456');
      await tapElement(TestIDs.Auth.registerButton);

      await waitForElement(TestIDs.Auth.errorMessage);
      await expect(element(by.id(TestIDs.Auth.errorMessage))).toHaveText(
        'Passwords do not match'
      );
    });

    it('should register successfully with valid data', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.switchToRegister);
      await waitForElement(TestIDs.Auth.registerScreen);

      const uniqueEmail = `user${Date.now()}@example.com`;
      await typeText(TestIDs.Auth.emailInput, uniqueEmail);
      await typeText(TestIDs.Auth.passwordInput, 'SecurePass123!');
      await typeText(TestIDs.Auth.confirmPasswordInput, 'SecurePass123!');
      await tapElement(TestIDs.Auth.registerButton);

      // Should redirect to feed after successful registration
      await waitForElement(TestIDs.Feed.container);
    });

    it('should show error for already registered email', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.switchToRegister);
      await waitForElement(TestIDs.Auth.registerScreen);

      await typeText(TestIDs.Auth.emailInput, 'test@example.com');
      await typeText(TestIDs.Auth.passwordInput, 'password123');
      await typeText(TestIDs.Auth.confirmPasswordInput, 'password123');
      await tapElement(TestIDs.Auth.registerButton);

      await waitForElement(TestIDs.Auth.errorMessage);
      await expect(element(by.id(TestIDs.Auth.errorMessage))).toHaveText(
        'Email already registered'
      );
    });

    it('should switch back to login from registration', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.switchToRegister);
      await waitForElement(TestIDs.Auth.registerScreen);

      await tapElement(TestIDs.Auth.switchToLogin);
      await waitForElement(TestIDs.Auth.loginScreen);
    });
  });

  describe('Logout Flow', () => {
    it('should logout successfully', async () => {
      // First login
      await login('test@example.com', 'password123');
      await waitForElement(TestIDs.Feed.container);

      // Then logout
      await logout();
      await waitForElement(TestIDs.Auth.loginScreen);
    });

    it('should clear session data on logout', async () => {
      // Login
      await login('test@example.com', 'password123');
      await waitForElement(TestIDs.Feed.container);

      // Logout
      await logout();

      // Reload app and verify still logged out
      await device.reloadReactNative();
      await waitForElement(TestIDs.Auth.loginScreen);
    });
  });

  describe('Session Persistence', () => {
    it('should stay logged in after app restart', async () => {
      // Login
      await login('test@example.com', 'password123');
      await waitForElement(TestIDs.Feed.container);

      // Restart app
      await device.terminateApp();
      await device.launchApp();

      // Should still be logged in
      await waitForElement(TestIDs.Feed.container);
    });
  });

  describe('Social Login', () => {
    it('should display social login options', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await expectVisible(TestIDs.Auth.socialGoogle);
      await expectVisible(TestIDs.Auth.socialApple);
    });

    // Note: Full social login tests require mock OAuth or test accounts
    it('should open Google login when tapped', async () => {
      await waitForElement(TestIDs.Auth.loginScreen);
      await tapElement(TestIDs.Auth.socialGoogle);

      // This will typically open a web view or system browser
      // For testing purposes, we just verify it doesn't crash
    });
  });
});
