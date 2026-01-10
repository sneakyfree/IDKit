"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Heart,
  MessageCircle,
  Share2,
  Bookmark,
  Music,
  CheckCircle,
} from "lucide-react";
import { cn, formatCount } from "@/lib/utils";
import type { FeedPostResponse } from "@/lib/api";
import { posts } from "@/lib/api";

interface PostCardProps {
  post: FeedPostResponse;
}

export function PostCard({ post }: PostCardProps) {
  const [isLiked, setIsLiked] = useState(post.is_liked);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [isSaved, setIsSaved] = useState(post.is_saved);
  const [isLikeAnimating, setIsLikeAnimating] = useState(false);

  const handleLike = async () => {
    // Optimistic update
    setIsLiked(!isLiked);
    setLikeCount((prev) => (isLiked ? prev - 1 : prev + 1));
    setIsLikeAnimating(true);

    try {
      if (isLiked) {
        await posts.unlike(post.id);
      } else {
        await posts.like(post.id);
      }
    } catch {
      // Revert on error
      setIsLiked(isLiked);
      setLikeCount(post.like_count);
    }

    setTimeout(() => setIsLikeAnimating(false), 300);
  };

  const handleSave = async () => {
    setIsSaved(!isSaved);

    try {
      if (isSaved) {
        await posts.unsave(post.id);
      } else {
        await posts.save(post.id);
      }
    } catch {
      setIsSaved(isSaved);
    }
  };

  const handleDoubleTap = () => {
    if (!isLiked) {
      handleLike();
    }
  };

  return (
    <div
      className="feed-item relative w-full bg-black"
      onDoubleClick={handleDoubleTap}
    >
      {/* Media */}
      <div className="absolute inset-0">
        {post.post_type === "video" && post.media_urls[0] ? (
          <video
            src={post.media_urls[0]}
            className="w-full h-full object-cover"
            loop
            muted
            playsInline
            autoPlay
          />
        ) : post.media_urls[0] ? (
          <Image
            src={post.media_urls[0]}
            alt=""
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-b from-gray-900 to-black flex items-center justify-center p-8">
            <p className="text-xl text-center">{post.content_text}</p>
          </div>
        )}
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80 pointer-events-none" />

      {/* Right side actions */}
      <div className="absolute right-3 bottom-32 flex flex-col items-center gap-5">
        {/* Author avatar */}
        <Link
          href={`/@${post.author.username}`}
          className="relative mb-2"
        >
          <div className="w-12 h-12 rounded-full border-2 border-white overflow-hidden bg-gray-800">
            {post.author.avatar_url ? (
              <Image
                src={post.author.avatar_url}
                alt={post.author.display_name}
                width={48}
                height={48}
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-lg font-bold">
                {post.author.display_name[0]}
              </div>
            )}
          </div>
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center">
            <span className="text-xs">+</span>
          </div>
        </Link>

        {/* Like */}
        <button
          onClick={handleLike}
          className="flex flex-col items-center action-btn"
        >
          <Heart
            className={cn(
              "w-8 h-8 transition-all",
              isLiked && "fill-red-500 text-red-500",
              isLikeAnimating && "heart-pulse"
            )}
          />
          <span className="text-xs mt-1">{formatCount(likeCount)}</span>
        </button>

        {/* Comments */}
        <Link
          href={`/post/${post.id}/comments`}
          className="flex flex-col items-center action-btn"
        >
          <MessageCircle className="w-8 h-8" />
          <span className="text-xs mt-1">{formatCount(post.comment_count)}</span>
        </Link>

        {/* Save */}
        <button
          onClick={handleSave}
          className="flex flex-col items-center action-btn"
        >
          <Bookmark
            className={cn(
              "w-8 h-8 transition-all",
              isSaved && "fill-yellow-400 text-yellow-400"
            )}
          />
          <span className="text-xs mt-1">{formatCount(post.save_count)}</span>
        </button>

        {/* Share */}
        <button className="flex flex-col items-center action-btn">
          <Share2 className="w-8 h-8" />
          <span className="text-xs mt-1">{formatCount(post.share_count)}</span>
        </button>
      </div>

      {/* Bottom info */}
      <div className="absolute left-3 right-20 bottom-20">
        {/* Author */}
        <Link
          href={`/@${post.author.username}`}
          className="flex items-center gap-2 mb-2"
        >
          <span className="font-bold">@{post.author.username}</span>
          {post.author.is_verified && (
            <CheckCircle className="w-4 h-4 text-primary-400 fill-primary-400" />
          )}
        </Link>

        {/* Caption */}
        {post.content_text && (
          <p className="text-sm line-clamp-2 mb-2">{post.content_text}</p>
        )}

        {/* Hashtags */}
        {post.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {post.hashtags.slice(0, 3).map((tag) => (
              <Link
                key={tag}
                href={`/tag/${tag}`}
                className="text-sm font-medium hover:underline"
              >
                #{tag}
              </Link>
            ))}
          </div>
        )}

        {/* AI Generated badge */}
        {post.ai_generated && (
          <div className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full text-xs">
            <span className="text-primary-400">AI</span>
            <span>Generated</span>
          </div>
        )}

        {/* Sound/Music */}
        <div className="flex items-center gap-2 mt-2">
          <Music className="w-4 h-4" />
          <div className="text-xs truncate animate-marquee">
            Original sound - @{post.author.username}
          </div>
        </div>
      </div>
    </div>
  );
}
