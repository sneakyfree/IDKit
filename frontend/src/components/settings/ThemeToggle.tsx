"use client";

import { useEffect, useState } from "react";
import { useThemeStore, Theme } from "@/lib/store";

interface ThemeToggleProps {
  variant?: "dropdown" | "buttons" | "switch";
  showLabels?: boolean;
  className?: string;
}

const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: "light", label: "Light", icon: "sun" },
  { value: "dark", label: "Dark", icon: "moon" },
  { value: "system", label: "System", icon: "monitor" },
];

function SunIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

function MoonIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
      />
    </svg>
  );
}

function MonitorIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
      />
    </svg>
  );
}

function ThemeIcon({
  theme,
  className,
}: {
  theme: Theme;
  className?: string;
}) {
  switch (theme) {
    case "light":
      return <SunIcon className={className} />;
    case "dark":
      return <MoonIcon className={className} />;
    case "system":
      return <MonitorIcon className={className} />;
  }
}

export function ThemeToggle({
  variant = "buttons",
  showLabels = true,
  className = "",
}: ThemeToggleProps) {
  const { theme, setTheme, initializeTheme } = useThemeStore();
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    initializeTheme();
  }, [initializeTheme]);

  if (!mounted) {
    return null;
  }

  if (variant === "switch") {
    // Simple dark/light toggle switch
    const isDark = theme === "dark" || (theme === "system" &&
      (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches));

    return (
      <button
        onClick={() => setTheme(isDark ? "light" : "dark")}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          isDark ? "bg-purple-600" : "bg-gray-300"
        } ${className}`}
        aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      >
        <span
          className={`inline-flex h-4 w-4 transform items-center justify-center rounded-full bg-white transition-transform ${
            isDark ? "translate-x-6" : "translate-x-1"
          }`}
        >
          {isDark ? (
            <MoonIcon className="h-3 w-3 text-purple-600" />
          ) : (
            <SunIcon className="h-3 w-3 text-yellow-500" />
          )}
        </span>
      </button>
    );
  }

  if (variant === "dropdown") {
    return (
      <div className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
          aria-label="Select theme"
        >
          <ThemeIcon theme={theme} className="w-5 h-5 text-gray-300" />
          {showLabels && (
            <span className="text-white capitalize">{theme}</span>
          )}
          <svg
            className={`w-4 h-4 text-gray-300 transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute right-0 mt-2 py-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20 min-w-[140px]">
              {THEME_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    setTheme(option.value);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-2 transition-colors ${
                    theme === option.value
                      ? "bg-purple-500/20 text-purple-300"
                      : "text-gray-300 hover:bg-gray-700"
                  }`}
                >
                  <ThemeIcon theme={option.value} className="w-4 h-4" />
                  <span>{option.label}</span>
                  {theme === option.value && (
                    <svg
                      className="w-4 h-4 ml-auto text-purple-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  // Default: buttons variant
  return (
    <div className={`flex gap-1 bg-gray-800 rounded-lg p-1 ${className}`}>
      {THEME_OPTIONS.map((option) => (
        <button
          key={option.value}
          onClick={() => setTheme(option.value)}
          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
            theme === option.value
              ? "bg-gray-700 text-white"
              : "text-gray-200 hover:text-white"
          }`}
          aria-label={`${option.label} theme`}
          aria-pressed={theme === option.value}
        >
          <ThemeIcon theme={option.value} className="w-4 h-4" />
          {showLabels && <span className="text-sm">{option.label}</span>}
        </button>
      ))}
    </div>
  );
}

// Hook to initialize theme on app load
export function useInitTheme() {
  const { initializeTheme } = useThemeStore();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    initializeTheme();
    setInitialized(true);
  }, [initializeTheme]);

  return initialized;
}

export default ThemeToggle;
