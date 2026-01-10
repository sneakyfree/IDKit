"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";

type ViewMode = "month" | "week" | "list";
type ContentType = "all" | "post" | "video" | "podcast" | "email";

interface ScheduledItem {
  id: string;
  title: string;
  type: ContentType;
  platform: string;
  scheduledAt: string;
  status: "scheduled" | "published" | "failed";
  thumbnailUrl: string | null;
}

interface CalendarDay {
  date: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  items: ScheduledItem[];
}

// Mock data - will be replaced with API calls
const mockScheduledItems: ScheduledItem[] = [
  {
    id: "1",
    title: "New Product Launch Announcement",
    type: "post",
    platform: "instagram",
    scheduledAt: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
    status: "scheduled",
    thumbnailUrl: null,
  },
  {
    id: "2",
    title: "Behind the Scenes Video",
    type: "video",
    platform: "youtube",
    scheduledAt: new Date(Date.now() + 172800000).toISOString(), // 2 days
    status: "scheduled",
    thumbnailUrl: null,
  },
  {
    id: "3",
    title: "Weekly Newsletter",
    type: "email",
    platform: "email",
    scheduledAt: new Date(Date.now() + 259200000).toISOString(), // 3 days
    status: "scheduled",
    thumbnailUrl: null,
  },
  {
    id: "4",
    title: "Tech Talk Episode 15",
    type: "podcast",
    platform: "spotify",
    scheduledAt: new Date(Date.now() + 604800000).toISOString(), // 1 week
    status: "scheduled",
    thumbnailUrl: null,
  },
];

