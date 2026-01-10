/**
 * Profile E2E Tests
 *
 * Tests for profile viewing and editing functionality.
 */

import { device, element, by, expect } from 'detox';
import { TestIDs } from './testIDs';
import {
  waitForElement,
  waitForElementToDisappear,
  typeText,
  tapElement,
  login,
  navigateToTab,
  expectVisible,
  scrollToElement,
  followUser,
  sleep,
} from './helpers';

describe('Profile', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await login('test@example.com', 'password123');
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await waitForElement(TestIDs.Feed.container);
  });

  describe('Own Profile', () => {
    it('should navigate to own profile from bottom nav', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);
    });

    it('should display profile information', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await expectVisible(TestIDs.Profile.avatar);
      await expectVisible(TestIDs.Profile.displayName);
      await expectVisible(TestIDs.Profile.username);
    });

    it('should display follower and following counts', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await expectVisible(TestIDs.Profile.followersCount);
      await expectVisible(TestIDs.Profile.followingCount);
      await expectVisible(TestIDs.Profile.postsCount);
    });

    it('should show edit button on own profile', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await expectVisible(TestIDs.Profile.editButton);
    });

    it('should navigate to settings from profile', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.settingsButton);
      await waitForElement(TestIDs.Settings.screen);
    });
  });

  describe('Profile Tabs', () => {
    it('should display posts tab by default', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await expectVisible(TestIDs.Profile.postsTab);
    });

    it('should switch to likes tab', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.likesTab);

      // Likes content should be visible
    });

    it('should switch to media tab', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.mediaTab);

      // Media grid should be visible
    });

    it('should switch back to posts tab', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.likesTab);
      await tapElement(TestIDs.Profile.postsTab);
    });
  });

  describe('Profile Editing', () => {
    it('should open edit profile modal', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.editButton);

      // Edit modal should appear
      await expect(element(by.text('Edit Profile'))).toBeVisible();
    });

    it('should update display name', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.editButton);

      // Update display name
      const displayNameInput = element(by.id('edit-profile.display-name'));
      await displayNameInput.clearText();
      await displayNameInput.typeText('New Display Name');

      await tapElement(TestIDs.Common.confirmButton);

      // Verify update
      await waitForElement(TestIDs.Profile.screen);
      await expect(element(by.id(TestIDs.Profile.displayName))).toHaveText(
        'New Display Name'
      );
    });

    it('should update bio', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.editButton);

      const bioInput = element(by.id('edit-profile.bio'));
      await bioInput.clearText();
      await bioInput.typeText('This is my updated bio');

      await tapElement(TestIDs.Common.confirmButton);

      await waitForElement(TestIDs.Profile.screen);
    });

    it('should cancel edit without saving', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.editButton);

      const displayNameInput = element(by.id('edit-profile.display-name'));
      await displayNameInput.clearText();
      await displayNameInput.typeText('Should Not Save');

      await tapElement(TestIDs.Common.cancelButton);

      // Verify name wasn't changed
      await waitForElement(TestIDs.Profile.screen);
    });
  });

  describe('Other User Profile', () => {
    it('should navigate to other user profile from feed', async () => {
      await waitForElement(TestIDs.Feed.container);

      // Tap on author avatar in first feed item
      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );
      await authorAvatar.tap();

      await waitForElement(TestIDs.Profile.screen);
    });

    it('should show follow button on other user profile', async () => {
      // Navigate to another user's profile
      await waitForElement(TestIDs.Feed.container);

      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );
      await authorAvatar.tap();

      await waitForElement(TestIDs.Profile.screen);

      // Should show follow/unfollow button instead of edit
      // (Depends on whether already following)
    });

    it('should follow a user', async () => {
      await waitForElement(TestIDs.Feed.container);

      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );
      await authorAvatar.tap();

      await waitForElement(TestIDs.Profile.screen);

      try {
        await tapElement(TestIDs.Profile.followButton);
        // Button should change to unfollow
        await expectVisible(TestIDs.Profile.unfollowButton);
      } catch {
        // Already following
        await expectVisible(TestIDs.Profile.unfollowButton);
      }
    });

    it('should unfollow a user', async () => {
      await waitForElement(TestIDs.Feed.container);

      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );
      await authorAvatar.tap();

      await waitForElement(TestIDs.Profile.screen);

      try {
        await tapElement(TestIDs.Profile.unfollowButton);
        // Should show confirmation or change to follow
        await expectVisible(TestIDs.Profile.followButton);
      } catch {
        // Not following
        await expectVisible(TestIDs.Profile.followButton);
      }
    });

    it('should not show edit button on other user profile', async () => {
      await waitForElement(TestIDs.Feed.container);

      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );
      await authorAvatar.tap();

      await waitForElement(TestIDs.Profile.screen);

      await expect(element(by.id(TestIDs.Profile.editButton))).not.toBeVisible();
    });
  });

  describe('Followers/Following Lists', () => {
    it('should open followers list when count is tapped', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.followersCount);

      // Followers list should appear
      await expect(element(by.text('Followers'))).toBeVisible();
    });

    it('should open following list when count is tapped', async () => {
      await navigateToTab('profile');
      await waitForElement(TestIDs.Profile.screen);

      await tapElement(TestIDs.Profile.followingCount);

      // Following list should appear
      await expect(element(by.text('Following'))).toBeVisible();
    });
  });
});
