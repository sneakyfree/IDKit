/**
 * i18n Configuration
 * 
 * Internationalization support for IDKit.
 * Supports 8 languages with auto-detection and persistence.
 */

export const locales = ['en', 'es', 'pt', 'fr', 'de', 'ja', 'ko', 'zh'] as const;
export type Locale = typeof locales[number];

export const localeNames: Record<Locale, string> = {
    en: 'English',
    es: 'Español',
    pt: 'Português',
    fr: 'Français',
    de: 'Deutsch',
    ja: '日本語',
    ko: '한국어',
    zh: '中文',
};

export const localeFlags: Record<Locale, string> = {
    en: '🇺🇸',
    es: '🇪🇸',
    pt: '🇧🇷',
    fr: '🇫🇷',
    de: '🇩🇪',
    ja: '🇯🇵',
    ko: '🇰🇷',
    zh: '🇨🇳',
};

export const defaultLocale: Locale = 'en';

/**
 * Get browser's preferred locale
 */
export function detectBrowserLocale(): Locale {
    if (typeof navigator === 'undefined') return defaultLocale;

    const browserLang = navigator.language.split('-')[0];
    return locales.includes(browserLang as Locale)
        ? (browserLang as Locale)
        : defaultLocale;
}

/**
 * Get locale from localStorage or detect from browser
 */
export function getStoredLocale(): Locale {
    if (typeof localStorage === 'undefined') return defaultLocale;

    const stored = localStorage.getItem('locale');
    if (stored && locales.includes(stored as Locale)) {
        return stored as Locale;
    }
    return detectBrowserLocale();
}

/**
 * Store locale preference
 */
export function setStoredLocale(locale: Locale): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem('locale', locale);
}

/**
 * Format date according to locale
 */
export function formatDate(date: Date | string, locale: Locale): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    }).format(d);
}

/**
 * Format number according to locale
 */
export function formatNumber(num: number, locale: Locale): string {
    return new Intl.NumberFormat(locale).format(num);
}

/**
 * Format currency according to locale
 */
export function formatCurrency(
    amount: number,
    locale: Locale,
    currency: string = 'USD'
): string {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
    }).format(amount);
}
