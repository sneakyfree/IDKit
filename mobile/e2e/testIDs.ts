/**
 * Test IDs for E2E Testing
 *
 * Centralized test IDs to ensure consistency between
 * the app components and E2E tests.
 */

export const TestIDs = {
  // Authentication
  Auth: {
    loginScreen: 'auth.login-screen',
    registerScreen: 'auth.register-screen',
    emailInput: 'auth.email-input',
    passwordInput: 'auth.password-input',
    confirmPasswordInput: 'auth.confirm-password-input',
    loginButton: 'auth.login-button',
    registerButton: 'auth.register-button',
    switchToRegister: 'auth.switch-to-register',
    switchToLogin: 'auth.switch-to-login',
    forgotPassword: 'auth.forgot-password',
    socialGoogle: 'auth.social-google',
    socialApple: 'auth.social-apple',
    biometricButton: 'auth.biometric-button',
    errorMessage: 'auth.error-message',
  },

  // Navigation
  Nav: {
    bottomNav: 'nav.bottom-nav',
    homeTab: 'nav.home-tab',
    searchTab: 'nav.search-tab',
    createTab: 'nav.create-tab',
    inboxTab: 'nav.inbox-tab',
    profileTab: 'nav.profile-tab',
    backButton: 'nav.back-button',
    headerTitle: 'nav.header-title',
  },

  // Feed
  Feed: {
    container: 'feed.container',
    item: 'feed.item',
    itemAtIndex: (index: number) => `feed.item-${index}`,
    likeButton: 'feed.like-button',
    commentButton: 'feed.comment-button',
    shareButton: 'feed.share-button',
    bookmarkButton: 'feed.bookmark-button',
    authorAvatar: 'feed.author-avatar',
    authorName: 'feed.author-name',
    contentText: 'feed.content-text',
    contentMedia: 'feed.content-media',
    refreshIndicator: 'feed.refresh-indicator',
    loadingSpinner: 'feed.loading-spinner',
    emptyState: 'feed.empty-state',
    errorState: 'feed.error-state',
  },

  // Content Creation
  Create: {
    screen: 'create.screen',
    textInput: 'create.text-input',
    characterCount: 'create.character-count',
    addMediaButton: 'create.add-media-button',
    addPollButton: 'create.add-poll-button',
    addScheduleButton: 'create.add-schedule-button',
    postButton: 'create.post-button',
    draftButton: 'create.draft-button',
    mediaPreview: 'create.media-preview',
    removeMediaButton: 'create.remove-media-button',
    pollOption: (index: number) => `create.poll-option-${index}`,
    addPollOption: 'create.add-poll-option',
    schedulePicker: 'create.schedule-picker',
  },

  // Profile
  Profile: {
    screen: 'profile.screen',
    avatar: 'profile.avatar',
    displayName: 'profile.display-name',
    username: 'profile.username',
    bio: 'profile.bio',
    followersCount: 'profile.followers-count',
    followingCount: 'profile.following-count',
    postsCount: 'profile.posts-count',
    editButton: 'profile.edit-button',
    followButton: 'profile.follow-button',
    unfollowButton: 'profile.unfollow-button',
    postsTab: 'profile.posts-tab',
    likesTab: 'profile.likes-tab',
    mediaTab: 'profile.media-tab',
    settingsButton: 'profile.settings-button',
  },

  // Search
  Search: {
    screen: 'search.screen',
    input: 'search.input',
    clearButton: 'search.clear-button',
    resultsContainer: 'search.results-container',
    resultItem: 'search.result-item',
    trendingSection: 'search.trending-section',
    trendingItem: 'search.trending-item',
    filterButton: 'search.filter-button',
    filterUsers: 'search.filter-users',
    filterPosts: 'search.filter-posts',
    filterTags: 'search.filter-tags',
  },

  // Inbox
  Inbox: {
    screen: 'inbox.screen',
    notificationItem: 'inbox.notification-item',
    messageItem: 'inbox.message-item',
    tabNotifications: 'inbox.tab-notifications',
    tabMessages: 'inbox.tab-messages',
    emptyState: 'inbox.empty-state',
    markAllRead: 'inbox.mark-all-read',
  },

  // Settings
  Settings: {
    screen: 'settings.screen',
    accountSection: 'settings.account-section',
    privacySection: 'settings.privacy-section',
    notificationsSection: 'settings.notifications-section',
    appearanceSection: 'settings.appearance-section',
    helpSection: 'settings.help-section',
    logoutButton: 'settings.logout-button',
    darkModeToggle: 'settings.dark-mode-toggle',
    pushNotificationsToggle: 'settings.push-notifications-toggle',
    emailNotificationsToggle: 'settings.email-notifications-toggle',
    privateAccountToggle: 'settings.private-account-toggle',
    deleteAccountButton: 'settings.delete-account-button',
  },

  // Common
  Common: {
    loadingSpinner: 'common.loading-spinner',
    errorBanner: 'common.error-banner',
    successBanner: 'common.success-banner',
    confirmModal: 'common.confirm-modal',
    confirmButton: 'common.confirm-button',
    cancelButton: 'common.cancel-button',
    closeButton: 'common.close-button',
    pullToRefresh: 'common.pull-to-refresh',
  },
} as const;
