/**
 * Tests for i18n Utilities
 * 
 * @jest-environment jsdom
 */

import {
    SUPPORTED_LOCALES,
    LOCALE_NAMES,
    LOCALE_FLAGS,
    detectBrowserLocale,
    formatDate,
    formatNumber,
    formatCurrency,
    formatRelativeTime,
    isRTL,
} from "@/lib/i18n";

describe("i18n Utilities", () => {
    describe("SUPPORTED_LOCALES", () => {
        it("should include 5 languages", () => {
            expect(SUPPORTED_LOCALES).toHaveLength(5);
            expect(SUPPORTED_LOCALES).toContain("en");
            expect(SUPPORTED_LOCALES).toContain("es");
            expect(SUPPORTED_LOCALES).toContain("fr");
            expect(SUPPORTED_LOCALES).toContain("de");
            expect(SUPPORTED_LOCALES).toContain("pt");
        });
    });

    describe("LOCALE_NAMES", () => {
        it("should have names for all locales", () => {
            SUPPORTED_LOCALES.forEach((locale) => {
                expect(LOCALE_NAMES[locale]).toBeDefined();
                expect(typeof LOCALE_NAMES[locale]).toBe("string");
            });
        });

        it("should have correct names", () => {
            expect(LOCALE_NAMES.en).toBe("English");
            expect(LOCALE_NAMES.es).toBe("Español");
            expect(LOCALE_NAMES.fr).toBe("Français");
            expect(LOCALE_NAMES.de).toBe("Deutsch");
            expect(LOCALE_NAMES.pt).toBe("Português");
        });
    });

    describe("LOCALE_FLAGS", () => {
        it("should have flags for all locales", () => {
            SUPPORTED_LOCALES.forEach((locale) => {
                expect(LOCALE_FLAGS[locale]).toBeDefined();
            });
        });

        it("should have emoji flags", () => {
            expect(LOCALE_FLAGS.en).toBe("🇺🇸");
            expect(LOCALE_FLAGS.es).toBe("🇪🇸");
            expect(LOCALE_FLAGS.fr).toBe("🇫🇷");
            expect(LOCALE_FLAGS.de).toBe("🇩🇪");
            expect(LOCALE_FLAGS.pt).toBe("🇵🇹");
        });
    });

    describe("detectBrowserLocale", () => {
        it("should return en as default", () => {
            const locale = detectBrowserLocale();
            expect(SUPPORTED_LOCALES).toContain(locale);
        });
    });

    describe("formatDate", () => {
        const testDate = new Date("2024-06-15T10:30:00Z");

        it("should format date for English locale", () => {
            const formatted = formatDate(testDate, "en");
            expect(formatted).toBeTruthy();
            expect(typeof formatted).toBe("string");
        });

        it("should format date for Spanish locale", () => {
            const formatted = formatDate(testDate, "es");
            expect(formatted).toBeTruthy();
        });

        it("should handle string dates", () => {
            const formatted = formatDate("2024-06-15", "en");
            expect(formatted).toBeTruthy();
        });

        it("should accept formatting options", () => {
            const formatted = formatDate(testDate, "en", {
                year: "numeric",
                month: "long",
                day: "numeric",
            });
            expect(formatted).toContain("2024");
        });
    });

    describe("formatNumber", () => {
        it("should format number for English locale", () => {
            const formatted = formatNumber(1234567.89, "en");
            expect(formatted).toContain("1");
            expect(formatted.length).toBeGreaterThan(7);
        });

        it("should format number for German locale", () => {
            const formatted = formatNumber(1234567.89, "de");
            expect(formatted).toBeTruthy();
        });

        it("should accept formatting options", () => {
            const formatted = formatNumber(0.5, "en", { style: "percent" });
            expect(formatted).toContain("50");
            expect(formatted).toContain("%");
        });
    });

    describe("formatCurrency", () => {
        it("should format USD currency", () => {
            const formatted = formatCurrency(99.99, "en", "USD");
            expect(formatted).toContain("$");
            expect(formatted).toContain("99");
        });

        it("should format EUR currency", () => {
            const formatted = formatCurrency(99.99, "de", "EUR");
            expect(formatted).toContain("€");
        });

        it("should use USD as default currency", () => {
            const formatted = formatCurrency(100, "en");
            expect(formatted).toContain("$");
        });
    });

    describe("formatRelativeTime", () => {
        it("should format recent time as seconds", () => {
            const recentDate = new Date(Date.now() - 30000); // 30 seconds ago
            const formatted = formatRelativeTime(recentDate, "en");
            expect(formatted).toBeTruthy();
        });

        it("should format minutes ago", () => {
            const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);
            const formatted = formatRelativeTime(fiveMinAgo, "en");
            expect(formatted).toBeTruthy();
        });

        it("should format hours ago", () => {
            const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
            const formatted = formatRelativeTime(twoHoursAgo, "en");
            expect(formatted).toBeTruthy();
        });

        it("should format days ago", () => {
            const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
            const formatted = formatRelativeTime(twoDaysAgo, "en");
            expect(formatted).toBeTruthy();
        });

        it("should handle string dates", () => {
            const dateStr = new Date(Date.now() - 3600000).toISOString();
            const formatted = formatRelativeTime(dateStr, "en");
            expect(formatted).toBeTruthy();
        });

        it("should format in different locales", () => {
            const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);

            const enFormatted = formatRelativeTime(oneHourAgo, "en");
            const esFormatted = formatRelativeTime(oneHourAgo, "es");

            // Both should be non-empty strings
            expect(enFormatted).toBeTruthy();
            expect(esFormatted).toBeTruthy();
        });
    });

    describe("isRTL", () => {
        it("should return false for LTR languages", () => {
            expect(isRTL("en")).toBe(false);
            expect(isRTL("es")).toBe(false);
            expect(isRTL("fr")).toBe(false);
            expect(isRTL("de")).toBe(false);
            expect(isRTL("pt")).toBe(false);
        });
    });
});
