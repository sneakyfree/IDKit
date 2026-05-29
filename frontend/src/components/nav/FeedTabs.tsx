"use client";

import { cn } from "@/lib/utils";
import { useFeedStore } from "@/lib/store";

export function FeedTabs() {
  const { activeTab, setActiveTab } = useFeedStore();

  return (
    <div className="fixed top-0 left-0 right-0 z-40 pt-safe">
      <div className="flex items-center justify-center gap-4 py-4">
        <button
          onClick={() => setActiveTab("following")}
          className={cn(
            "text-base font-semibold text-white transition-opacity",
            activeTab === "following" ? "opacity-100" : "opacity-80"
          )}
        >
          Following
        </button>
        <div className="w-px h-4 bg-white/30" />
        <button
          onClick={() => setActiveTab("for-you")}
          className={cn(
            "text-base font-semibold text-white transition-opacity",
            activeTab === "for-you" ? "opacity-100" : "opacity-80"
          )}
        >
          For You
        </button>
      </div>
      {/* Active indicator */}
      <div className="flex justify-center">
        <div
          className={cn(
            "w-8 h-0.5 bg-white rounded-full transition-transform duration-200",
            activeTab === "following" ? "-translate-x-12" : "translate-x-8"
          )}
        />
      </div>
    </div>
  );
}
