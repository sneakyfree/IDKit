/**
 * TASK 4.1.2: Lighthouse Optimization Utilities
 * 
 * Performance optimizations for achieving 90+ Lighthouse scores
 */

// ============================================================================
// Image Optimization
// ============================================================================

interface OptimizedImageProps {
    src: string;
    alt: string;
    width: number;
    height: number;
    priority?: boolean;
    className?: string;
    loading?: 'lazy' | 'eager';
    sizes?: string;
}

/**
 * Generate responsive image srcset for optimal loading
 */
export function generateSrcSet(baseSrc: string, widths: number[] = [320, 640, 750, 1080, 1200]): string {
    const extension = baseSrc.split('.').pop() || 'jpg';
    const basePath = baseSrc.replace(`.${extension}`, '');

    return widths
        .map(w => `${basePath}-${w}w.${extension} ${w}w`)
        .join(', ');
}

/**
 * Calculate sizes attribute for responsive images
 */
export function calculateSizes(breakpoints: { maxWidth: number; size: string }[]): string {
    return breakpoints
        .map(bp => `(max-width: ${bp.maxWidth}px) ${bp.size}`)
        .concat(['100vw'])
        .join(', ');
}

// ============================================================================
// Script Loading Optimization
// ============================================================================

type ScriptLoadingStrategy = 'afterInteractive' | 'lazyOnload' | 'beforeInteractive' | 'worker';

interface ScriptConfig {
    src: string;
    strategy: ScriptLoadingStrategy;
    onLoad?: () => void;
}

/**
 * Dynamically load scripts with optimal timing
 */
export function loadScript(config: ScriptConfig): Promise<void> {
    return new Promise((resolve, reject) => {
        if (typeof window === 'undefined') {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = config.src;
        script.async = true;

        if (config.strategy === 'lazyOnload') {
            script.defer = true;
        }

        script.onload = () => {
            config.onLoad?.();
            resolve();
        };
        script.onerror = reject;

        if (config.strategy === 'beforeInteractive') {
            document.head.appendChild(script);
        } else {
            // Append after main content for non-critical scripts
            document.body.appendChild(script);
        }
    });
}

/**
 * Load multiple scripts in parallel with priority
 */
export async function loadScripts(configs: ScriptConfig[]): Promise<void> {
    const critical = configs.filter(c => c.strategy === 'beforeInteractive');
    const afterInteractive = configs.filter(c => c.strategy === 'afterInteractive');
    const lazy = configs.filter(c => c.strategy === 'lazyOnload');

    // Load critical first
    await Promise.all(critical.map(loadScript));

    // Then after interactive
    await Promise.all(afterInteractive.map(loadScript));

    // Lazy scripts on idle
    if ('requestIdleCallback' in window) {
        window.requestIdleCallback(() => {
            lazy.forEach(loadScript);
        });
    } else {
        setTimeout(() => lazy.forEach(loadScript), 1000);
    }
}

// ============================================================================
// Font Loading Optimization
// ============================================================================

/**
 * Preload critical fonts
 */
export function preloadFonts(fonts: { href: string; as: string; type: string; crossOrigin?: string }[]): void {
    if (typeof document === 'undefined') return;

    fonts.forEach(font => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = font.href;
        link.as = font.as;
        link.type = font.type;
        if (font.crossOrigin) {
            link.crossOrigin = font.crossOrigin;
        }
        document.head.appendChild(link);
    });
}

/**
 * Font display strategy for optimal CLS
 */
export const fontDisplayStrategies = {
    // Use for critical text - prevents invisible text
    swap: 'font-display: swap;',
    // Use for non-critical text - better performance
    optional: 'font-display: optional;',
    // Good balance for most cases
    fallback: 'font-display: fallback;',
};

// ============================================================================
// Critical CSS
// ============================================================================

/**
 * Extract and inline critical CSS
 */
export function inlineCriticalCSS(css: string): void {
    if (typeof document === 'undefined') return;

    const style = document.createElement('style');
    style.id = 'critical-css';
    style.textContent = css;
    document.head.insertBefore(style, document.head.firstChild);
}

/**
 * Defer non-critical CSS
 */
