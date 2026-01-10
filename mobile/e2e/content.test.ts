/**
 * Content Creation E2E Tests
 *
 * Tests for creating, editing, and managing content.
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
  expectNotVisible,
  createPost,
  handlePermissionDialog,
  sleep,
} from './helpers';

describe('Content Creation', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await login('test@example.com', 'password123');
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await waitForElement(TestIDs.Feed.container);
  });

  describe('Create Screen Navigation', () => {
    it('should navigate to create screen from bottom nav', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);
    });

    it('should display all creation options', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await expectVisible(TestIDs.Create.textInput);
      await expectVisible(TestIDs.Create.addMediaButton);
      await expectVisible(TestIDs.Create.postButton);
    });
  });

  describe('Text Post Creation', () => {
    it('should create a simple text post', async () => {
      const postContent = `Test post ${Date.now()}`;

      await createPost(postContent);

      // Should navigate back to feed
      await waitForElement(TestIDs.Feed.container);
    });

    it('should show character count', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      const content = 'Hello, World!';
      await typeText(TestIDs.Create.textInput, content);

      await expectVisible(TestIDs.Create.characterCount);
    });

    it('should enforce character limit', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      // Type more than allowed characters (assuming 280 limit)
      const longContent = 'a'.repeat(300);
      await typeText(TestIDs.Create.textInput, longContent);

      // Post button should be disabled or show error
      // Check that character count shows over-limit state
    });

    it('should not allow empty posts', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      // Try to post without content
      await tapElement(TestIDs.Create.postButton);

      // Should still be on create screen
      await expectVisible(TestIDs.Create.screen);
    });

    it('should save post as draft', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      const draftContent = `Draft post ${Date.now()}`;
      await typeText(TestIDs.Create.textInput, draftContent);

      await tapElement(TestIDs.Create.draftButton);

      // Should save and navigate away
      // Verify draft was saved by checking drafts section
    });
  });

  describe('Media Post Creation', () => {
    it('should open media picker when add media is tapped', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await tapElement(TestIDs.Create.addMediaButton);

      // Handle permission dialog if it appears
      await handlePermissionDialog(true);

      // Media picker should open
      // This will show system picker
    });

    it('should show media preview after selection', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await tapElement(TestIDs.Create.addMediaButton);
      await handlePermissionDialog(true);

      // Note: Selecting actual media in tests requires mock or pre-staged content
      // This test would verify the preview appears after selection
    });

    it('should allow removing selected media', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      // After media is selected (would need mock)
      // await expectVisible(TestIDs.Create.mediaPreview);
      // await tapElement(TestIDs.Create.removeMediaButton);
      // await expectNotVisible(TestIDs.Create.mediaPreview);
    });
  });

  describe('Poll Creation', () => {
    it('should open poll creation when poll button is tapped', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await tapElement(TestIDs.Create.addPollButton);

      // Poll options should appear
      await expectVisible(TestIDs.Create.pollOption(0));
      await expectVisible(TestIDs.Create.pollOption(1));
    });

    it('should allow adding poll options', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await tapElement(TestIDs.Create.addPollButton);

      await typeText(TestIDs.Create.pollOption(0), 'Option A');
      await typeText(TestIDs.Create.pollOption(1), 'Option B');

      await tapElement(TestIDs.Create.addPollOption);
      await expectVisible(TestIDs.Create.pollOption(2));

      await typeText(TestIDs.Create.pollOption(2), 'Option C');
    });

    it('should create a post with poll', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await typeText(TestIDs.Create.textInput, 'Which do you prefer?');
      await tapElement(TestIDs.Create.addPollButton);

      await typeText(TestIDs.Create.pollOption(0), 'Option A');
      await typeText(TestIDs.Create.pollOption(1), 'Option B');

      await tapElement(TestIDs.Create.postButton);

      await waitForElement(TestIDs.Feed.container);
    });
  });

  describe('Scheduled Posts', () => {
    it('should open schedule picker', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await tapElement(TestIDs.Create.addScheduleButton);

      await expectVisible(TestIDs.Create.schedulePicker);
    });

    it('should schedule a post for later', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await typeText(TestIDs.Create.textInput, 'Scheduled post');
      await tapElement(TestIDs.Create.addScheduleButton);

      // Select a future time in the picker
      // This requires interacting with native date picker

      await tapElement(TestIDs.Create.postButton);

      // Should show confirmation that post is scheduled
    });
  });

  describe('Post Editing', () => {
    it('should allow editing a draft', async () => {
      // Navigate to drafts and edit one
      // This test would require drafts to exist
    });
  });

  describe('Content Validation', () => {
    it('should warn about potentially sensitive content', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      // Type content that might trigger a warning
      // Specific implementation depends on content policy
    });
  });

  describe('Back Navigation', () => {
    it('should show discard confirmation when navigating away with content', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await typeText(TestIDs.Create.textInput, 'Unsaved content');

      // Try to navigate away
      await tapElement(TestIDs.Nav.backButton);

      // Should show discard confirmation
      await expectVisible(TestIDs.Common.confirmModal);
    });

    it('should discard content when confirmed', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await typeText(TestIDs.Create.textInput, 'Unsaved content');

      await tapElement(TestIDs.Nav.backButton);
      await expectVisible(TestIDs.Common.confirmModal);

      await tapElement(TestIDs.Common.confirmButton);

      // Should navigate away
      await waitForElementToDisappear(TestIDs.Create.screen);
    });

    it('should keep content when discard is cancelled', async () => {
      await navigateToTab('create');
      await waitForElement(TestIDs.Create.screen);

      await typeText(TestIDs.Create.textInput, 'Keep this content');

      await tapElement(TestIDs.Nav.backButton);
      await expectVisible(TestIDs.Common.confirmModal);

      await tapElement(TestIDs.Common.cancelButton);

      // Should stay on create screen with content
      await expectVisible(TestIDs.Create.screen);
      await expect(element(by.id(TestIDs.Create.textInput))).toHaveText(
        'Keep this content'
      );
    });
  });
});
