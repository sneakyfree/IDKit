"use client";

import { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon, Clock, Loader2 } from "lucide-react";

/**
 * TASK 5.2.2: Calendar UI Component
 * 
 * Interactive calendar for viewing and managing scheduled posts
 */

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  platform: string;
  status: "pending" | "published" | "failed" | "cancelled";
  color: string;
}

type ViewType = "month" | "week" | "day";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// Platform colors
const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  tiktok: "#000000",
  youtube: "#FF0000",
  twitter: "#1DA1F2",
  linkedin: "#0A66C2",
  facebook: "#1877F2",
};

export default function ScheduleCalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<ViewType>("month");
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  // Fetch scheduled posts for current view
  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const start = getViewStart(currentDate, view);
      const end = getViewEnd(currentDate, view);

      const response = await fetch(
        `/api/v1/schedule/calendar?start=${start.toISOString()}&end=${end.toISOString()}`,
        {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to load schedule");

      const data = await response.json();
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load schedule");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [currentDate, view]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Navigation
  const navigatePrev = () => {
    const newDate = new Date(currentDate);
    if (view === "month") newDate.setMonth(newDate.getMonth() - 1);
    else if (view === "week") newDate.setDate(newDate.getDate() - 7);
    else newDate.setDate(newDate.getDate() - 1);
    setCurrentDate(newDate);
  };

  const navigateNext = () => {
    const newDate = new Date(currentDate);
    if (view === "month") newDate.setMonth(newDate.getMonth() + 1);
    else if (view === "week") newDate.setDate(newDate.getDate() + 7);
    else newDate.setDate(newDate.getDate() + 1);
    setCurrentDate(newDate);
  };

  const navigateToday = () => setCurrentDate(new Date());

  // Get events for a specific date
  const getEventsForDate = (date: Date): CalendarEvent[] => {
    return events.filter(event => {
      const eventDate = new Date(event.start);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  // Generate calendar grid for month view
  const generateMonthGrid = (): Date[][] => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const grid: Date[][] = [];
    let week: Date[] = [];

    // Fill in days before first of month
    for (let i = 0; i < firstDay.getDay(); i++) {
      const date = new Date(year, month, 1 - (firstDay.getDay() - i));
      week.push(date);
    }

    // Fill in days of month
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const date = new Date(year, month, day);
      week.push(date);

      if (week.length === 7) {
        grid.push(week);
        week = [];
      }
    }

    // Fill in days after last of month
    if (week.length > 0) {
      const daysNeeded = 7 - week.length;
      for (let i = 1; i <= daysNeeded; i++) {
        week.push(new Date(year, month + 1, i));
      }
      grid.push(week);
    }

    return grid;
  };

  const isToday = (date: Date): boolean => date.toDateString() === new Date().toDateString();
  const isCurrentMonth = (date: Date): boolean => date.getMonth() === currentDate.getMonth();

  return (
    <main className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800 px-4 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold">Content Schedule</h1>
              <p className="text-sm text-gray-200">Plan and manage your content calendar</p>
            </div>
            <button
              onClick={() => window.location.href = "/schedule/new"}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span className="hidden sm:inline">Schedule Post</span>
            </button>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={navigatePrev}
                className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                aria-label="Previous"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={navigateToday}
                className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 text-sm"
              >
                Today
              </button>
              <button
                onClick={navigateNext}
                className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                aria-label="Next"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Current date display */}
            <h2 className="text-lg font-semibold">
              {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>

            {/* View switcher */}
            <div className="flex gap-1 p-1 bg-gray-800 rounded-lg ml-auto">
              {(["month", "week", "day"] as ViewType[]).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === v ? "bg-purple-600" : "hover:bg-gray-700"
                    }`}
                >
                  {v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>

            {/* Timezone selector */}
            <select aria-label="Filter or select option"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
            >
              <option value="America/New_York">Eastern</option>
              <option value="America/Chicago">Central</option>
              <option value="America/Denver">Mountain</option>
              <option value="America/Los_Angeles">Pacific</option>
              <option value="UTC">UTC</option>
              <option value="Europe/London">London</option>
            </select>
          </div>
        </div>
      </header>

      {/* Calendar Grid */}
      <div className="max-w-7xl mx-auto p-4">
        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-center">
            <p className="text-red-300 mb-2">{error}</p>
            <button onClick={fetchEvents} className="text-red-400 underline">
              Retry
            </button>
          </div>
        )}

        {/* Month View */}
        {!loading && view === "month" && (
          <div className="bg-gray-900 rounded-2xl overflow-hidden">
            {/* Day headers */}
            <div className="grid grid-cols-7 border-b border-gray-800">
              {DAYS.map((day) => (
                <div key={day} className="p-3 text-center text-sm text-gray-200 font-medium">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar grid */}
            {generateMonthGrid().map((week, weekIndex) => (
              <div key={weekIndex} className="grid grid-cols-7 border-b border-gray-800 last:border-b-0">
                {week.map((date, dayIndex) => {
                  const dayEvents = getEventsForDate(date);
                  const isMonthDay = isCurrentMonth(date);

                  return (
                    <div
                      key={dayIndex}
                      className={`min-h-[100px] p-2 border-r border-gray-800 last:border-r-0 ${!isMonthDay ? "bg-gray-900/50" : "bg-gray-900"
                        } ${isToday(date) ? "ring-2 ring-purple-500 ring-inset" : ""}`}
                    >
                      <span className={`text-sm ${!isMonthDay ? "text-gray-200" : isToday(date) ? "text-purple-400 font-bold" : "text-gray-300"
                        }`}>
                        {date.getDate()}
                      </span>

                      {/* Events */}
                      <div className="mt-1 space-y-1">
                        {dayEvents.slice(0, 3).map((event) => (
                          <button
                            key={event.id}
                            onClick={() => setSelectedEvent(event)}
                            className="w-full text-left text-xs p-1 rounded truncate transition-opacity hover:opacity-80"
                            style={{ backgroundColor: event.color + "40", borderLeft: `3px solid ${event.color}` }}
                          >
                            {event.title}
                          </button>
                        ))}
                        {dayEvents.length > 3 && (
                          <span className="text-xs text-gray-300">+{dayEvents.length - 3} more</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && events.length === 0 && (
          <div className="bg-gray-900 rounded-2xl p-12 text-center">
            <CalendarIcon className="w-16 h-16 mx-auto text-gray-200 mb-4" />
            <h3 className="text-lg font-medium mb-2">No scheduled posts</h3>
            <p className="text-gray-300 mb-6">Start planning your content by scheduling your first post.</p>
            <button
              onClick={() => window.location.href = "/schedule/new"}
              className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
            >
              <Plus className="w-5 h-5" />
              Schedule Post
            </button>
          </div>
        )}

        {/* Platform Legend */}
        <div className="mt-6 flex flex-wrap gap-4 justify-center">
          {Object.entries(PLATFORM_COLORS).map(([platform, color]) => (
            <div key={platform} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-sm text-gray-200 capitalize">{platform}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setSelectedEvent(null)}
        >
          <div
            className="bg-gray-900 rounded-2xl max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: selectedEvent.color }} />
              <h3 className="text-lg font-bold">{selectedEvent.title}</h3>
            </div>
            <div className="space-y-3 text-sm text-gray-200">
              <p className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {new Date(selectedEvent.start).toLocaleString()}
              </p>
              <p className="capitalize">Platform: {selectedEvent.platform}</p>
              <p className="capitalize">Status: {selectedEvent.status}</p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setSelectedEvent(null)}
                className="flex-1 py-2 bg-gray-800 rounded-xl hover:bg-gray-700"
              >
                Close
              </button>
              <button className="flex-1 py-2 bg-purple-600 rounded-xl hover:bg-purple-700">
                Edit
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

// Helper functions
function getViewStart(date: Date, view: ViewType): Date {
  const d = new Date(date);
  if (view === "month") {
    d.setDate(1);
    d.setDate(d.getDate() - d.getDay()); // Start from Sunday of first week
  } else if (view === "week") {
    d.setDate(d.getDate() - d.getDay());
  }
  d.setHours(0, 0, 0, 0);
  return d;
}

function getViewEnd(date: Date, view: ViewType): Date {
  const d = new Date(date);
  if (view === "month") {
    d.setMonth(d.getMonth() + 1, 0); // Last day of month
    d.setDate(d.getDate() + (6 - d.getDay())); // End on Saturday
  } else if (view === "week") {
    d.setDate(d.getDate() - d.getDay() + 6);
  }
  d.setHours(23, 59, 59, 999);
  return d;
}
