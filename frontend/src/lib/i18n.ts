import { create } from "zustand";
import { persist } from "zustand/middleware";

// Supported locales
export const SUPPORTED_LOCALES = ["en", "es", "fr", "de", "pt"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  pt: "Português",
};

export const LOCALE_FLAGS: Record<Locale, string> = {
  en: "🇺🇸",
  es: "🇪🇸",
  fr: "🇫🇷",
  de: "🇩🇪",
  pt: "🇵🇹",
};

// Translation type based on message structure
type TranslationKey = string;
type TranslationValue = string | Record<string, unknown>;
type Translations = Record<string, Record<string, TranslationValue>>;

// Store for managing locale state
interface I18nState {
  locale: Locale;
  translations: Translations | null;
  isLoading: boolean;
  setLocale: (locale: Locale) => void;
  loadTranslations: (locale: Locale) => Promise<void>;
}

// Import translations dynamically
const loadTranslationFile = async (locale: Locale): Promise<Translations> => {
  try {
    const translations = await import(`../../messages/${locale}.json`);
    return translations.default || translations;
  } catch (error) {
    console.error(`Failed to load translations for locale: ${locale}`, error);
    // Fallback to English
    if (locale !== "en") {
      const fallback = await import("../../messages/en.json");
      return fallback.default || fallback;
    }
    return {};
  }
};

export const useI18nStore = create<I18nState>()(
  persist(
    (set, get) => ({
      locale: "en",
      translations: null,
      isLoading: false,

      setLocale: async (locale: Locale) => {
        set({ locale });
        await get().loadTranslations(locale);
      },

      loadTranslations: async (locale: Locale) => {
        set({ isLoading: true });
        try {
          const translations = await loadTranslationFile(locale);
          set({ translations, isLoading: false });
        } catch (error) {
          console.error("Failed to load translations:", error);
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "idkit-i18n",
      partialize: (state) => ({ locale: state.locale }),
    }
  )
);

// Translation function with interpolation support
export function useTranslation() {
  const { translations, locale, isLoading } = useI18nStore();

  const t = (
    key: TranslationKey,
    params?: Record<string, string | number>
  ): string => {
    if (!translations) return key;

    // Split key by dots to access nested translations
    const keys = key.split(".");
    let value: unknown = translations;

    for (const k of keys) {
      if (value && typeof value === "object" && k in value) {
        value = (value as Record<string, unknown>)[k];
      } else {
        // Key not found, return the key itself
        return key;
      }
    }

    if (typeof value !== "string") {
      return key;
    }

    // Handle pluralization
    if (params?.count !== undefined) {
      const count = params.count as number;
      const pluralKey = count === 1 ? key : `${key}_plural`;
      const pluralKeys = pluralKey.split(".");
      let pluralValue: unknown = translations;

      for (const k of pluralKeys) {
        if (pluralValue && typeof pluralValue === "object" && k in pluralValue) {
          pluralValue = (pluralValue as Record<string, unknown>)[k];
        } else {
          break;
        }
      }

      if (typeof pluralValue === "string") {
        value = pluralValue;
      }
    }

    // Replace parameters in the string
    let result = value as string;
    if (params) {
      for (const [paramKey, paramValue] of Object.entries(params)) {
        result = result.replace(
          new RegExp(`\\{${paramKey}\\}`, "g"),
          String(paramValue)
        );
      }
    }

    return result;
  };

  return { t, locale, isLoading };
}

// Detect browser locale
export function detectBrowserLocale(): Locale {
  if (typeof window === "undefined") return "en";

  const browserLang = navigator.language.split("-")[0];

  if (SUPPORTED_LOCALES.includes(browserLang as Locale)) {
    return browserLang as Locale;
  }

  return "en";
}

// Format date according to locale
export function formatDate(
  date: Date | string,
  locale: Locale,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;

  const localeMap: Record<Locale, string> = {
    en: "en-US",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    pt: "pt-BR",
  };

  return dateObj.toLocaleDateString(localeMap[locale], options);
}

// Format number according to locale
export function formatNumber(
  num: number,
  locale: Locale,
  options?: Intl.NumberFormatOptions
): string {
  const localeMap: Record<Locale, string> = {
    en: "en-US",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    pt: "pt-BR",
  };

  return num.toLocaleString(localeMap[locale], options);
}

// Format currency according to locale
export function formatCurrency(
  amount: number,
  locale: Locale,
  currency = "USD"
): string {
  const localeMap: Record<Locale, string> = {
    en: "en-US",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    pt: "pt-BR",
  };

  return new Intl.NumberFormat(localeMap[locale], {
    style: "currency",
    currency,
  }).format(amount);
}

// Format relative time (e.g., "2 hours ago")
export function formatRelativeTime(
  date: Date | string,
  locale: Locale
): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  const localeMap: Record<Locale, string> = {
    en: "en-US",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    pt: "pt-BR",
  };

  const rtf = new Intl.RelativeTimeFormat(localeMap[locale], {
    numeric: "auto",
  });

  if (diffInSeconds < 60) {
    return rtf.format(-diffInSeconds, "second");
  } else if (diffInSeconds < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), "minute");
  } else if (diffInSeconds < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), "hour");
  } else if (diffInSeconds < 604800) {
    return rtf.format(-Math.floor(diffInSeconds / 86400), "day");
  } else if (diffInSeconds < 2592000) {
    return rtf.format(-Math.floor(diffInSeconds / 604800), "week");
  } else if (diffInSeconds < 31536000) {
    return rtf.format(-Math.floor(diffInSeconds / 2592000), "month");
  } else {
    return rtf.format(-Math.floor(diffInSeconds / 31536000), "year");
  }
}

// RTL support check
export function isRTL(locale: Locale): boolean {
  // Add RTL locales here when supported (e.g., Arabic, Hebrew)
  const rtlLocales: Locale[] = [];
  return rtlLocales.includes(locale);
}