export function deferStylesheet(href: string): void {
    if (typeof document === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.media = 'print';
    link.onload = () => {
        link.media = 'all';
    };
    document.head.appendChild(link);
}

// ============================================================================
// Lazy Loading
// ============================================================================

/**
 * Intersection Observer for lazy loading
 */
export function createLazyLoadObserver(
    onIntersect: (element: Element) => void,
    options: IntersectionObserverInit = {}
): IntersectionObserver | null {
    if (typeof IntersectionObserver === 'undefined') return null;

    const defaultOptions: IntersectionObserverInit = {
        root: null,
        rootMargin: '50px',
        threshold: 0.1,
        ...options,
    };

    return new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                onIntersect(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, defaultOptions);
}

/**
 * Lazy load images with native loading attribute fallback
 */
export function setupLazyImages(): void {
    if (typeof document === 'undefined') return;

    // Check for native lazy loading support
    if ('loading' in HTMLImageElement.prototype) {
        document.querySelectorAll('img[data-src]').forEach(img => {
            (img as HTMLImageElement).src = img.getAttribute('data-src') || '';
        });
        return;
    }

    // Fallback with Intersection Observer
    const observer = createLazyLoadObserver((element) => {
        const img = element as HTMLImageElement;
        img.src = img.getAttribute('data-src') || '';
        img.removeAttribute('data-src');
    });

    if (observer) {
        document.querySelectorAll('img[data-src]').forEach(img => {
            observer.observe(img);
        });
    }
}

// ============================================================================
// Resource Hints
// ============================================================================

type ResourceHintType = 'preload' | 'prefetch' | 'preconnect' | 'dns-prefetch';

interface ResourceHint {
    rel: ResourceHintType;
    href: string;
    as?: string;
    crossOrigin?: string;
}

/**
 * Add resource hints dynamically
 */
export function addResourceHints(hints: ResourceHint[]): void {
    if (typeof document === 'undefined') return;

    hints.forEach(hint => {
        const link = document.createElement('link');
        link.rel = hint.rel;
        link.href = hint.href;
        if (hint.as) link.as = hint.as;
        if (hint.crossOrigin) link.crossOrigin = hint.crossOrigin;
        document.head.appendChild(link);
    });
}

/**
 * Common resource hints for IDKit
 */
export const commonResourceHints: ResourceHint[] = [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossOrigin: 'anonymous' },
    { rel: 'dns-prefetch', href: 'https://api.stripe.com' },
    { rel: 'dns-prefetch', href: 'https://www.googletagmanager.com' },
];

// ============================================================================
// Performance Budget
// ============================================================================

export interface PerformanceBudget {
    resourceType: string;
    maxSize: number; // in KB
    maxRequests?: number;
}

export const defaultBudget: PerformanceBudget[] = [
    { resourceType: 'script', maxSize: 300, maxRequests: 10 },
    { resourceType: 'stylesheet', maxSize: 100, maxRequests: 3 },
    { resourceType: 'image', maxSize: 500, maxRequests: 20 },
    { resourceType: 'font', maxSize: 100, maxRequests: 4 },
    { resourceType: 'total', maxSize: 1500 },
];

/**
 * Check if resources exceed budget
 */
export function checkPerformanceBudget(
    resources: { type: string; size: number }[],
    budget: PerformanceBudget[] = defaultBudget
): { passed: boolean; violations: string[] } {
    const violations: string[] = [];
    const grouped: Record<string, { totalSize: number; count: number }> = {};

    resources.forEach(r => {
        if (!grouped[r.type]) {
            grouped[r.type] = { totalSize: 0, count: 0 };
        }
        grouped[r.type].totalSize += r.size;
        grouped[r.type].count++;
    });

    budget.forEach(b => {
        const group = grouped[b.resourceType];
        if (group) {
            if (group.totalSize > b.maxSize) {
                violations.push(`${b.resourceType} exceeds size budget: ${group.totalSize}KB > ${b.maxSize}KB`);
            }
            if (b.maxRequests && group.count > b.maxRequests) {
                violations.push(`${b.resourceType} exceeds request budget: ${group.count} > ${b.maxRequests}`);
            }
        }
    });

    return { passed: violations.length === 0, violations };
}
