import { act, renderHook } from "@testing-library/react";
import {
  useAuthStore,
  useFeedStore,
  useCreateStore,
  useThemeStore,
} from "@/lib/store";

// Reset store state between tests (without resetting modules which breaks React)
beforeEach(() => {
  // Reset each store to initial state
  useAuthStore.setState({
    user: null,
    profile: null,
    isAuthenticated: false,
    isLoading: true,
  });
  useFeedStore.setState({ activeTab: "for-you" });
  useCreateStore.setState({ isOpen: false });
  useThemeStore.setState({ theme: "dark", resolvedTheme: "dark" });
});

describe("useAuthStore", () => {
  it("should have default state", () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.profile).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it("should set user and update authentication state", () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: "1",
      email: "test@example.com",
      full_name: "Test User",
      avatar_url: null,
      is_verified: false,
      subscription_tier: "free",
    };

    act(() => {
      result.current.setUser(mockUser);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("should set profile", () => {
    const { result } = renderHook(() => useAuthStore());

    const mockProfile = {
      id: "1",
      user_id: "1",
      username: "testuser",
      display_name: "Test User",
      bio: "Test bio",
      avatar_url: null,
      cover_image_url: null,
      website_url: "https://test.com",
      follower_count: 100,
      following_count: 50,
      post_count: 10,
      is_verified: false,
      niche_tags: [],
      is_following: false,
    };

    act(() => {
      result.current.setProfile(mockProfile);
    });

    expect(result.current.profile).toEqual(mockProfile);
  });

  it("should logout and clear state", () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: "1",
      email: "test@example.com",
      full_name: "Test User",
      avatar_url: null,
      is_verified: false,
      subscription_tier: "free",
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
  it("should have default active tab as for-you", () => {
    const { result } = renderHook(() => useFeedStore());

    expect(result.current.activeTab).toBe("for-you");
  });

  it("should switch active tab", () => {
    const { result } = renderHook(() => useFeedStore());

    act(() => {
      result.current.setActiveTab("following");
    });

    expect(result.current.activeTab).toBe("following");
  });
});

describe("useCreateStore", () => {
  it("should start closed", () => {
    const { result } = renderHook(() => useCreateStore());

    expect(result.current.isOpen).toBe(false);
  });

  it("should open and close", () => {
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
  it("should have default theme as dark", () => {
    const { result } = renderHook(() => useThemeStore());

    expect(result.current.theme).toBe("dark");
    expect(result.current.resolvedTheme).toBe("dark");
  });

  it("should set theme to light", () => {
    const { result } = renderHook(() => useThemeStore());

    act(() => {
      result.current.setTheme("light");
    });

    expect(result.current.theme).toBe("light");
    expect(result.current.resolvedTheme).toBe("light");
  });

  it("should handle system theme", () => {
    const { result } = renderHook(() => useThemeStore());

    act(() => {
      result.current.setTheme("system");
    });

    expect(result.current.theme).toBe("system");
    // In tests, matchMedia mock returns dark for prefers-color-scheme: dark
    expect(result.current.resolvedTheme).toBe("dark");
  });
});

