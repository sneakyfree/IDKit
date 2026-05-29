"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { PostCard } from "./PostCard";
import { feed } from "@/lib/api";
import type { FeedPostResponse } from "@/lib/api";
import { useFeedStore } from "@/lib/store";
import { Loader2 } from "lucide-react";

export function FeedScroll() {
  const [posts, setPosts] = useState<FeedPostResponse[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { activeTab } = useFeedStore();

  const loadPosts = useCallback(async (cursor?: string) => {
    if (cursor) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }

    try {
      const response = await (activeTab === "for-you"
        ? feed.getPersonalized(cursor)
        : feed.getFollowing());

      if (cursor) {
        setPosts((prev) => [...prev, ...response.posts]);
      } else {
        setPosts(response.posts);
      }
      setNextCursor(response.next_cursor);
    } catch (error) {
      console.error("Failed to load feed:", error);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [activeTab]);

  // Initial load
  useEffect(() => {
    setPosts([]);
    setNextCursor(null);
    loadPosts();
  }, [activeTab, loadPosts]);

  // Infinite scroll observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const last = entries[0];
        if (last.isIntersecting && nextCursor && !isLoadingMore) {
          loadPosts(nextCursor);
        }
      },
      { threshold: 0.5 }
    );

    const lastPost = container.lastElementChild;
    if (lastPost) {
      observer.observe(lastPost);
    }

    return () => observer.disconnect();
  }, [posts, nextCursor, isLoadingMore, loadPosts]);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="h-screen flex flex-col items-center justify-center text-gray-200">
        <p className="text-xl mb-2">No posts yet</p>
        <p className="text-sm">
          {activeTab === "following"
            ? "Follow creators to see their posts"
            : "Be the first to post!"}
        </p>
        <Link href="/studio" className="mt-4 px-5 py-2 bg-purple-600 text-white rounded-full text-sm font-medium hover:bg-purple-700 transition-colors">
          Create your first post
        </Link>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="feed-scroll hide-scrollbar"
    >
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      {isLoadingMore && (
        <div className="h-20 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
        </div>
      )}
    </div>
  );
}
