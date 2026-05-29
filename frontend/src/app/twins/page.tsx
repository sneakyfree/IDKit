"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { apiRequest } from "@/lib/api";

interface Twin {
  id: string;
  name: string;
  description: string;
  avatarUrl: string | null;
  voiceCloned: boolean;
  avatarTrained: boolean;
  lastUsed: string;
  videosGenerated: number;
}

type TabType = "twins" | "voices" | "avatars";

export default function TwinsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("twins");
  const [twins, setTwins] = useState<Twin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTwins() {
      try {
        const response = await apiRequest<Twin[]>("/api/v1/twins");
        setTwins(Array.isArray(response) ? response : []);
      } catch {
        setTwins([]);
      } finally {
        setLoading(false);
      }
    }
    fetchTwins();
  }, []);

  const mockTwins = twins;

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold text-white">AI Twin Lab</h1>
          <Link
            href="/twins/create"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
          >
            + New Twin
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          {(["twins", "voices", "avatars"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === tab
                  ? "text-white border-b-2 border-purple-500"
                  : "text-gray-300"
                }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      {activeTab === "twins" && (
        <div className="p-4 space-y-4">
          {/* Info Card */}
          <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 rounded-2xl p-4 border border-purple-500/30">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-500/30 flex items-center justify-center flex-shrink-0">
                <SparklesIcon className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold">Create Your AI Twin</h3>
                <p className="text-sm text-gray-300 mt-1">
                  Train your AI clone with your voice and appearance. Generate unlimited
                  videos, podcasts, and content automatically.
                </p>
              </div>
            </div>
          </div>

          {/* Twins List */}
          <div className="space-y-3">
            {mockTwins.map((twin) => (
              <Link
                key={twin.id}
                href={`/twins/${twin.id}`}
                className="block bg-gray-900 rounded-2xl p-4 hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-start gap-4">
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5 flex-shrink-0">
                    <div className="w-full h-full rounded-xl bg-gray-800 flex items-center justify-center">
                      <UserIcon className="w-8 h-8 text-gray-300" />
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold">{twin.name}</h3>
                    <p className="text-sm text-gray-200 mt-0.5">{twin.description}</p>

                    {/* Status */}
                    <div className="flex items-center gap-3 mt-2">
                      <div className="flex items-center gap-1">
                        {twin.voiceCloned ? (
                          <CheckCircleIcon className="w-4 h-4 text-green-500" />
                        ) : (
                          <CircleIcon className="w-4 h-4 text-gray-300" />
                        )}
                        <span className="text-xs text-gray-200">Voice</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {twin.avatarTrained ? (
                          <CheckCircleIcon className="w-4 h-4 text-green-500" />
                        ) : (
                          <CircleIcon className="w-4 h-4 text-gray-300" />
                        )}
                        <span className="text-xs text-gray-200">Avatar</span>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-300">
                      <span>{twin.videosGenerated} videos generated</span>
                      <span>Last used {twin.lastUsed}</span>
                    </div>
                  </div>

                  <ChevronRightIcon className="w-5 h-5 text-gray-300 flex-shrink-0" />
                </div>
              </Link>
            ))}
          </div>

          {/* Create New Twin Card */}
          <Link
            href="/twins/create"
            className="block bg-gray-900 rounded-2xl p-6 border-2 border-dashed border-gray-700 hover:border-purple-500 hover:bg-gray-800 transition-all text-center"
          >
            <div className="w-14 h-14 mx-auto rounded-full bg-gray-800 flex items-center justify-center mb-3">
              <PlusIcon className="w-7 h-7 text-gray-300" />
            </div>
            <h3 className="font-semibold">Create New AI Twin</h3>
            <p className="text-sm text-gray-200 mt-1">
              Clone your voice and appearance
            </p>
          </Link>
        </div>
      )}

      {activeTab === "voices" && (
        <div className="p-4 space-y-4">
          {/* Voice Cloning Section */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <h3 className="font-semibold mb-3">Cloned Voices</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl">
                <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <MicIcon className="w-5 h-5 text-purple-400" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-sm">Professional Voice</h4>
                  <p className="text-xs text-gray-200">English (US) • Female</p>
                </div>
                <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                  <PlayIcon className="w-5 h-5" />
                </button>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-xl">
                <div className="w-10 h-10 rounded-full bg-pink-500/20 flex items-center justify-center">
                  <MicIcon className="w-5 h-5 text-pink-400" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-sm">Casual Voice</h4>
                  <p className="text-xs text-gray-200">English (US) • Female</p>
                </div>
                <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                  <PlayIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
            <Link
              href="/twins/voice/new"
              className="mt-4 w-full py-3 bg-gray-800 rounded-xl text-sm font-medium text-center block hover:bg-gray-700 transition-colors"
            >
              + Clone New Voice
            </Link>
          </div>

          {/* Voice Settings */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <h3 className="font-semibold mb-3">Voice Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-200">Default Voice</label>
                <select aria-label="Filter or select option" className="mt-1 w-full bg-gray-800 rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option>Professional Voice</option>
                  <option>Casual Voice</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-200">Speaking Speed</label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  defaultValue="1"
                  className="mt-2 w-full"
                />
                <div className="flex justify-between text-xs text-gray-300 mt-1">
                  <span>0.5x</span>
                  <span>1x</span>
                  <span>2x</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "avatars" && (
        <div className="p-4 space-y-4">
          {/* Avatar Training Section */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <h3 className="font-semibold mb-3">Trained Avatars</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="aspect-square rounded-xl bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5">
                <div className="w-full h-full rounded-xl bg-gray-800 flex flex-col items-center justify-center">
                  <UserIcon className="w-12 h-12 text-gray-300" />
                  <span className="text-xs text-gray-200 mt-2">Professional</span>
                </div>
              </div>
              <Link
                href="/twins/avatar/new"
                className="aspect-square rounded-xl border-2 border-dashed border-gray-700 flex flex-col items-center justify-center hover:border-purple-500 hover:bg-gray-800 transition-all"
              >
                <PlusIcon className="w-8 h-8 text-gray-300" />
                <span className="text-xs text-gray-200 mt-2">Train New</span>
              </Link>
            </div>
          </div>

          {/* Training Tips */}
          <div className="bg-gray-900 rounded-2xl p-4">
            <h3 className="font-semibold mb-3">Training Tips</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-start gap-2">
                <CheckIcon className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                Upload 10-20 high-quality photos
              </li>
              <li className="flex items-start gap-2">
                <CheckIcon className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                Use different angles and expressions
              </li>
              <li className="flex items-start gap-2">
                <CheckIcon className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                Good lighting improves results
              </li>
              <li className="flex items-start gap-2">
                <CheckIcon className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                Avoid sunglasses or heavy filters
              </li>
            </ul>
          </div>
        </div>
      )}

      <BottomNav />
    </main>
  );
}

// Icons
function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clipRule="evenodd" />
    </svg>
  );
}

function CircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle cx="12" cy="12" r="9" strokeWidth={2} />
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

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
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

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}
