/**
 * TASK 5.3.1: Dark Mode Theme System
 * 
 * Theme management with system preference detection and persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
    theme: Theme;
    resolvedTheme: 'light' | 'dark';
    setTheme: (theme: Theme) => void;
}

// Detect system preference
function getSystemTheme(): 'light' | 'dark' {
    if (typeof window === 'undefined') return 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Apply theme to document
function applyTheme(resolvedTheme: 'light' | 'dark') {
    if (typeof document === 'undefined') return;

    document.documentElement.setAttribute('data-theme', resolvedTheme);

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.setAttribute('content', resolvedTheme === 'dark' ? '#0a0a0a' : '#ffffff');
    }
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set, get) => ({
            theme: 'system',
            resolvedTheme: 'dark',

            setTheme: (theme: Theme) => {
                const resolvedTheme = theme === 'system' ? getSystemTheme() : theme;
                applyTheme(resolvedTheme);
                set({ theme, resolvedTheme });
            },
        }),
        {
            name: 'idkit-theme',
            onRehydrateStorage: () => (state) => {
                if (state) {
                    const resolvedTheme = state.theme === 'system' ? getSystemTheme() : state.theme;
                    applyTheme(resolvedTheme);
                    state.resolvedTheme = resolvedTheme;
                }
            },
        }
    )
);

// Initialize theme on load
export function initializeTheme() {
    if (typeof window === 'undefined') return;

    const stored = localStorage.getItem('idkit-theme');
    let theme: Theme = 'system';

    if (stored) {
        try {
            const parsed = JSON.parse(stored);
            theme = parsed.state?.theme || 'system';
        } catch {
            theme = 'system';
        }
    }

    const resolvedTheme = theme === 'system' ? getSystemTheme() : theme;
    applyTheme(resolvedTheme);

    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
        const currentTheme = useThemeStore.getState().theme;
        if (currentTheme === 'system') {
            const newResolved = e.matches ? 'dark' : 'light';
            applyTheme(newResolved);
            useThemeStore.setState({ resolvedTheme: newResolved });
        }
    });
}

// React hook for theme
export function useTheme() {
    const { theme, resolvedTheme, setTheme } = useThemeStore();
    return { theme, resolvedTheme, setTheme };
}

// CSS variable definitions for themes
export const themeVariables = {
    light: {
        '--bg-primary': '#ffffff',
        '--bg-secondary': '#f5f5f5',
        '--bg-tertiary': '#e5e5e5',
        '--text-primary': '#000000',
        '--text-secondary': '#666666',
        '--text-tertiary': '#999999',
        '--border': '#e0e0e0',
        '--border-focus': '#8b5cf6',
        '--accent': '#8b5cf6',
        '--accent-hover': '#7c3aed',
        '--success': '#22c55e',
        '--warning': '#f59e0b',
        '--error': '#ef4444',
        '--card': '#ffffff',
        '--card-hover': '#f9fafb',
        '--shadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
    },
    dark: {
        '--bg-primary': '#0a0a0a',
        '--bg-secondary': '#1a1a1a',
        '--bg-tertiary': '#2a2a2a',
        '--text-primary': '#ffffff',
        '--text-secondary': '#a0a0a0',
        '--text-tertiary': '#666666',
        '--border': '#2a2a2a',
        '--border-focus': '#a78bfa',
        '--accent': '#a78bfa',
        '--accent-hover': '#8b5cf6',
        '--success': '#4ade80',
        '--warning': '#fbbf24',
        '--error': '#f87171',
        '--card': '#111111',
        '--card-hover': '#1a1a1a',
        '--shadow': '0 1px 3px rgba(0, 0, 0, 0.3)',
    },
};
