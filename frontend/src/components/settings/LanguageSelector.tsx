"use client";

import { useEffect, useState } from "react";
import {
  useI18nStore,
  useTranslation,
  SUPPORTED_LOCALES,
  LOCALE_NAMES,
  LOCALE_FLAGS,
  Locale,
  detectBrowserLocale,
} from "@/lib/i18n";

interface LanguageSelectorProps {
  variant?: "dropdown" | "list" | "compact";
  showFlags?: boolean;
  showNames?: boolean;
  className?: string;
}

export function LanguageSelector({
  variant = "dropdown",
  showFlags = true,
  showNames = true,
  className = "",
}: LanguageSelectorProps) {
  const { locale, setLocale, loadTranslations, isLoading } = useI18nStore();
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Load translations on mount
  useEffect(() => {
    setMounted(true);
    loadTranslations(locale);
  }, []);

  // Auto-detect browser locale on first visit
  useEffect(() => {
    if (mounted && !localStorage.getItem("idkit-i18n")) {
      const detectedLocale = detectBrowserLocale();
      if (detectedLocale !== locale) {
        setLocale(detectedLocale);
      }
    }
  }, [mounted]);

  const handleLocaleChange = (newLocale: Locale) => {
    setLocale(newLocale);
    setIsOpen(false);
  };

  if (!mounted) {
    return null;
  }

  if (variant === "list") {
    return (
      <div className={`space-y-2 ${className}`}>
        <label className="block text-sm font-medium text-gray-200 mb-3">
          {t("settings.selectLanguage")}
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {SUPPORTED_LOCALES.map((loc) => (
            <button
              key={loc}
              onClick={() => handleLocaleChange(loc)}
              disabled={isLoading}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-colors ${
                locale === loc
                  ? "border-purple-500 bg-purple-500/20 text-white"
                  : "border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white"
              } ${isLoading ? "opacity-80 cursor-not-allowed" : ""}`}
            >
              {showFlags && (
                <span className="text-xl">{LOCALE_FLAGS[loc]}</span>
              )}
              {showNames && (
                <span className="flex-1 text-left">{LOCALE_NAMES[loc]}</span>
              )}
              {locale === loc && (
                <svg
                  className="w-5 h-5 text-purple-400"
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
      </div>
    );
  }

  if (variant === "compact") {
    return (
      <div className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading}
          className={`flex items-center gap-1 px-2 py-1 rounded text-sm hover:bg-gray-800 transition-colors ${
            isLoading ? "opacity-80 cursor-not-allowed" : ""
          }`}
        >
          {showFlags && <span>{LOCALE_FLAGS[locale]}</span>}
          <span className="text-gray-300 uppercase">{locale}</span>
          <svg
            className={`w-3 h-3 text-gray-300 transition-transform ${
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
            <div className="absolute right-0 mt-1 py-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20 min-w-[120px]">
              {SUPPORTED_LOCALES.map((loc) => (
                <button
                  key={loc}
                  onClick={() => handleLocaleChange(loc)}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 text-sm transition-colors ${
                    locale === loc
                      ? "bg-purple-500/20 text-purple-300"
                      : "text-gray-300 hover:bg-gray-700"
                  }`}
                >
                  {showFlags && <span>{LOCALE_FLAGS[loc]}</span>}
                  <span className="uppercase">{loc}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  // Default dropdown variant
  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className={`flex items-center justify-between gap-3 w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors ${
          isLoading ? "opacity-80 cursor-not-allowed" : ""
        }`}
      >
        <div className="flex items-center gap-2">
          {showFlags && (
            <span className="text-xl">{LOCALE_FLAGS[locale]}</span>
          )}
          {showNames && (
            <span className="text-white">{LOCALE_NAMES[locale]}</span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-300 transition-transform ${
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
          <div className="absolute left-0 right-0 mt-2 py-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20">
            {SUPPORTED_LOCALES.map((loc) => (
              <button
                key={loc}
                onClick={() => handleLocaleChange(loc)}
                className={`w-full flex items-center gap-3 px-4 py-2 transition-colors ${
                  locale === loc
                    ? "bg-purple-500/20 text-purple-300"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                {showFlags && (
                  <span className="text-xl">{LOCALE_FLAGS[loc]}</span>
                )}
                {showNames && <span>{LOCALE_NAMES[loc]}</span>}
                {locale === loc && (
                  <svg
                    className="w-5 h-5 ml-auto text-purple-400"
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

// Hook to initialize i18n on app load
export function useInitI18n() {
  const { locale, loadTranslations } = useI18nStore();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const init = async () => {
      await loadTranslations(locale);
      setInitialized(true);
    };
    init();
  }, []);

  return initialized;
}

export default LanguageSelector;
