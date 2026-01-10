"use client";

import { FeedScroll } from "@/components/feed/FeedScroll";
import { FeedTabs } from "@/components/nav/FeedTabs";
import { BottomNav } from "@/components/nav/BottomNav";
import { CreateModal } from "@/components/nav/CreateModal";

export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-black">
      {/* Feed tabs (For You / Following) */}
      <FeedTabs />

      {/* Main feed scroll */}
      <FeedScroll />

      {/* Bottom navigation */}
      <BottomNav />

      {/* Create modal */}
      <CreateModal />
    </main>
  );
}
