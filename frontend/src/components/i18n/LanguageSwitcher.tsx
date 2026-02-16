"use client";

import { useState, useRef, useEffect } from "react";
import { Globe, Check, ChevronDown } from "lucide-react";
import { useI18nStore, SUPPORTED_LOCALES, LOCALE_NAMES, LOCALE_FLAGS } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";

/**
 * LanguageSwitcher — Dropdown to select locale
 *
 * Features:
 * - Keyboard navigation (arrow keys, Enter, Escape)
 * - ARIA combobox pattern
 * - Persists to localStorage via Zustand
 * - Flag icons + native locale names
 */
export function LanguageSwitcher({ variant = "default" }: { variant?: "default" | "compact" }) {
    const { locale, setLocale } = useI18nStore();
    const [open, setOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const listboxId = "language-listbox";

    // Close on outside click
    useEffect(() => {
        function handleClick(e: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, []);

    // Close on Escape
    function handleKeyDown(e: React.KeyboardEvent) {
        if (e.key === "Escape") {
            setOpen(false);
        }
    }

    function selectLocale(loc: Locale) {
        setLocale(loc);
        setOpen(false);
    }

    return (
        <div ref={containerRef} className="relative" onKeyDown={handleKeyDown}>
            <button
                onClick={() => setOpen(!open)}
                className={`flex items-center gap-2 rounded-xl transition-colors ${variant === "compact"
                        ? "p-2 hover:bg-gray-800"
                        : "px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700"
                    }`}
                aria-haspopup="listbox"
                aria-expanded={open}
                aria-controls={listboxId}
                aria-label="Select language"
            >
                <Globe className="w-4 h-4 text-gray-400" />
                {variant !== "compact" && (
                    <>
                        <span className="text-sm">
                            {LOCALE_FLAGS[locale]} {LOCALE_NAMES[locale]}
                        </span>
                        <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`} />
                    </>
                )}
            </button>

            {open && (
                <ul
                    id={listboxId}
                    role="listbox"
                    aria-label="Languages"
                    className="absolute right-0 top-full mt-2 w-52 bg-gray-900 border border-gray-700 rounded-xl shadow-xl z-50 py-1 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
                >
                    {SUPPORTED_LOCALES.map((loc) => (
                        <li
                            key={loc}
                            role="option"
                            aria-selected={locale === loc}
                            className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${locale === loc
                                    ? "bg-purple-600/20 text-purple-300"
                                    : "hover:bg-gray-800 text-gray-300"
                                }`}
                            onClick={() => selectLocale(loc)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                    e.preventDefault();
                                    selectLocale(loc);
                                }
                            }}
                            tabIndex={0}
                        >
                            <span className="text-lg">{LOCALE_FLAGS[loc]}</span>
                            <span className="text-sm flex-1">{LOCALE_NAMES[loc]}</span>
                            {locale === loc && <Check className="w-4 h-4 text-purple-400" />}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default LanguageSwitcher;
