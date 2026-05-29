"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";

type TimeRange = "7d" | "30d" | "90d" | "all";

interface AnalyticsOverview {
  totalFollowers: number;
  followerChange: number;
  followerChangePercent: number;
  totalViews: number;
  viewChange: number;
  viewChangePercent: number;
  totalEngagements: number;
  engagementRate: number;
  engagementChange: number;
}

interface PlatformStat {
  platform: string;
  followers: number;
  views: number;
  growth: number;
  color: string;
}

interface TopContent {
  id: string;
  title: string;
  platform: string;
  views: number;
  engagement: number;
}

const PLATFORM_COLORS: Record<string, string> = {
  tiktok: "bg-pink-500",
  instagram: "bg-purple-500",
  youtube: "bg-red-500",
  twitter: "bg-blue-500",
  facebook: "bg-blue-600",
  linkedin: "bg-blue-700",
};

const DEFAULT_OVERVIEW: AnalyticsOverview = {
  totalFollowers: 0,
  followerChange: 0,
  followerChangePercent: 0,
  totalViews: 0,
  viewChange: 0,
  viewChangePercent: 0,
  totalEngagements: 0,
  engagementRate: 0,
  engagementChange: 0,
};

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");
  const [overview, setOverview] = useState<AnalyticsOverview>(DEFAULT_OVERVIEW);
  const [platformStats, setPlatformStats] = useState<PlatformStat[]>([]);
  const [topContent, setTopContent] = useState<TopContent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/social/analytics/overview?period=${timeRange}`,
        { headers }
      );

      if (!response.ok) throw new Error("Failed to load analytics");

      const data = await response.json();

      // Map backend response to frontend types
      const totalFollowers = data.total_followers || 0;
      const platforms: PlatformStat[] = Object.entries(
        (data.platforms || {}) as Record<string, { accounts: number; followers: number }>
      ).map(([name, info]) => ({
        platform: name.charAt(0).toUpperCase() + name.slice(1),
        followers: info.followers || 0,
        views: 0,
        growth: 0,
        color: PLATFORM_COLORS[name.toLowerCase()] || "bg-gray-500",
      }));

      setOverview({
        ...DEFAULT_OVERVIEW,
        totalFollowers,
      });
      setPlatformStats(platforms);
      setTopContent([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setIsLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold text-white">Analytics</h1>
          <Link
            href="/analytics/export"
            className="px-4 py-2 bg-gray-800 rounded-full text-sm font-medium text-white hover:bg-gray-700 transition-colors"
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
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${timeRange === range
                ? "bg-white text-black"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                }`}
            >
              {range === "all" ? "All Time" : range.replace("d", " Days")}
            </button>
          ))}
        </div>
      </header>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="mx-4 mt-4 bg-red-900/30 border border-red-500/50 rounded-xl p-4">
          <p className="text-red-300 text-sm">{error}</p>
          <button onClick={fetchAnalytics} className="mt-2 text-sm text-purple-400 hover:text-purple-300">
            Try again
          </button>
        </div>
      )}

      {/* Overview Cards */}
      {!isLoading && (
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {/* Followers */}
            <div className="bg-gray-900 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-gray-200 text-sm mb-2">
                <UsersIcon className="w-4 h-4" />
                Followers
              </div>
              <div className="text-2xl font-bold">
                {formatNumber(overview.totalFollowers)}
              </div>
              <div className="flex items-center gap-1 mt-1">
                <TrendUpIcon className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-500">
                  +{formatNumber(overview.followerChange)} ({overview.followerChangePercent}%)
                </span>
              </div>
            </div>

            {/* Views */}
            <div className="bg-gray-900 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-gray-200 text-sm mb-2">
                <EyeIcon className="w-4 h-4" />
                Views
              </div>
              <div className="text-2xl font-bold">
                {formatNumber(overview.totalViews)}
              </div>
              <div className="flex items-center gap-1 mt-1">
                <TrendUpIcon className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-500">
                  +{formatNumber(overview.viewChange)} ({overview.viewChangePercent}%)
                </span>
              </div>
            </div>

            {/* Engagements */}
            <div className="bg-gray-900 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-gray-200 text-sm mb-2">
                <HeartIcon className="w-4 h-4" />
                Engagements
              </div>
              <div className="text-2xl font-bold">
                {formatNumber(overview.totalEngagements)}
              </div>
              <div className="text-sm text-gray-300 mt-1">
                Likes, comments, shares
              </div>
            </div>

            {/* Engagement Rate */}
            <div className="bg-gray-900 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-gray-200 text-sm mb-2">
                <ChartIcon className="w-4 h-4" />
                Eng. Rate
              </div>
              <div className="text-2xl font-bold">
                {overview.engagementRate}%
              </div>
              <div className="flex items-center gap-1 mt-1">
                <TrendUpIcon className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-500">
                  +{overview.engagementChange}%
                </span>
              </div>
            </div>
          </div>

          {/* Platform Breakdown */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <h2 className="font-semibold mb-4">Platform Performance</h2>
            <div className="space-y-4">
              {platformStats.map((platform) => (
                <div key={platform.platform}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${platform.color}`} />
                      <span className="text-sm font-medium">{platform.platform}</span>
                    </div>
                    <span className="text-sm text-gray-200">
                      {formatNumber(platform.followers)} followers
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${platform.color}`}
                        style={{
                          width: `${overview.totalFollowers > 0 ? (platform.followers / overview.totalFollowers) * 100 : 0}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 w-20 text-right">
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
              {topContent.length === 0 ? (
                <p className="text-sm text-gray-300 text-center py-4">Connect social accounts to see top content</p>
              ) : topContent.map((content, index) => (
                <div
                  key={content.id}
                  className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl"
                >
                  <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium truncate">{content.title}</h3>
                    <p className="text-xs text-gray-300">{content.platform}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{formatNumber(content.views)}</div>
                    <div className="text-xs text-gray-300">{content.engagement}% eng.</div>
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
              <p className="text-xs text-gray-300 mt-1">Demographics & behavior</p>
            </Link>
            <Link
              href="/analytics/trends"
              className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
            >
              <TrendIcon className="w-6 h-6 text-pink-400 mb-2" />
              <h3 className="font-medium text-sm">Trend Radar</h3>
              <p className="text-xs text-gray-300 mt-1">AI topic monitoring</p>
            </Link>
            <Link
              href="/analytics/competitors"
              className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
            >
              <CompetitorIcon className="w-6 h-6 text-blue-400 mb-2" />
              <h3 className="font-medium text-sm">Competitor Analysis</h3>
              <p className="text-xs text-gray-300 mt-1">Benchmark performance</p>
            </Link>
            <Link
              href="/analytics/viral"
              className="bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
            >
              <ViralIcon className="w-6 h-6 text-orange-400 mb-2" />
              <h3 className="font-medium text-sm">Viral Predictor</h3>
              <p className="text-xs text-gray-300 mt-1">Score your content</p>
            </Link>
            <Link
              href="/roi"
              className="bg-gradient-to-br from-green-900/40 to-emerald-900/20 rounded-2xl p-4 hover:from-green-900/60 hover:to-emerald-900/40 transition-colors border border-green-500/30"
            >
              <ROIIcon className="w-6 h-6 text-green-400 mb-2" />
              <h3 className="font-medium text-sm">ROI Calculator</h3>
              <p className="text-xs text-gray-300 mt-1">Track profitability</p>
            </Link>
            <Link
              href="/settings/payouts"
              className="bg-gradient-to-br from-purple-900/40 to-purple-900/20 rounded-2xl p-4 hover:from-purple-900/60 hover:to-purple-900/40 transition-colors border border-purple-500/30"
            >
              <PayoutIcon className="w-6 h-6 text-purple-400 mb-2" />
              <h3 className="font-medium text-sm">Payouts</h3>
              <p className="text-xs text-gray-300 mt-1">Manage earnings</p>
            </Link>
          </div>
        </div>
      )}

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

function ROIIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function PayoutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  );
}

