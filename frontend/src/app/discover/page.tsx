"use client";

import { BottomNav } from "@/components/nav/BottomNav";
import { Search, TrendingUp, Users } from "lucide-react";

export default function DiscoverPage() {
  return (
    <div className="min-h-screen bg-black text-white pb-20">
      {/* Search Header */}
      <div className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search creators, topics, content..."
            className="w-full pl-10 pr-4 py-3 bg-gray-900 rounded-full text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
      </div>

      {/* Trending Section */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-purple-500" />
          <h2 className="text-lg font-semibold">Trending Topics</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {["#AITwin", "#ContentCreation", "#DigitalIdentity", "#VoiceCloning", "#FutureOfWork"].map((tag) => (
            <span key={tag} className="px-3 py-1 bg-gray-800 rounded-full text-sm text-gray-300 hover:bg-gray-700 cursor-pointer">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Suggested Creators */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-pink-500" />
          <h2 className="text-lg font-semibold">Suggested Creators</h2>
        </div>
        <p className="text-gray-500">Discover creators to follow</p>
      </div>

      <BottomNav />
    </div>
  );
}
