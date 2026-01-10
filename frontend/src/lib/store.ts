/**
 * Zustand Store for IDKit
 *
 * Minimal global state management.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse, ProfileResponse } from "./api";

interface AuthState {
  user: UserResponse | null;
  profile: ProfileResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setUser: (user: UserResponse | null) => void;
  setProfile: (profile: ProfileResponse | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) =>
        set({ user, isAuthenticated: !!user, isLoading: false }),

      setProfile: (profile) => set({ profile }),

      setLoading: (isLoading) => set({ isLoading }),

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, profile: null, isAuthenticated: false });
      },
    }),
    {
      name: "idkit-auth",
      partialize: (state) => ({
        user: state.user,
        profile: state.profile,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Feed state
interface FeedState {
  activeTab: "for-you" | "following";
  setActiveTab: (tab: "for-you" | "following") => void;
}

export const useFeedStore = create<FeedState>((set) => ({
  activeTab: "for-you",
  setActiveTab: (activeTab) => set({ activeTab }),
}));

// Create modal state
interface CreateState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}

export const useCreateStore = create<CreateState>((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));

// Theme state
export type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
  initializeTheme: () => void;
}

const getSystemTheme = (): "light" | "dark" => {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

const resolveTheme = (theme: Theme): "light" | "dark" => {
  if (theme === "system") {
    return getSystemTheme();
  }
  return theme;
};

const applyTheme = (resolvedTheme: "light" | "dark") => {
  if (typeof document === "undefined") return;

  const root = document.documentElement;

  if (resolvedTheme === "dark") {
    root.classList.add("dark");
    root.classList.remove("light");
  } else {
    root.classList.add("light");
    root.classList.remove("dark");
  }

  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute(
      "content",
      resolvedTheme === "dark" ? "#000000" : "#ffffff"
    );
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "dark" as Theme,
      resolvedTheme: "dark" as "light" | "dark",

      setTheme: (theme: Theme) => {
        const resolved = resolveTheme(theme);
        applyTheme(resolved);
        set({ theme, resolvedTheme: resolved });
      },

      initializeTheme: () => {
        const { theme } = get();
        const resolved = resolveTheme(theme);
        applyTheme(resolved);
        set({ resolvedTheme: resolved });

        // Listen for system theme changes
        if (typeof window !== "undefined" && theme === "system") {
          const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
          const handler = (e: MediaQueryListEvent) => {
            const newResolved = e.matches ? "dark" : "light";
            applyTheme(newResolved);
            set({ resolvedTheme: newResolved });
          };
          mediaQuery.addEventListener("change", handler);
        }
      },
    }),
    {
      name: "idkit-theme",
      partialize: (state) => ({ theme: state.theme }),
    }
  )
);
