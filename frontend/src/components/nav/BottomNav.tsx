"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Search,
  Plus,
  MessageCircle,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCreateStore } from "@/lib/store";

const navItems = [
  { href: "/", icon: Home, label: "Home" },
  { href: "/discover", icon: Search, label: "Discover" },
  { href: "#create", icon: Plus, label: "Create", isCreate: true },
  { href: "/inbox", icon: MessageCircle, label: "Inbox" },
  { href: "/profile", icon: User, label: "Profile" },
];

export function BottomNav() {
  const pathname = usePathname();
  const openCreate = useCreateStore((s) => s.open);

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-lg border-t border-white/10">
      <div className="flex items-center justify-around h-16 max-w-lg mx-auto px-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          if (item.isCreate) {
            return (
              <button
                key={item.href}
                onClick={openCreate}
                className="flex flex-col items-center justify-center w-14 h-14 -mt-4"
              >
                <div className="flex items-center justify-center w-12 h-8 bg-gradient-to-r from-primary-500 to-pink-500 rounded-lg">
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </button>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center w-14 h-14 transition-colors",
                isActive ? "text-white" : "text-gray-500"
              )}
            >
              <Icon className={cn("w-6 h-6", isActive && "fill-current")} />
              <span className="text-[10px] mt-1">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
