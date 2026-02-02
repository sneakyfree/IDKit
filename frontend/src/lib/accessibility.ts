/**
 * Accessibility Utilities
 * 
 * Helpers for WCAG 2.1 AA compliance including:
 * - Focus management
 * - Keyboard navigation
 * - ARIA attributes
 * - Screen reader announcements
 */

import { useEffect, useRef, useCallback } from "react";

// ============== Focus Management ==============

/**
 * Trap focus within a container (for modals, dialogs)
 */
export function useFocusTrap(isActive: boolean) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isActive || !containerRef.current) return;

        const container = containerRef.current;
        const focusableElements = container.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Focus first element
        firstElement.focus();

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key !== "Tab") return;

            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        };

        container.addEventListener("keydown", handleKeyDown);
        return () => container.removeEventListener("keydown", handleKeyDown);
    }, [isActive]);

    return containerRef;
}

/**
 * Return focus to element when component unmounts
 */
export function useReturnFocus() {
    const previouslyFocused = useRef<Element | null>(null);

    useEffect(() => {
        previouslyFocused.current = document.activeElement;

        return () => {
            if (previouslyFocused.current instanceof HTMLElement) {
                previouslyFocused.current.focus();
            }
        };
    }, []);
}

// ============== Keyboard Navigation ==============

/**
 * Handle keyboard events for clickable elements
 */
export function getKeyboardClickProps(
    onClick: () => void,
    role: string = "button"
) {
    return {
        role,
        tabIndex: 0,
        onClick,
        onKeyDown: (e: React.KeyboardEvent) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
            }
        },
    };
}

/**
 * Arrow key navigation for menus/lists
 */
export function useArrowNavigation(
    itemCount: number,
    onSelect?: (index: number) => void
) {
    const focusedIndex = useRef(0);

    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            switch (e.key) {
                case "ArrowDown":
                    e.preventDefault();
                    focusedIndex.current = Math.min(focusedIndex.current + 1, itemCount - 1);
                    break;
                case "ArrowUp":
                    e.preventDefault();
                    focusedIndex.current = Math.max(focusedIndex.current - 1, 0);
                    break;
                case "Home":
                    e.preventDefault();
                    focusedIndex.current = 0;
                    break;
                case "End":
                    e.preventDefault();
                    focusedIndex.current = itemCount - 1;
                    break;
                case "Enter":
                case " ":
                    e.preventDefault();
                    onSelect?.(focusedIndex.current);
                    break;
            }
        },
        [itemCount, onSelect]
    );

    return { focusedIndex: focusedIndex.current, handleKeyDown };
}

// ============== Screen Reader Announcements ==============

/**
 * Announce message to screen readers
 */
export function announceToScreenReader(
    message: string,
    priority: "polite" | "assertive" = "polite"
) {
    const announcement = document.createElement("div");
    announcement.setAttribute("role", "status");
    announcement.setAttribute("aria-live", priority);
    announcement.setAttribute("aria-atomic", "true");
    announcement.className = "sr-only";
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

/**
 * Hook for live region announcements
 */
export function useLiveAnnouncer() {
    const announce = useCallback(
        (message: string, priority: "polite" | "assertive" = "polite") => {
            announceToScreenReader(message, priority);
        },
        []
    );

    return announce;
}

// ============== ARIA Helpers ==============

/**
 * Generate unique IDs for ARIA relationships
 */
let idCounter = 0;
export function generateAriaId(prefix: string = "aria"): string {
    return `${prefix}-${++idCounter}`;
}

/**
 * Common ARIA patterns
 */
export const ariaPatterns = {
    // Modal dialog
    dialog: (labelledBy: string) => ({
        role: "dialog",
        "aria-modal": true,
        "aria-labelledby": labelledBy,
    }),

    // Alert/Error message
    alert: {
        role: "alert",
        "aria-live": "assertive" as const,
    },

    // Status message (success, info)
    status: {
        role: "status",
        "aria-live": "polite" as const,
    },

    // Tab panel
    tabPanel: (id: string, labelledBy: string, selected: boolean) => ({
        id,
        role: "tabpanel",
        "aria-labelledby": labelledBy,
        hidden: !selected,
    }),

    // Tab
    tab: (
        id: string,
        controls: string,
        selected: boolean,
        index: number
    ) => ({
        id,
        role: "tab",
        "aria-controls": controls,
        "aria-selected": selected,
        tabIndex: selected ? 0 : -1,
    }),

    // Menu
    menu: {
        role: "menu",
    },

    menuItem: (index: number) => ({
        role: "menuitem",
        tabIndex: index === 0 ? 0 : -1,
    }),

    // Expandable section
    expandable: (expanded: boolean, controlsId: string) => ({
        "aria-expanded": expanded,
        "aria-controls": controlsId,
    }),

    // Loading state
    loading: (isLoading: boolean) => ({
        "aria-busy": isLoading,
    }),

    // Required field
    required: {
        "aria-required": true,
    },

    // Error field
    invalid: (errorId: string) => ({
        "aria-invalid": true,
        "aria-describedby": errorId,
    }),
};

// ============== Visibility Helpers ==============

/**
 * Visually hidden but accessible to screen readers
 */
export const visuallyHiddenStyles: React.CSSProperties = {
    position: "absolute",
    width: "1px",
    height: "1px",
    padding: 0,
    margin: "-1px",
    overflow: "hidden",
    clip: "rect(0, 0, 0, 0)",
    whiteSpace: "nowrap",
    border: 0,
};

// ============== Color Contrast ==============

/**
 * Calculate relative luminance for WCAG contrast
 */
function getLuminance(r: number, g: number, b: number): number {
    const [rs, gs, bs] = [r, g, b].map((c) => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 */
export function getContrastRatio(
    color1: { r: number; g: number; b: number },
    color2: { r: number; g: number; b: number }
): number {
    const l1 = getLuminance(color1.r, color1.g, color1.b);
    const l2 = getLuminance(color2.r, color2.g, color2.b);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if colors meet WCAG AA requirements
 */
export function meetsWCAG_AA(
    foreground: { r: number; g: number; b: number },
    background: { r: number; g: number; b: number },
    isLargeText: boolean = false
): boolean {
    const ratio = getContrastRatio(foreground, background);
    return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

// ============== Motion Preferences ==============

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Hook for reduced motion preference
 */
export function useReducedMotion(): boolean {
    const isReduced = useRef(prefersReducedMotion());

    useEffect(() => {
        const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
        const handleChange = (e: MediaQueryListEvent) => {
            isReduced.current = e.matches;
        };

        mediaQuery.addEventListener("change", handleChange);
        return () => mediaQuery.removeEventListener("change", handleChange);
    }, []);

    return isReduced.current;
}
