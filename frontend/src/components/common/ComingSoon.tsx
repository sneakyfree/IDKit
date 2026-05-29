"use client";

import Link from "next/link";

interface ComingSoonProps {
  title: string;
  description?: string;
  backHref?: string;
  backLabel?: string;
}

/**
 * Consistent placeholder for features that are routed-to but not yet built.
 * Renders a branded dark-theme page so navigation never dead-ends on a raw 404.
 */
export function ComingSoon({
  title,
  description = "This feature is on the way. Check back soon.",
  backHref = "/",
  backLabel = "Back to home",
}: ComingSoonProps) {
  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
      <p className="text-gray-300 max-w-md mb-8">{description}</p>
      <Link
        href={backHref}
        className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium hover:opacity-90 transition-opacity"
      >
        {backLabel}
      </Link>
    </main>
  );
}

export default ComingSoon;
