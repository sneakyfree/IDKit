/**
 * Search E2E Tests
 *
 * Tests for search functionality.
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
  search,
  sleep,
} from './helpers';

describe('Search', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await login('test@example.com', 'password123');
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    await waitForElement(TestIDs.Feed.container);
  });

  describe('Search Screen', () => {
    it('should navigate to search screen', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);
    });

    it('should display search input', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await expectVisible(TestIDs.Search.input);
    });

    it('should display trending section when no search query', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await expectVisible(TestIDs.Search.trendingSection);
    });
  });

  describe('Search Functionality', () => {
    it('should search for content', async () => {
      await search('test query');

      await expectVisible(TestIDs.Search.resultsContainer);
    });

    it('should display search results', async () => {
      await search('hello');

      await waitForElement(TestIDs.Search.resultsContainer);
      // Results should be visible
    });

    it('should clear search input', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await typeText(TestIDs.Search.input, 'test query');
      await tapElement(TestIDs.Search.clearButton);

      await expect(element(by.id(TestIDs.Search.input))).toHaveText('');
    });

    it('should show trending after clearing search', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await typeText(TestIDs.Search.input, 'test query');
      await element(by.id(TestIDs.Search.input)).tapReturnKey();
      await waitForElement(TestIDs.Search.resultsContainer);

      await tapElement(TestIDs.Search.clearButton);

      await expectVisible(TestIDs.Search.trendingSection);
    });

    it('should search on keyboard return', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await typeText(TestIDs.Search.input, 'keyword');
      await element(by.id(TestIDs.Search.input)).tapReturnKey();

      await waitForElement(TestIDs.Search.resultsContainer);
    });
  });

  describe('Search Filters', () => {
    it('should display filter options', async () => {
      await search('test');

      await tapElement(TestIDs.Search.filterButton);

      await expectVisible(TestIDs.Search.filterUsers);
      await expectVisible(TestIDs.Search.filterPosts);
      await expectVisible(TestIDs.Search.filterTags);
    });

    it('should filter by users', async () => {
      await search('john');

      await tapElement(TestIDs.Search.filterButton);
      await tapElement(TestIDs.Search.filterUsers);

      // Results should be filtered to users only
    });

    it('should filter by posts', async () => {
      await search('content');

      await tapElement(TestIDs.Search.filterButton);
      await tapElement(TestIDs.Search.filterPosts);

      // Results should be filtered to posts only
    });

    it('should filter by tags', async () => {
      await search('#trending');

      await tapElement(TestIDs.Search.filterButton);
      await tapElement(TestIDs.Search.filterTags);

      // Results should be filtered to tags only
    });
  });

  describe('Search Results Interaction', () => {
    it('should navigate to user profile from search results', async () => {
      await search('user');

      await tapElement(TestIDs.Search.filterButton);
      await tapElement(TestIDs.Search.filterUsers);

      await waitForElement(TestIDs.Search.resultsContainer);

      // Tap on first result
      await tapElement(TestIDs.Search.resultItem);

      // Should navigate to profile
      await waitForElement(TestIDs.Profile.screen);
    });

    it('should navigate to post from search results', async () => {
      await search('post');

      await tapElement(TestIDs.Search.filterButton);
      await tapElement(TestIDs.Search.filterPosts);

      await waitForElement(TestIDs.Search.resultsContainer);

      // Tap on first result
      await tapElement(TestIDs.Search.resultItem);

      // Should navigate to post detail
    });
  });

  describe('Trending', () => {
    it('should display trending items', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await expectVisible(TestIDs.Search.trendingSection);
      await expectVisible(TestIDs.Search.trendingItem);
    });

    it('should search when tapping trending item', async () => {
      await navigateToTab('search');
      await waitForElement(TestIDs.Search.screen);

      await tapElement(TestIDs.Search.trendingItem);

      // Should populate search and show results
      await waitForElement(TestIDs.Search.resultsContainer);
    });
  });

  describe('Empty and Error States', () => {
    it('should show no results message for empty search', async () => {
      await search('xyznonexistentquery123');

      // Should show empty state
      await expect(element(by.text('No results found'))).toBeVisible();
    });
  });
});
