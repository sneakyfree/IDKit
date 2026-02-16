/**
 * Ambient type declarations for jest-axe
 * @see https://github.com/nickcolley/jest-axe
 */
declare module 'jest-axe' {
    import type { AxeResults, RunOptions, Spec } from 'axe-core';

    interface JestAxeConfigureOptions {
        rules?: { [key: string]: { enabled: boolean } };
        globalOptions?: Spec;
        impactLevels?: string[];
    }

    export function axe(html: Element | string, options?: RunOptions): Promise<AxeResults>;
    export function configureAxe(options: JestAxeConfigureOptions): typeof axe;
    export const toHaveNoViolations: {
        toHaveNoViolations(results: AxeResults): { pass: boolean; message: () => string };
    };
}
