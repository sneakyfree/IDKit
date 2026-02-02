/**
 * PHASE 6: Accessibility Audit Configuration and Utilities
 * 
 * Setup for automated accessibility testing with axe-core
 */

import { configureAxe, toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Configure axe-core with IDKit-specific rules
export const axeConfig = configureAxe({
    rules: {
        // Enforce these rules
        'color-contrast': { enabled: true },
        'keyboard': { enabled: true },
        'aria-roles': { enabled: true },
        'aria-valid-attr': { enabled: true },
        'aria-valid-attr-value': { enabled: true },
        'button-name': { enabled: true },
        'image-alt': { enabled: true },
        'label': { enabled: true },
        'link-name': { enabled: true },
        'list': { enabled: true },
        'listitem': { enabled: true },
        'meta-viewport': { enabled: true },
        'page-has-heading-one': { enabled: true },
        'region': { enabled: true },
        'tabindex': { enabled: true },

        // Exclude these (handled elsewhere or N/A)
        'duplicate-id': { enabled: false }, // React handles this
    },
});

// WCAG 2.1 AA compliance check configuration
export const wcagConfig = {
    runOnly: {
        type: 'tag' as const,
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
    },
};

// Critical pages to test
export const criticalPages = [
    '/',
    '/feed',
    '/settings',
    '/settings/privacy',
    '/settings/payouts',
    '/analytics',
    '/content/bulk',
    '/schedule',
    '/testing',
    '/twins',
    '/podcasts',
];

// Accessibility test helper
export async function testPageAccessibility(page: any, options = {}) {
    const results = await page.evaluate(async () => {
        // @ts-ignore - axe is injected
        return await window.axe.run(document, options);
    });

    return results;
}

// Console output for violations
export function formatViolations(violations: any[]) {
    if (violations.length === 0) {
        return '✅ No accessibility violations found';
    }

    return violations.map((v: any) => {
        const nodes = v.nodes.map((n: any) => `  - ${n.html}`).join('\n');
        return `
❌ ${v.id}: ${v.help}
   Impact: ${v.impact}
   Description: ${v.description}
   Affected elements:
${nodes}
   Fix: ${v.helpUrl}
`;
    }).join('\n');
}
