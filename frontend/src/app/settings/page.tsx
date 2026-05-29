"use client";

import { useState } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { ThemeToggle } from "@/components/settings/ThemeToggle";
import { LanguageSelector } from "@/components/settings/LanguageSelector";

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    pushEnabled: true,
    emailDigest: true,
    newFollowers: true,
    comments: true,
    mentions: true,
    marketing: false,
  });

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold text-white">Settings</h1>
        </div>
      </header>

      <div className="p-4 space-y-6">
        {/* Account Section */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">Account</h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <Link
              href="/settings/profile"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <UserIcon className="w-5 h-5 text-gray-200" />
                <span>Edit Profile</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/privacy"
              aria-label="Privacy"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span>Privacy</span>
              </div>
              <span className="text-sm text-gray-300">›</span>
            </Link>
            <Link
              href="/settings/security"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <ShieldIcon className="w-5 h-5 text-gray-200" />
                <span>Security & Privacy</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/connected"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <LinkIcon className="w-5 h-5 text-gray-200" />
                <span>Connected Accounts</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
          </div>
        </section>

        {/* Notifications Section */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">Notifications</h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <BellIcon className="w-5 h-5 text-gray-200" />
                <span>Push Notifications</span>
              </div>
              <Toggle
                enabled={notifications.pushEnabled}
                onChange={() =>
                  setNotifications((n) => ({ ...n, pushEnabled: !n.pushEnabled }))
                }
              />
            </div>
            <div className="h-px bg-gray-800 ml-12" />
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <MailIcon className="w-5 h-5 text-gray-200" />
                <span>Email Digest</span>
              </div>
              <Toggle
                enabled={notifications.emailDigest}
                onChange={() =>
                  setNotifications((n) => ({ ...n, emailDigest: !n.emailDigest }))
                }
              />
            </div>
            <div className="h-px bg-gray-800 ml-12" />
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <UsersIcon className="w-5 h-5 text-gray-200" />
                <span>New Followers</span>
              </div>
              <Toggle
                enabled={notifications.newFollowers}
                onChange={() =>
                  setNotifications((n) => ({ ...n, newFollowers: !n.newFollowers }))
                }
              />
            </div>
            <div className="h-px bg-gray-800 ml-12" />
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <ChatIcon className="w-5 h-5 text-gray-200" />
                <span>Comments & Mentions</span>
              </div>
              <Toggle
                enabled={notifications.comments}
                onChange={() =>
                  setNotifications((n) => ({ ...n, comments: !n.comments }))
                }
              />
            </div>
          </div>
        </section>

        {/* Appearance */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">Appearance</h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <PaletteIcon className="w-5 h-5 text-gray-200" />
                <span>Theme</span>
              </div>
              <ThemeToggle variant="buttons" showLabels={true} />
            </div>
            <div className="h-px bg-gray-800" />
            <div className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <GlobeIcon className="w-5 h-5 text-gray-200" />
                <span>Language</span>
              </div>
              <LanguageSelector variant="dropdown" />
            </div>
          </div>
        </section>

        {/* Content & Preferences */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">
            Content & Preferences
          </h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <Link
              href="/settings/brand-voice"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <SparklesIcon className="w-5 h-5 text-gray-200" />
                <span>Brand Voice Settings</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/ai-preferences"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <CpuIcon className="w-5 h-5 text-gray-200" />
                <span>AI Preferences</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/posting"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <CalendarIcon className="w-5 h-5 text-gray-200" />
                <span>Posting Schedule</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
          </div>
        </section>

        {/* Billing */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">Billing</h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <Link
              href="/settings/subscription"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <CreditCardIcon className="w-5 h-5 text-gray-200" />
                <div>
                  <span className="block">Subscription</span>
                  <span className="text-xs text-purple-400">Pro Plan</span>
                </div>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/usage"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <ChartIcon className="w-5 h-5 text-gray-200" />
                <span>Usage & Limits</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/settings/payouts"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <BankIcon className="w-5 h-5 text-gray-200" />
                <span>Payouts</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
          </div>
        </section>

        {/* Support */}
        <section>
          <h2 className="text-sm font-medium text-gray-200 mb-3 px-1">Support</h2>
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            <Link
              href="/help"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <HelpIcon className="w-5 h-5 text-gray-200" />
                <span>Help Center</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
            <div className="h-px bg-gray-800 ml-12" />
            <Link
              href="/feedback"
              className="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <MessageIcon className="w-5 h-5 text-gray-200" />
                <span>Send Feedback</span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-300" />
            </Link>
          </div>
        </section>

        {/* Logout */}
        <button className="w-full py-3 bg-gray-900 rounded-2xl text-red-500 font-medium hover:bg-gray-800 transition-colors">
          Log Out
        </button>

        {/* Version */}
        <p className="text-center text-xs text-gray-200">
          IDKit v1.0.0
        </p>
      </div>

      <section data-test-export-section className="px-4 py-3 border-t border-gray-800">
          <h3 className="text-base font-semibold text-white mb-2">Data export</h3>
          <p className="text-sm text-gray-200 mb-2">Download a copy of your data.</p>
          <button aria-label="Request data export" className="px-4 py-2 bg-purple-600 text-white rounded-lg">Request data export</button>
        </section>
        <section data-test-delete-section className="px-4 py-3 border-t border-gray-800">
          <h3 className="text-base font-semibold text-white mb-2">Delete account</h3>
          <p className="text-sm text-gray-200 mb-2">Permanently remove your account and data.</p>
          <button aria-label="Delete account" className="px-4 py-2 bg-red-600 text-white rounded-lg">Delete account</button>
        </section>
        <BottomNav />
    </main>
  );
}

// Toggle Component
function Toggle({
  enabled,
  onChange,
  label,
}: {
  enabled: boolean;
  onChange: () => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={label || "Toggle setting"}
      onClick={onChange}
      className={`relative w-11 h-6 rounded-full transition-colors ${enabled ? "bg-purple-600" : "bg-gray-700"
        }`}
    >
      <div
        className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${enabled ? "translate-x-6" : "translate-x-1"
          }`}
      />
    </button>
  );
}

// Icons
function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  );
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  );
}

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  );
}

function MailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}

function CpuIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
    </svg>
  );
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function CreditCardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  );
}

function ChartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function HelpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function MessageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}

function PaletteIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
    </svg>
  );
}

function GlobeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function BankIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

