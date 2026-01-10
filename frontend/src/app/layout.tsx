import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { SkipLinks } from "@/components/a11y/SkipLink";
import { GlobalLiveRegion } from "@/components/a11y/LiveRegion";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "IDKit - Influencer Development Kit",
  description: "AI-powered platform for influencers to automate marketing and content creation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#000000" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var stored = localStorage.getItem('idkit-theme');
                  var theme = stored ? JSON.parse(stored).state?.theme : 'dark';
                  var resolved = theme;
                  if (theme === 'system') {
                    resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  document.documentElement.classList.remove('light', 'dark');
                  document.documentElement.classList.add(resolved);
                  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', resolved === 'dark' ? '#000000' : '#ffffff');
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.className} bg-white dark:bg-black text-gray-900 dark:text-white antialiased transition-colors duration-200`}>
        <ThemeProvider>
          <SkipLinks />
          <GlobalLiveRegion />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
