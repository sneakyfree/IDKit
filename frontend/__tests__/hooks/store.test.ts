import { act, renderHook } from "@testing-library/react";

// Reset zustand stores between tests
beforeEach(() => {
  jest.resetModules();
});

describe("useAuthStore", () => {
  it("should have default state", async () => {
    const { useAuthStore } = await import("@/lib/store");
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.profile).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it("should set user and update authentication state", async () => {
    const { useAuthStore } = await import("@/lib/store");
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: "1",
      email: "test@example.com",
      username: "testuser",
      display_name: "Test User",
      avatar_url: null,
      is_verified: false,
      is_premium: false,
      created_at: new Date().toISOString(),
    };

    act(() => {
      result.current.setUser(mockUser);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("should set profile", async () => {
    const { useAuthStore } = await import("@/lib/store");
    const { result } = renderHook(() => useAuthStore());

    const mockProfile = {
      id: "1",
      user_id: "1",
      bio: "Test bio",
      website: "https://test.com",
      location: "Test City",
      follower_count: 100,
      following_count: 50,
      post_count: 10,
      is_following: false,
    };

    act(() => {
      result.current.setProfile(mockProfile);
    });

    expect(result.current.profile).toEqual(mockProfile);
  });

  it("should logout and clear state", async () => {
    const { useAuthStore } = await import("@/lib/store");
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: "1",
      email: "test@example.com",
      username: "testuser",
      display_name: "Test User",
      avatar_url: null,
      is_verified: false,
      is_premium: false,
      created_at: new Date().toISOString(),
    };

    act(() => {
      result.current.setUser(mockUser);
    });

    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.profile).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});

describe("useFeedStore", () => {
  it("should have default active tab as for-you", async () => {
    const { useFeedStore } = await import("@/lib/store");
    const { result } = renderHook(() => useFeedStore());

    expect(result.current.activeTab).toBe("for-you");
  });

  it("should switch active tab", async () => {
    const { useFeedStore } = await import("@/lib/store");
    const { result } = renderHook(() => useFeedStore());

    act(() => {
      result.current.setActiveTab("following");
    });

    expect(result.current.activeTab).toBe("following");
  });
});

describe("useCreateStore", () => {
  it("should start closed", async () => {
    const { useCreateStore } = await import("@/lib/store");
    const { result } = renderHook(() => useCreateStore());

    expect(result.current.isOpen).toBe(false);
  });

  it("should open and close", async () => {
    const { useCreateStore } = await import("@/lib/store");
    const { result } = renderHook(() => useCreateStore());

    act(() => {
      result.current.open();
    });
    expect(result.current.isOpen).toBe(true);

    act(() => {
      result.current.close();
    });
    expect(result.current.isOpen).toBe(false);
  });
});

describe("useThemeStore", () => {
  it("should have default theme as dark", async () => {
    const { useThemeStore } = await import("@/lib/store");
    const { result } = renderHook(() => useThemeStore());

    expect(result.current.theme).toBe("dark");
    expect(result.current.resolvedTheme).toBe("dark");
  });

  it("should set theme to light", async () => {
    const { useThemeStore } = await import("@/lib/store");
    const { result } = renderHook(() => useThemeStore());

    act(() => {
      result.current.setTheme("light");
    });

    expect(result.current.theme).toBe("light");
    expect(result.current.resolvedTheme).toBe("light");
  });

  it("should handle system theme", async () => {
    const { useThemeStore } = await import("@/lib/store");
    const { result } = renderHook(() => useThemeStore());

    act(() => {
      result.current.setTheme("system");
    });

    expect(result.current.theme).toBe("system");
    // In tests, matchMedia mock returns dark for prefers-color-scheme: dark
    expect(result.current.resolvedTheme).toBe("dark");
  });
});
