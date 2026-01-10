"use client";

import { useState } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";

type ContentType = "all" | "video" | "post" | "podcast";

// Mock content data
const mockContent = [
  {
    id: "1",
    title: "How AI is Changing Content Creation",
    type: "video",
    status: "published",
    createdAt: "2024-01-15",
    views: 15200,
    likes: 890,
    thumbnailUrl: null,
  },
  {
    id: "2",
    title: "My Morning Routine - January Edition",
    type: "video",
    status: "draft",
    createdAt: "2024-01-14",
    views: 0,
    likes: 0,
    thumbnailUrl: null,
  },
  {
    id: "3",
    title: "5 Tips for Growing Your Audience",
    type: "post",
    status: "scheduled",
    createdAt: "2024-01-13",
    scheduledFor: "2024-01-20",
    views: 0,
    likes: 0,
    thumbnailUrl: null,
  },
  {
    id: "4",
    title: "Tech Talk Episode 12 - AI Trends 2024",
    type: "podcast",
    status: "published",
    createdAt: "2024-01-10",
    views: 8500,
    likes: 420,
    thumbnailUrl: null,
  },
];

export default function StudioPage() {
  const [activeFilter, setActiveFilter] = useState<ContentType>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredContent = mockContent.filter((item) => {
    if (activeFilter !== "all" && item.type !== activeFilter) return false;
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase()))
      return false;
    return true;
  });

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Content Studio</h1>
          <Link
            href="/studio/create"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
          >
            + Create
          </Link>
        </div>

        {/* Search */}
        <div className="px-4 pb-3">
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-900 rounded-full py-2.5 pl-10 pr-4 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 px-4 pb-3 overflow-x-auto">
          {(["all", "video", "post", "podcast"] as ContentType[]).map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                activeFilter === filter
                  ? "bg-white text-black"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {/* Quick Actions */}
      <div className="px-4 py-4">
        <h2 className="text-sm font-medium text-gray-400 mb-3">Quick Create</h2>
        <div className="grid grid-cols-4 gap-3">
          <Link
            href="/studio/create/video"
            className="flex flex-col items-center gap-2 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
              <VideoIcon className="w-5 h-5 text-red-500" />
            </div>
            <span className="text-xs text-gray-300">Video</span>
          </Link>
          <Link
            href="/studio/create/post"
            className="flex flex-col items-center gap-2 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
              <EditIcon className="w-5 h-5 text-blue-500" />
            </div>
            <span className="text-xs text-gray-300">Post</span>
          </Link>
          <Link
            href="/podcast"
            className="flex flex-col items-center gap-2 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
              <MicIcon className="w-5 h-5 text-purple-500" />
            </div>
            <span className="text-xs text-gray-300">Podcast</span>
          </Link>
          <Link
            href="/twins"
            className="flex flex-col items-center gap-2 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-pink-500/20 flex items-center justify-center">
              <SparklesIcon className="w-5 h-5 text-pink-500" />
            </div>
            <span className="text-xs text-gray-300">AI Twin</span>
          </Link>
        </div>
      </div>

      {/* Content List */}
      <div className="px-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-400">Your Content</h2>
          <span className="text-xs text-gray-500">
            {filteredContent.length} items
          </span>
        </div>

        <div className="space-y-3">
          {filteredContent.map((item) => (
            <Link
              key={item.id}
              href={`/studio/edit/${item.id}`}
              className="flex gap-3 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
            >
              {/* Thumbnail */}
              <div className="w-24 h-16 rounded-lg bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center flex-shrink-0">
                {item.type === "video" && <VideoIcon className="w-6 h-6 text-gray-500" />}
                {item.type === "post" && <EditIcon className="w-6 h-6 text-gray-500" />}
                {item.type === "podcast" && <MicIcon className="w-6 h-6 text-gray-500" />}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-sm truncate">{item.title}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <StatusBadge status={item.status} />
                  <span className="text-xs text-gray-500">{item.createdAt}</span>
                </div>
                {item.status === "published" && (
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>{formatNumber(item.views)} views</span>
                    <span>{formatNumber(item.likes)} likes</span>
                  </div>
                )}
              </div>

              {/* Menu */}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  // Open menu
                }}
                className="p-2 -mr-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <MoreIcon className="w-5 h-5 text-gray-400" />
              </button>
            </Link>
          ))}
        </div>

        {filteredContent.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
              <EditIcon className="w-8 h-8 text-gray-600" />
            </div>
            <h3 className="font-medium text-gray-400">No content found</h3>
            <p className="text-sm text-gray-500 mt-1">
              Create your first piece of content to get started
            </p>
          </div>
        )}
      </div>

      <BottomNav />
    </main>
  );
}

// Components
function StatusBadge({ status }: { status: string }) {
  const styles = {
    published: "bg-green-500/20 text-green-400",
    draft: "bg-gray-500/20 text-gray-400",
    scheduled: "bg-blue-500/20 text-blue-400",
    processing: "bg-yellow-500/20 text-yellow-400",
  };

  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        styles[status as keyof typeof styles] || styles.draft
      }`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// Utility
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

// Icons
function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

function VideoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function EditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
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

function MoreIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
    </svg>
  );
}