export default function SchedulePage() {
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [scheduledItems, setScheduledItems] = useState<ScheduledItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState<ContentType>("all");
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  // Load scheduled items
  useEffect(() => {
    const loadScheduledItems = async () => {
      setIsLoading(true);
      try {
        // TODO: Replace with actual API call
        // const response = await schedule.getItems();
        setScheduledItems(mockScheduledItems);
      } catch (error) {
        console.error("Failed to load scheduled items:", error);
      } finally {
        setIsLoading(false);
      }
    };
    loadScheduledItems();
  }, []);

  // Generate calendar days
  const getCalendarDays = useCallback((): CalendarDay[] => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    const days: CalendarDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      const date = new Date(year, month - 1, prevMonthLastDay - i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: false,
        items: getItemsForDate(date),
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      const isToday = date.getTime() === today.getTime();
      days.push({
        date,
        isCurrentMonth: true,
        isToday,
        items: getItemsForDate(date),
      });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      const date = new Date(year, month + 1, i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: false,
        items: getItemsForDate(date),
      });
    }

    return days;
  }, [currentDate, scheduledItems]);

  const getItemsForDate = (date: Date): ScheduledItem[] => {
    const dateStr = date.toISOString().split("T")[0];
    return scheduledItems.filter((item) => {
      const itemDate = new Date(item.scheduledAt).toISOString().split("T")[0];
      return itemDate === dateStr && (filterType === "all" || item.type === filterType);
    });
  };

  const getWeekDays = (): CalendarDay[] => {
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

    const days: CalendarDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      days.push({
        date,
        isCurrentMonth: true,
        isToday: date.getTime() === today.getTime(),
        items: getItemsForDate(date),
      });
    }

    return days;
  };

  const navigatePrevious = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    } else if (viewMode === "week") {
      setCurrentDate(new Date(currentDate.getTime() - 7 * 86400000));
    }
  };

  const navigateNext = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    } else if (viewMode === "week") {
      setCurrentDate(new Date(currentDate.getTime() + 7 * 86400000));
    }
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  const filteredItems = scheduledItems.filter(
    (item) => filterType === "all" || item.type === filterType
  );

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  };

  const formatWeekRange = (date: Date) => {
    const startOfWeek = new Date(date);
    startOfWeek.setDate(date.getDate() - date.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    const startMonth = startOfWeek.toLocaleDateString("en-US", { month: "short" });
    const endMonth = endOfWeek.toLocaleDateString("en-US", { month: "short" });

    if (startMonth === endMonth) {
      return `${startMonth} ${startOfWeek.getDate()} - ${endOfWeek.getDate()}, ${startOfWeek.getFullYear()}`;
    }
    return `${startMonth} ${startOfWeek.getDate()} - ${endMonth} ${endOfWeek.getDate()}, ${startOfWeek.getFullYear()}`;
  };

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Content Schedule</h1>
          <button
            onClick={() => setShowScheduleModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
          >
            + Schedule
          </button>
        </div>

        {/* View Mode Tabs */}
        <div className="flex gap-2 px-4 pb-3">
          {(["month", "week", "list"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                viewMode === mode
                  ? "bg-white text-black"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        {/* Content Type Filter */}
        <div className="flex gap-2 px-4 pb-3 overflow-x-auto">
          {(["all", "post", "video", "podcast", "email"] as ContentType[]).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                filterType === type
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800/50 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {type === "all" ? "All" : type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {/* Calendar Navigation */}
      {viewMode !== "list" && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <button
            onClick={navigatePrevious}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <span className="font-medium">
              {viewMode === "month" ? formatMonthYear(currentDate) : formatWeekRange(currentDate)}
            </span>
            <button
              onClick={goToToday}
              className="px-2 py-1 text-xs bg-gray-800 rounded hover:bg-gray-700 transition-colors"
            >
              Today
            </button>
          </div>
          <button
            onClick={navigateNext}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Calendar View */}
      {viewMode === "month" && (
        <div className="px-2 py-2">
          {/* Week day headers */}
          <div className="grid grid-cols-7 mb-1">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="text-center text-xs text-gray-500 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {getCalendarDays().map((day, index) => (
              <button
                key={index}
                onClick={() => setSelectedDate(day.date)}
                className={`min-h-[70px] p-1 rounded-lg transition-colors ${
                  day.isCurrentMonth ? "bg-gray-900" : "bg-gray-900/30"
                } ${day.isToday ? "ring-2 ring-purple-500" : ""} ${
                  selectedDate?.toDateString() === day.date.toDateString()
                    ? "ring-2 ring-white"
                    : ""
                } hover:bg-gray-800`}
              >
                <div
                  className={`text-xs font-medium mb-1 ${
                    day.isCurrentMonth ? "text-white" : "text-gray-600"
                  } ${day.isToday ? "text-purple-400" : ""}`}
                >
                  {day.date.getDate()}
                </div>
                <div className="space-y-0.5">
                  {day.items.slice(0, 2).map((item) => (
                    <div
                      key={item.id}
                      className={`text-[10px] truncate px-1 py-0.5 rounded ${getTypeColor(item.type)}`}
                    >
                      {item.title}
                    </div>
                  ))}
                  {day.items.length > 2 && (
                    <div className="text-[10px] text-gray-500 px-1">
                      +{day.items.length - 2} more
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Week View */}
      {viewMode === "week" && (
        <div className="px-2 py-2">
          <div className="grid grid-cols-7 gap-1">
            {getWeekDays().map((day, index) => (
              <div
                key={index}
                className={`p-2 rounded-lg ${day.isToday ? "bg-purple-900/30" : "bg-gray-900"}`}
              >
                <div className="text-center mb-2">
                  <div className="text-xs text-gray-500">
                    {day.date.toLocaleDateString("en-US", { weekday: "short" })}
                  </div>
                  <div
                    className={`text-lg font-bold ${
                      day.isToday ? "text-purple-400" : "text-white"
                    }`}
                  >
                    {day.date.getDate()}
                  </div>
                </div>
                <div className="space-y-1">
                  {day.items.map((item) => (
                    <Link
                      key={item.id}
                      href={`/schedule/${item.id}`}
                      className={`block text-[10px] p-1.5 rounded ${getTypeColor(item.type)} hover:opacity-80 transition-opacity`}
                    >
                      <div className="truncate font-medium">{item.title}</div>
                      <div className="text-gray-300 truncate">
                        {new Date(item.scheduledAt).toLocaleTimeString("en-US", {
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* List View */}
      {viewMode === "list" && (
        <div className="px-4 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoaderIcon className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : filteredItems.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-3">
              {filteredItems
                .sort((a, b) => new Date(a.scheduledAt).getTime() - new Date(b.scheduledAt).getTime())
                .map((item) => (
                  <ScheduleCard key={item.id} item={item} />
                ))}
            </div>
          )}
        </div>
      )}

      {/* Selected Date Details */}
      {selectedDate && viewMode !== "list" && (
        <div className="px-4 py-4 border-t border-gray-800">
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            {selectedDate.toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </h3>
          <div className="space-y-2">
            {getItemsForDate(selectedDate).length === 0 ? (
              <p className="text-sm text-gray-500">No scheduled content for this day</p>
            ) : (
              getItemsForDate(selectedDate).map((item) => (
                <ScheduleCard key={item.id} item={item} compact />
              ))
            )}
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <ScheduleModal onClose={() => setShowScheduleModal(false)} />
      )}

      <BottomNav />
    </main>
  );
}

// Components
function ScheduleCard({ item, compact = false }: { item: ScheduledItem; compact?: boolean }) {
  const scheduledDate = new Date(item.scheduledAt);

  return (
    <Link
      href={`/schedule/${item.id}`}
      className={`flex gap-3 p-3 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors ${
        compact ? "py-2" : ""
      }`}
    >
      {/* Type Icon */}
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${getTypeColor(item.type)}`}>
        <ContentTypeIcon type={item.type} />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-sm truncate">{item.title}</h3>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
          <PlatformIcon platform={item.platform} />
          <span>{item.platform}</span>
          <span>-</span>
          <span>
            {scheduledDate.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}{" "}
            at{" "}
            {scheduledDate.toLocaleTimeString("en-US", {
              hour: "numeric",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>

      {/* Status */}
      <StatusBadge status={item.status} />
    </Link>
  );
}

function ScheduleModal({ onClose }: { onClose: () => void }) {
  const [selectedContent, setSelectedContent] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");

  const handleSchedule = async () => {
    // TODO: Implement API call
    console.log("Scheduling:", { selectedContent, selectedPlatform, scheduledDate, scheduledTime });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-gray-900 rounded-t-3xl p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Schedule Content</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full">
            <CloseIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Content Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Select Content
            </label>
            <select
              value={selectedContent}
              onChange={(e) => setSelectedContent(e.target.value)}
              className="w-full bg-gray-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Choose content to schedule...</option>
              <option value="draft-1">New Product Launch (Draft)</option>
              <option value="draft-2">Behind the Scenes Video (Draft)</option>
              <option value="draft-3">Weekly Newsletter (Draft)</option>
            </select>
          </div>

          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Platform
            </label>
            <div className="grid grid-cols-3 gap-2">
              {["instagram", "youtube", "tiktok", "twitter", "linkedin", "email"].map((platform) => (
                <button
                  key={platform}
                  onClick={() => setSelectedPlatform(platform)}
                  className={`p-3 rounded-lg text-xs font-medium transition-colors ${
                    selectedPlatform === platform
                      ? "bg-purple-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                >
                  {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Date
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full bg-gray-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Time
              </label>
              <input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-full bg-gray-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          {/* Best Time Suggestions */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
              <SparklesIcon className="w-4 h-4 text-purple-400" />
              <span>Suggested best times</span>
            </div>
            <div className="flex gap-2">
              {["9:00 AM", "12:00 PM", "6:00 PM", "8:00 PM"].map((time) => (
                <button
                  key={time}
                  onClick={() => setScheduledTime(time.replace(" AM", ":00").replace(" PM", ":00"))}
                  className="px-3 py-1 bg-gray-700 rounded-full text-xs hover:bg-gray-600 transition-colors"
                >
                  {time}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-gray-800 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSchedule}
              disabled={!selectedContent || !selectedPlatform || !scheduledDate || !scheduledTime}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Schedule
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
        <CalendarIcon className="w-8 h-8 text-gray-600" />
      </div>
      <h3 className="font-medium text-gray-400">No scheduled content</h3>
      <p className="text-sm text-gray-500 mt-1">
        Schedule your first post to see it here
      </p>
      <Link
        href="/studio"
        className="inline-block mt-4 px-4 py-2 bg-purple-600 rounded-full text-sm font-medium hover:bg-purple-700 transition-colors"
      >
        Create Content
      </Link>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    scheduled: "bg-blue-500/20 text-blue-400",
    published: "bg-green-500/20 text-green-400",
    failed: "bg-red-500/20 text-red-400",
  };

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${
        styles[status as keyof typeof styles] || styles.scheduled
      }`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function ContentTypeIcon({ type }: { type: ContentType }) {
  switch (type) {
    case "video":
      return <VideoIcon className="w-5 h-5" />;
    case "podcast":
      return <MicIcon className="w-5 h-5" />;
    case "email":
      return <MailIcon className="w-5 h-5" />;
    default:
      return <EditIcon className="w-5 h-5" />;
  }
}

function PlatformIcon({ platform }: { platform: string }) {
  // Simplified - would use actual platform icons
  return <span className="w-4 h-4 rounded-full bg-gray-700" />;
}

function getTypeColor(type: ContentType): string {
  switch (type) {
    case "video":
      return "bg-red-500/20 text-red-400";
    case "podcast":
      return "bg-purple-500/20 text-purple-400";
    case "email":
      return "bg-yellow-500/20 text-yellow-400";
    case "post":
      return "bg-blue-500/20 text-blue-400";
    default:
      return "bg-gray-500/20 text-gray-400";
  }
}

// Icons
function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
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

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function VideoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function EditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
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

function MailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}
