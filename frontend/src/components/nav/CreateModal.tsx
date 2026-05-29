"use client";

import { useCreateStore } from "@/lib/store";
import {
  X,
  Video,
  Image as ImageIcon,
  FileText,
  Mic,
  Sparkles,
  Calendar,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const createOptions = [
  {
    href: "/create/post",
    icon: FileText,
    label: "Quick Post",
    description: "Text, image, or carousel",
    color: "from-blue-500 to-cyan-500",
  },
  {
    href: "/create/video",
    icon: Video,
    label: "AI Video",
    description: "Create with your AI Twin",
    color: "from-purple-500 to-pink-500",
  },
  {
    href: "/create/podcast",
    icon: Mic,
    label: "Podcast",
    description: "Record or generate episode",
    color: "from-orange-500 to-red-500",
  },
  {
    href: "/studio",
    icon: Sparkles,
    label: "Content Studio",
    description: "Full creation suite",
    color: "from-emerald-500 to-teal-500",
  },
  {
    href: "/schedule",
    icon: Calendar,
    label: "Schedule",
    description: "Plan your content",
    color: "from-amber-500 to-orange-500",
  },
];

export function CreateModal() {
  const { isOpen, close } = useCreateStore();

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
      onClick={close}
    >
      {/* Modal content */}
      <div
        className="absolute bottom-0 left-0 right-0 bg-gray-900 rounded-t-3xl p-6 pb-safe animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="w-12 h-1 bg-gray-700 rounded-full mx-auto mb-6" />

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Create</h2>
          <button
            onClick={close}
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Options grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {createOptions.map((option) => {
            const Icon = option.icon;
            return (
              <Link
                key={option.href}
                href={option.href}
                onClick={close}
                className="flex flex-col items-center p-4 bg-white/5 hover:bg-white/10 rounded-2xl transition-colors"
              >
                <div
                  className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center mb-3 bg-gradient-to-br",
                    option.color
                  )}
                >
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <span className="font-medium text-sm">{option.label}</span>
                <span className="text-xs text-gray-300 text-center mt-1">
                  {option.description}
                </span>
              </Link>
            );
          })}
        </div>

        {/* Quick action */}
        <Link
          href="/create/quick"
          onClick={close}
          className="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-primary-500 to-pink-500 rounded-xl font-semibold"
        >
          <ImageIcon className="w-5 h-5" />
          <span>Upload from Gallery</span>
        </Link>
      </div>
    </div>
  );
}
