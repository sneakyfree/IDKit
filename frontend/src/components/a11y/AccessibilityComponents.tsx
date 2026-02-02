'use client';

/**
 * Accessibility Components
 * 
 * WCAG-compliant utility components for improved accessibility.
 */

import { ReactNode, useEffect, useRef, useState } from 'react';

/**
 * SkipLink - Allows keyboard users to skip to main content
 */
export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
    return (
        <a
            href={`#${targetId}`}
            className="
        sr-only focus:not-sr-only
        focus:absolute focus:top-4 focus:left-4 focus:z-50
        focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white
        focus:rounded-lg focus:ring-2 focus:ring-white focus:outline-none
        transition-all
      "
        >
            Skip to main content
        </a>
    );
}

/**
 * FocusTrap - Traps focus within a container (for modals/dialogs)
 */
interface FocusTrapProps {
    children: ReactNode;
    active?: boolean;
    onEscape?: () => void;
}

export function FocusTrap({ children, active = true, onEscape }: FocusTrapProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!active) return;

        const container = containerRef.current;
        if (!container) return;

        // Find all focusable elements
        const getFocusableElements = () => {
            return container.querySelectorAll<HTMLElement>(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && onEscape) {
                onEscape();
                return;
            }

            if (e.key !== 'Tab') return;

            const focusable = getFocusableElements();
            if (focusable.length === 0) return;

            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        };

        // Focus first element on mount
        const focusable = getFocusableElements();
        if (focusable.length > 0) {
            focusable[0].focus();
        }

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [active, onEscape]);

    return <div ref={containerRef}>{children}</div>;
}

/**
 * LiveRegion - Announces dynamic content changes to screen readers
 */
interface LiveRegionProps {
    message: string;
    type?: 'polite' | 'assertive';
}

export function LiveRegion({ message, type = 'polite' }: LiveRegionProps) {
    const [announcement, setAnnouncement] = useState('');

    useEffect(() => {
        if (message) {
            // Clear then set to trigger announcement
            setAnnouncement('');
            const timer = setTimeout(() => setAnnouncement(message), 100);
            return () => clearTimeout(timer);
        }
    }, [message]);

    return (
        <div
            role="status"
            aria-live={type}
            aria-atomic="true"
            className="sr-only"
        >
            {announcement}
        </div>
    );
}

/**
 * VisuallyHidden - Hides content visually but keeps it accessible to screen readers
 */
export function VisuallyHidden({ children }: { children: ReactNode }) {
    return <span className="sr-only">{children}</span>;
}

/**
 * useAnnounce - Hook for programmatic announcements
 */
export function useAnnounce() {
    const [message, setMessage] = useState('');
    const [type, setType] = useState<'polite' | 'assertive'>('polite');

    const announce = (text: string, priority: 'polite' | 'assertive' = 'polite') => {
        setType(priority);
        setMessage(text);
    };

    const LiveAnnouncer = () => (
        <LiveRegion message={message} type={type} />
    );

    return { announce, LiveAnnouncer };
}

/**
 * useReducedMotion - Respects user's reduced motion preference
 */
export function useReducedMotion(): boolean {
    const [reducedMotion, setReducedMotion] = useState(false);

    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        setReducedMotion(mediaQuery.matches);

        const handleChange = (e: MediaQueryListEvent) => {
            setReducedMotion(e.matches);
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, []);

    return reducedMotion;
}

/**
 * Landmarks - Semantic landmark wrapper
 */
interface LandmarkProps {
    as?: 'main' | 'nav' | 'aside' | 'header' | 'footer' | 'section';
    label?: string;
    children: ReactNode;
    className?: string;
}

export function Landmark({
    as: Component = 'section',
    label,
    children,
    className = ''
}: LandmarkProps) {
    return (
        <Component aria-label={label} className={className}>
            {children}
        </Component>
    );
}
