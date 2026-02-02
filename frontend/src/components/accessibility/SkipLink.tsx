"use client";

import React from "react";

interface SkipLinkProps {
    href?: string;
    children?: React.ReactNode;
}

/**
 * SkipLink - Accessibility component for keyboard users
 * 
 * Allows keyboard users to skip navigation and jump directly to main content.
 * Only visible when focused.
 */
export function SkipLink({
    href = "#main-content",
    children = "Skip to main content",
}: SkipLinkProps) {
    return (
        <a
            href={href}
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-purple-600 focus:text-white focus:rounded-lg focus:font-medium focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-purple-400 focus:ring-offset-2 focus:ring-offset-black"
        >
            {children}
        </a>
    );
}

/**
 * SkipLinks - Multiple skip links for complex layouts
 */
export function SkipLinks({
    links,
}: {
    links: { href: string; label: string }[];
}) {
    return (
        <nav aria-label="Skip links" className="sr-only focus-within:not-sr-only">
            <ul className="fixed top-0 left-0 z-[100] flex gap-2 p-2">
                {links.map((link) => (
                    <li key={link.href}>
                        <a
                            href={link.href}
                            className="focus:block focus:px-4 focus:py-2 focus:bg-purple-600 focus:text-white focus:rounded-lg focus:font-medium focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
                        >
                            {link.label}
                        </a>
                    </li>
                ))}
            </ul>
        </nav>
    );
}

export default SkipLink;
