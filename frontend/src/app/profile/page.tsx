"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { profiles } from "@/lib/api";

interface UserProfile {
  id: string;
  username: string;
  displayName: string;
  bio: string;
  avatarUrl: string | null;
  coverUrl: string | null;
  isVerified: boolean;
  followerCount: number;
  followingCount: number;
  postCount: number;
  niches: string[];
  website: string;
}

interface Post {
  id: string;
  thumbnailUrl: string | null;
  viewCount: number;
  type: string;
}

type TabType = "posts" | "likes" | "saved";

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<TabType>("posts");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const response = await profiles.getMe();
        setUser({
          id: response.id || "1",
          username: response.username || "creator",
          displayName: response.display_name || response.username || "Creator",
          bio: response.bio || "",
          avatarUrl: response.avatar_url || null,
          coverUrl: null,
          isVerified: response.is_verified || false,
          followerCount: response.follower_count || 0,
          followingCount: response.following_count || 0,
          postCount: response.post_count || 0,
          niches: response.niche_tags || [],
          website: response.website_url || "",
        });
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  const mockUser = user || {
    id: "1", username: "creator", displayName: "Creator", bio: "",
    avatarUrl: null, coverUrl: null, isVerified: false,
    followerCount: 0, followingCount: 0, postCount: 0, niches: [], website: "",
  };
  const mockPosts = posts;

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <button className="p-2 -ml-2">
            <ChevronLeftIcon className="w-6 h-6" />
          </button>
          <h1 className="font-semibold">@{mockUser.username}</h1>
          <button className="p-2 -mr-2">
            <MenuIcon className="w-6 h-6" />
          </button>
        </div>
      </header>

      {/* Profile Info */}
      <div className="px-4 pt-4">
        {/* Avatar & Stats */}
        <div className="flex items-center gap-6">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5">
            <div className="w-full h-full rounded-full bg-gray-800 flex items-center justify-center">
              <span className="text-2xl font-bold">
                {mockUser.displayName.charAt(0)}
              </span>
            </div>
          </div>

          {/* Stats */}
          <div className="flex-1 flex justify-around">
            <div className="text-center">
              <div className="text-xl font-bold text-white">{mockUser.postCount}</div>
              <div className="text-gray-200 text-xs">Posts</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-white">
                {formatNumber(mockUser.followerCount)}
              </div>
              <div className="text-gray-200 text-xs">Followers</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-white">
                {formatNumber(mockUser.followingCount)}
              </div>
              <div className="text-gray-200 text-xs">Following</div>
            </div>
          </div>
        </div>

        {/* Name & Bio */}
        <div className="mt-4">
          <div className="flex items-center gap-1">
            <h2 className="font-semibold">{mockUser.displayName}</h2>
            {mockUser.isVerified && (
              <VerifiedIcon className="w-4 h-4 text-blue-500" />
            )}
          </div>
          <p className="text-gray-300 text-sm mt-1">{mockUser.bio}</p>

          {/* Niches */}
          <div className="flex flex-wrap gap-2 mt-3">
            {mockUser.niches.map((niche) => (
              <span
                key={niche}
                className="px-2.5 py-1 bg-gray-800 rounded-full text-xs text-gray-300"
              >
                {niche}
              </span>
            ))}
          </div>

          {/* Website */}
          {mockUser.website && (
            <a
              href={mockUser.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 mt-2 block"
            >
              {mockUser.website.replace("https://", "")}
            </a>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mt-4">
          <Link
            href="/profile/edit"
            className="flex-1 py-2 bg-gray-800 rounded-lg text-center text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Edit Profile
          </Link>
          <Link
            href="/profile/share"
            className="flex-1 py-2 bg-gray-800 rounded-lg text-center text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Share Profile
          </Link>
          <Link
            href="/studio"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Studio
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800 mt-6">
        <button
          onClick={() => setActiveTab("posts")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "posts"
            ? "text-white border-b-2 border-white"
            : "text-gray-300"
            }`}
        >
          <GridIcon className="w-5 h-5 mx-auto" />
        </button>
        <button
          onClick={() => setActiveTab("likes")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "likes"
            ? "text-white border-b-2 border-white"
            : "text-gray-300"
            }`}
        >
          <HeartIcon className="w-5 h-5 mx-auto" />
        </button>
        <button
          onClick={() => setActiveTab("saved")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "saved"
            ? "text-white border-b-2 border-white"
            : "text-gray-300"
            }`}
        >
          <BookmarkIcon className="w-5 h-5 mx-auto" />
        </button>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-3 gap-0.5">
        {mockPosts.map((post) => (
          <Link
            key={post.id}
            href={`/posts/${post.id}`}
            className="aspect-square bg-gray-900 relative group"
          >
            {/* Placeholder thumbnail */}
            <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900" />

            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <div className="flex items-center gap-1 text-sm">
                <PlayIcon className="w-4 h-4" />
                <span>{formatNumber(post.viewCount)}</span>
              </div>
            </div>

            {/* Video indicator */}
            {post.type === "video" && (
              <div className="absolute top-2 right-2">
                <PlayIcon className="w-4 h-4" />
              </div>
            )}
          </Link>
        ))}
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </main>
  );
}

// Utility functions
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

// Icons
function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  );
}

function MenuIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function VerifiedIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
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

function BookmarkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
    </svg>
  );
}

function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}
