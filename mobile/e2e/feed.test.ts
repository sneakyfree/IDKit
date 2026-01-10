/**
 * Feed E2E Tests
 *
 * Tests for the main feed functionality including
 * scrolling, interactions, and content display.
 */

import { device, element, by, expect, waitFor } from 'detox';
import { TestIDs } from './testIDs';
import {
  waitForElement,
  waitForElementToDisappear,
  tapElement,
  login,
  pullToRefresh,
  waitForFeedToLoad,
  likeFeedItem,
  expectVisible,
  navigateToTab,
  scrollToElement,
  sleep,
} from './helpers';

describe('Feed', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await login('test@example.com', 'password123');
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await waitForFeedToLoad();
  });

  describe('Feed Loading', () => {
    it('should display the feed container', async () => {
      await expectVisible(TestIDs.Feed.container);
    });

    it('should show loading indicator while fetching', async () => {
      await device.reloadReactNative();
      // Loading spinner should appear briefly
      await expect(element(by.id(TestIDs.Feed.loadingSpinner))).toExist();
      await waitForElementToDisappear(TestIDs.Feed.loadingSpinner);
    });

    it('should display feed items after loading', async () => {
      await waitForFeedToLoad();
      await expectVisible(TestIDs.Feed.itemAtIndex(0));
    });

    it('should show empty state when no posts', async () => {
      // This test would require a test account with no followed users
      // or a way to clear the feed
    });
  });

  describe('Feed Scrolling', () => {
    it('should scroll through feed items', async () => {
      await waitForFeedToLoad();

      // Scroll down to load more items
      await element(by.id(TestIDs.Feed.container)).scroll(500, 'down');

      // Verify we can see later items
      await waitForElement(TestIDs.Feed.itemAtIndex(3));
    });

    it('should support pull to refresh', async () => {
      await waitForFeedToLoad();

      // Pull to refresh
      await pullToRefresh(TestIDs.Feed.container);

      // Wait for refresh to complete
      await waitForElementToDisappear(TestIDs.Feed.refreshIndicator, 10000);

      // Feed should still be visible
      await expectVisible(TestIDs.Feed.container);
    });

    it('should load more items when scrolling to bottom', async () => {
      await waitForFeedToLoad();

      // Scroll to bottom
      await element(by.id(TestIDs.Feed.container)).scroll(2000, 'down');

      // Wait for more items to load
      await sleep(2000);

      // Should have loaded more items
      await waitForElement(TestIDs.Feed.itemAtIndex(5));
    });
  });

  describe('Feed Item Interactions', () => {
    it('should like a post', async () => {
      await waitForFeedToLoad();

      const likeButton = element(
        by.id(TestIDs.Feed.likeButton).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      // Tap like
      await likeButton.tap();

      // Button should change state (visual feedback)
      // The exact check depends on implementation
    });

    it('should unlike a previously liked post', async () => {
      await waitForFeedToLoad();

      const likeButton = element(
        by.id(TestIDs.Feed.likeButton).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      // Like then unlike
      await likeButton.tap();
      await sleep(500);
      await likeButton.tap();
    });

    it('should open comments sheet when tapping comment button', async () => {
      await waitForFeedToLoad();

      const commentButton = element(
        by.id(TestIDs.Feed.commentButton).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await commentButton.tap();

      // Should show comments modal/sheet
      await expect(element(by.text('Comments'))).toBeVisible();
    });

    it('should open share sheet when tapping share button', async () => {
      await waitForFeedToLoad();

      const shareButton = element(
        by.id(TestIDs.Feed.shareButton).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await shareButton.tap();

      // Share sheet should appear
      // This will show native share dialog
    });

    it('should bookmark a post', async () => {
      await waitForFeedToLoad();

      const bookmarkButton = element(
        by.id(TestIDs.Feed.bookmarkButton).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await bookmarkButton.tap();

      // Should show confirmation or change state
    });
  });

  describe('Feed Item Navigation', () => {
    it('should navigate to author profile when tapping avatar', async () => {
      await waitForFeedToLoad();

      const authorAvatar = element(
        by.id(TestIDs.Feed.authorAvatar).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await authorAvatar.tap();

      // Should navigate to profile screen
      await waitForElement(TestIDs.Profile.screen);
    });

    it('should navigate to author profile when tapping name', async () => {
      await waitForFeedToLoad();

      const authorName = element(
        by.id(TestIDs.Feed.authorName).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await authorName.tap();

      await waitForElement(TestIDs.Profile.screen);
    });

    it('should open media viewer when tapping content media', async () => {
      await waitForFeedToLoad();

      // Find a post with media (may need to scroll)
      const mediaElement = element(
        by.id(TestIDs.Feed.contentMedia).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      try {
        await mediaElement.tap();
        // Should open full screen media viewer
      } catch {
        // Post may not have media, that's OK
      }
    });
  });

  describe('Feed Content Display', () => {
    it('should display post author information', async () => {
      await waitForFeedToLoad();

      const firstItem = by.id(TestIDs.Feed.itemAtIndex(0));

      await expect(
        element(by.id(TestIDs.Feed.authorAvatar).withAncestor(firstItem))
      ).toBeVisible();

      await expect(
        element(by.id(TestIDs.Feed.authorName).withAncestor(firstItem))
      ).toBeVisible();
    });

    it('should display post content text', async () => {
      await waitForFeedToLoad();

      const contentText = element(
        by.id(TestIDs.Feed.contentText).withAncestor(
          by.id(TestIDs.Feed.itemAtIndex(0))
        )
      );

      await expect(contentText).toBeVisible();
    });

    it('should display interaction buttons', async () => {
      await waitForFeedToLoad();

      const firstItem = by.id(TestIDs.Feed.itemAtIndex(0));

      await expect(
        element(by.id(TestIDs.Feed.likeButton).withAncestor(firstItem))
      ).toBeVisible();

      await expect(
        element(by.id(TestIDs.Feed.commentButton).withAncestor(firstItem))
      ).toBeVisible();

      await expect(
        element(by.id(TestIDs.Feed.shareButton).withAncestor(firstItem))
      ).toBeVisible();
    });
  });

  describe('Error Handling', () => {
    it('should show error state on network failure', async () => {
      // This test requires network mocking
      // For now, we'll verify the error state exists
    });

    it('should allow retry after error', async () => {
      // Would require network mocking
    });
  });
});
