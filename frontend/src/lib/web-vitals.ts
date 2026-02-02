/**
 * Web Vitals Performance Monitoring
 * 
 * Tracks Core Web Vitals metrics for performance optimization:
 * - LCP (Largest Contentful Paint)
 * - FID (First Input Delay)
 * - CLS (Cumulative Layout Shift)
 * - FCP (First Contentful Paint)
 * - TTFB (Time to First Byte)
 */

export interface WebVitalsMetric {
    name: 'LCP' | 'FID' | 'CLS' | 'FCP' | 'TTFB' | 'INP';
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
    delta: number;
    id: string;
    navigationType: string;
}

// Thresholds based on Google's Core Web Vitals
const THRESHOLDS = {
    LCP: { good: 2500, poor: 4000 },
    FID: { good: 100, poor: 300 },
    CLS: { good: 0.1, poor: 0.25 },
    FCP: { good: 1800, poor: 3000 },
    TTFB: { good: 800, poor: 1800 },
    INP: { good: 200, poor: 500 },
};

/**
 * Get rating for a metric value
 */
function getRating(name: keyof typeof THRESHOLDS, value: number): 'good' | 'needs-improvement' | 'poor' {
    const threshold = THRESHOLDS[name];
    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
}

/**
 * Report handler type
 */
type ReportHandler = (metric: WebVitalsMetric) => void;

// Stores for metrics
let metricsStore: WebVitalsMetric[] = [];
let reportHandlers: ReportHandler[] = [];

/**
 * Report a web vital metric
 */
function reportMetric(metric: WebVitalsMetric): void {
    metricsStore.push(metric);
    reportHandlers.forEach(handler => handler(metric));
}

/**
 * Initialize Web Vitals monitoring
 * 
 * Call this in your app's entry point or layout component
 */
export async function initWebVitals(onReport?: ReportHandler): Promise<void> {
    if (onReport) {
        reportHandlers.push(onReport);
    }

    if (typeof window === 'undefined') return;

    try {
        // Dynamically import web-vitals to avoid SSR issues
        const { onLCP, onFID, onCLS, onFCP, onTTFB, onINP } = await import('web-vitals');

        const createHandler = (name: keyof typeof THRESHOLDS) => {
            return (metric: { name: string; value: number; delta: number; id: string; navigationType: string }) => {
                reportMetric({
                    name: name as WebVitalsMetric['name'],
                    value: metric.value,
                    rating: getRating(name, metric.value),
                    delta: metric.delta,
                    id: metric.id,
                    navigationType: metric.navigationType,
                });
            };
        };

        onLCP(createHandler('LCP'));
        onFID(createHandler('FID'));
        onCLS(createHandler('CLS'));
        onFCP(createHandler('FCP'));
        onTTFB(createHandler('TTFB'));
        onINP(createHandler('INP'));
    } catch (error) {
        console.warn('Web Vitals not available:', error);
    }
}

/**
 * Get all collected metrics
 */
export function getMetrics(): WebVitalsMetric[] {
    return [...metricsStore];
}

/**
 * Clear collected metrics
 */
export function clearMetrics(): void {
    metricsStore = [];
}

/**
 * Add a report handler
 */
export function onMetric(handler: ReportHandler): () => void {
    reportHandlers.push(handler);
    return () => {
        reportHandlers = reportHandlers.filter(h => h !== handler);
    };
}

/**
 * Send metrics to analytics endpoint
 */
export async function sendToAnalytics(
    endpoint: string,
    additionalData?: Record<string, unknown>
): Promise<void> {
    const metrics = getMetrics();
    if (metrics.length === 0) return;

    try {
        await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                metrics,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                userAgent: navigator.userAgent,
                ...additionalData,
            }),
            // Use keepalive to ensure the request completes even if page unloads
            keepalive: true,
        });
    } catch (error) {
        console.warn('Failed to send metrics:', error);
    }
}

/**
 * Log metrics to console (for development)
 */
export function logMetrics(): void {
    const metrics = getMetrics();

    console.group('📊 Web Vitals');

    metrics.forEach(metric => {
        const emoji = metric.rating === 'good' ? '✅' : metric.rating === 'needs-improvement' ? '⚠️' : '❌';
        const unit = metric.name === 'CLS' ? '' : 'ms';
        console.log(
            `${emoji} ${metric.name}: ${metric.value.toFixed(metric.name === 'CLS' ? 3 : 0)}${unit} (${metric.rating})`
        );
    });

    console.groupEnd();
}

/**
 * Get performance score (0-100) based on Core Web Vitals
 */
export function getPerformanceScore(): number {
    const metrics = getMetrics();
    if (metrics.length === 0) return 100;

    const scores: Record<string, number> = {};

    metrics.forEach(metric => {
        const threshold = THRESHOLDS[metric.name as keyof typeof THRESHOLDS];
        if (!threshold) return;

        // Calculate score: 100 for good threshold, 50 for poor threshold, linear interpolation
        if (metric.value <= threshold.good) {
            scores[metric.name] = 100;
        } else if (metric.value >= threshold.poor) {
            scores[metric.name] = 0;
        } else {
            // Linear interpolation between good and poor
            const range = threshold.poor - threshold.good;
            const position = metric.value - threshold.good;
            scores[metric.name] = Math.round(100 - (position / range) * 100);
        }
    });

    const scoreValues = Object.values(scores);
    if (scoreValues.length === 0) return 100;

    return Math.round(scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length);
}

/**
 * Get formatted metrics for display
 */
export function getFormattedMetrics(): {
    name: string;
    displayValue: string;
    rating: string;
    description: string;
}[] {
    const metrics = getMetrics();

    const descriptions: Record<string, string> = {
        LCP: 'Largest Contentful Paint - Loading performance',
        FID: 'First Input Delay - Interactivity',
        CLS: 'Cumulative Layout Shift - Visual stability',
        FCP: 'First Contentful Paint - Initial render',
        TTFB: 'Time to First Byte - Server response',
        INP: 'Interaction to Next Paint - Responsiveness',
    };

    return metrics.map(metric => ({
        name: metric.name,
        displayValue: metric.name === 'CLS'
            ? metric.value.toFixed(3)
            : `${Math.round(metric.value)}ms`,
        rating: metric.rating,
        description: descriptions[metric.name] || metric.name,
    }));
}
