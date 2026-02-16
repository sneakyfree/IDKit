"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { apiRequest } from "@/lib/api";

interface Podcast {
  id: string;
  title: string;
  description: string;
  coverUrl: string | null;
  episodeCount: number;
  subscriberCount: number;
  totalPlays: number;
}

interface Episode {
  id: string;
  podcastId: string;
  title: string;
  description: string;
  duration: number;
  status: string;
  publishedAt: string | null;
  plays: number;
}

export default function PodcastPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await apiRequest<{ podcasts: Podcast[]; episodes: Episode[] } | Podcast[]>("/api/v1/podcasts");
        if (Array.isArray(response)) {
          setPodcasts(response);
        } else {
          setPodcasts(response.podcasts || []);
          setEpisodes(response.episodes || []);
        }
      } catch {
        setPodcasts([]);
        setEpisodes([]);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const mockEpisodes = episodes;
  const podcast = podcasts[0] || null;

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Podcast Lab</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
          >
            + New Episode
          </button>
        </div>
      </header>

      {/* One-Click Generate Banner */}
      <div className="p-4">
        <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 rounded-2xl p-4 border border-purple-500/30">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-full bg-purple-500/30 flex items-center justify-center flex-shrink-0">
              <SparklesIcon className="w-6 h-6 text-purple-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Insta Podcast</h3>
              <p className="text-sm text-gray-300 mt-1">
                Generate a complete episode from just a topic. AI writes the script,
                clones your voice, and creates the video.
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-3 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
              >
                Generate Episode
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Podcast Info */}
      {podcast && (
        <div className="px-4">
          <div className="bg-gray-900 rounded-2xl p-4">
            <div className="flex gap-4">
              {/* Cover */}
              <div className="w-24 h-24 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                <MicIcon className="w-10 h-10 text-white" />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h2 className="font-bold text-lg">{podcast.title}</h2>
                <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                  {podcast.description}
                </p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>{podcast.episodeCount} episodes</span>
                  <span>{formatNumber(podcast.subscriberCount)} subscribers</span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="bg-gray-800 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{formatNumber(podcast.totalPlays)}</div>
                <div className="text-xs text-gray-400">Total Plays</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{podcast.episodeCount}</div>
                <div className="text-xs text-gray-400">Episodes</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 text-center">
                <div className="text-lg font-bold">{formatNumber(podcast.subscriberCount)}</div>
                <div className="text-xs text-gray-400">Subscribers</div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-4">
              <Link
                href={`/podcast/${podcast.id}/settings`}
                className="flex-1 py-2 bg-gray-800 rounded-lg text-center text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                Settings
              </Link>
              <Link
                href={`/podcast/${podcast.id}/analytics`}
                className="flex-1 py-2 bg-gray-800 rounded-lg text-center text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                Analytics
              </Link>
              <Link
                href={`/podcast/${podcast.id}/distribute`}
                className="flex-1 py-2 bg-gray-800 rounded-lg text-center text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                Distribute
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Episodes */}
      <div className="px-4 mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Episodes</h2>
          <span className="text-sm text-gray-500">{mockEpisodes.length} total</span>
        </div>

        <div className="space-y-3">
          {mockEpisodes.map((episode) => (
            <Link
              key={episode.id}
              href={`/podcast/episodes/${episode.id}`}
              className="block bg-gray-900 rounded-xl p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex gap-3">
                {/* Thumbnail */}
                <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center flex-shrink-0">
                  <MicIcon className="w-6 h-6 text-gray-500" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-sm truncate">{episode.title}</h3>
                    {episode.status === "draft" && (
                      <span className="px-2 py-0.5 bg-gray-700 rounded-full text-xs">
                        Draft
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                    {episode.description}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    {episode.duration > 0 && (
                      <span>{formatDuration(episode.duration)}</span>
                    )}
                    {episode.publishedAt && <span>{episode.publishedAt}</span>}
                    {episode.plays > 0 && <span>{formatNumber(episode.plays)} plays</span>}
                  </div>
                </div>

                {/* Play Button */}
                {episode.status === "published" && (
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      // Play episode
                    }}
                    className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0 hover:bg-purple-700 transition-colors"
                  >
                    <PlayIcon className="w-5 h-5 ml-0.5" />
                  </button>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Create Episode Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="relative w-full max-w-lg bg-gray-900 rounded-t-3xl p-6 animate-slide-up">
            <div className="w-12 h-1 bg-gray-700 rounded-full mx-auto mb-6" />

            <h2 className="text-xl font-bold mb-6">Create New Episode</h2>

            {/* Quick Generate */}
            <div className="space-y-4">
              <div>
                <label htmlFor="episode-topic" className="text-sm font-medium text-gray-300">
                  Episode Topic
                </label>
                <input
                  id="episode-topic"
                  type="text"
                  placeholder="e.g., The Future of AI in Marketing"
                  className="mt-2 w-full bg-gray-800 rounded-xl py-3 px-4 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label id="style-label" className="text-sm font-medium text-gray-300">Style</label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {["Conversational", "Educational", "Storytelling"].map((style) => (
                    <button
                      key={style}
                      className="py-2 px-3 bg-gray-800 rounded-lg text-sm hover:bg-gray-700 transition-colors"
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label id="duration-label" className="text-sm font-medium text-gray-300">Duration</label>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  {["5 min", "10 min", "15 min", "30 min"].map((duration) => (
                    <button
                      key={duration}
                      className="py-2 px-3 bg-gray-800 rounded-lg text-sm hover:bg-gray-700 transition-colors"
                    >
                      {duration}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-gray-800 rounded-xl">
                <input type="checkbox" id="useAiTwin" className="w-4 h-4" />
                <label htmlFor="useAiTwin" className="text-sm">
                  Use AI Twin voice and avatar
                </label>
              </div>

              <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-medium hover:opacity-90 transition-opacity">
                Generate Episode
              </button>

              <div className="text-center">
                <Link
                  href="/podcast/episodes/new"
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Or create manually →
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      <BottomNav />
    </main>
  );
}

// Utility functions
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// Icons
function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
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

function PlayIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}
