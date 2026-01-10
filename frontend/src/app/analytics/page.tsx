"use client";

import { useState } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";

type TimeRange = "7d" | "30d" | "90d" | "all";

// Mock analytics data
const mockOverview = {
  totalFollowers: 12500,
  followerChange: 342,
  followerChangePercent: 2.8,
  totalViews: 245000,
  viewChange: 18500,
  viewChangePercent: 8.2,
  totalEngagements: 15600,
  engagementRate: 6.4,
  engagementChange: 0.3,
};

const mockPlatformStats = [
  { platform: "TikTok", followers: 5200, views: 125000, growth: 5.2, color: "bg-pink-500" },
  { platform: "Instagram", followers: 4100, views: 68000, growth: 2.1, color: "bg-purple-500" },
  { platform: "YouTube", followers: 2800, views: 42000, growth: 3.8, color: "bg-red-500" },
  { platform: "Twitter/X", followers: 400, views: 10000, growth: 1.5, color: "bg-blue-500" },
];

const mockTopContent = [
  { id: "1", title: "How AI is Changing Everything", platform: "TikTok", views: 45200, engagement: 8.2 },
  { id: "2", title: "Morning Routine 2024", platform: "Instagram", views: 28900, engagement: 6.8 },
  { id: "3", title: "Tech Review: Latest Gadgets", platform: "YouTube", views: 18400, engagement: 5.5 },
];

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Analytics</h1>
          <Link
            href="/analytics/export"
            className="px-4 py-2 bg-gray-800 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Export
          </Link>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2 px-4 pb-3">
          {(["7d", "30d", "90d", "all"] as TimeRange[]).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                timeRange === range
                  ? "bg-white text-black"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {range === "all" ? "All Time" : range.replace("d", " Days")}
            </button>
          ))}
        </div>
      </header>

      {/* Overview Cards */}
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {/* Followers */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <UsersIcon className="w-4 h-4" />
              Followers
            </div>
            <div className="text-2xl font-bold">
              {formatNumber(mockOverview.totalFollowers)}
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendUpIcon className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-500">
                +{formatNumber(mockOverview.followerChange)} ({mockOverview.followerChangePercent}%)
              </span>
            </div>
          </div>

          {/* Views */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <EyeIcon className="w-4 h-4" />
              Views
            </div>
            <div className="text-2xl font-bold">
              {formatNumber(mockOverview.totalViews)}
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendUpIcon className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-500">
                +{formatNumber(mockOverview.viewChange)} ({mockOverview.viewChangePercent}%)
              </span>
            </div>
          </div>

          {/* Engagements */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <HeartIcon className="w-4 h-4" />
              Engagements
            </div>
            <div className="text-2xl font-bold">
              {formatNumber(mockOverview.totalEngagements)}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Likes, comments, shares
            </div>
          </div>

          {/* Engagement Rate */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <ChartIcon className="w-4 h-4" />
              Eng. Rate
            </div>
            <div className="text-2xl font-bold">
              {mockOverview.engagementRate}%
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendUpIcon className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-500">
                +{mockOverview.engagementChange}%
              </span>
            </div>
          </div>
        </div>

        {/* Platform Breakdown */}
        <div className="bg-gray-900 rounded-2xl p-4">
          <h2 className="font-semibold mb-4">Platform Performance</h2>
          <div className="space-y-4">
            {mockPlatformStats.map((platform) => (
              <div key={platform.platform}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${platform.color}`} />
                    <span className="text-sm font-medium">{platform.platform}</span>
                  </div>
                  <span className="text-sm text-gray-400">
                    {formatNumber(platform.followers)} followers
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${platform.color}`}
                      style={{
                        width: `${(platform.views / mockOverview.totalViews) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-20 text-right">
                    {formatNumber(platform.views)} views
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Content */}
        <div className="bg-gray-900 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Top Performing Content</h2>
            <Link href="/analytics/content" className="text-sm text-purple-400">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {mockTopContent.map((content, index) => (
              <div
                key={content.id}
                className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl"
              >
                <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium truncate">{content.title}</h3>
                  <p className="text-xs text-gray-500">{content.platform}</p>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">{formatNumber(content.views)}</div>
                  <div className="text-xs text-gray-500">{content.engagement}% eng.</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/analytics/audience"
            className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
          >
            <UsersIcon className="w-6 h-6 text-purple-400 mb-2" />
            <h3 className="font-medium text-sm">Audience Insights</h3>
            <p className="text-xs text-gray-500 mt-1">Demographics & behavior</p>
          </Link>
          <Link
            href="/analytics/trends"
            className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
          >
            <TrendIcon className="w-6 h-6 text-pink-400 mb-2" />
            <h3 className="font-medium text-sm">Trend Radar</h3>
            <p className="text-xs text-gray-500 mt-1">AI topic monitoring</p>
          </Link>
          <Link
            href="/analytics/competitors"
            className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
          >
            <CompetitorIcon className="w-6 h-6 text-blue-400 mb-2" />
            <h3 className="font-medium text-sm">Competitor Analysis</h3>
            <p className="text-xs text-gray-500 mt-1">Benchmark performance</p>
          </Link>
          <Link
            href="/analytics/viral"
            className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
          >
            <ViralIcon className="w-6 h-6 text-orange-400 mb-2" />
            <h3 className="font-medium text-sm">Viral Predictor</h3>
            <p className="text-xs text-gray-500 mt-1">Score your content</p>
          </Link>
        </div>
      </div>

      <BottomNav />
    </main>
  );
}

// Utility
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

// Icons
function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
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

function TrendUpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}

function TrendIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
    </svg>
  );
}

function CompetitorIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function ViralIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}
