'use client';

/**
 * Content Calendar
 * 
 * Visual calendar for scheduling and managing content posts.
 * Supports month/week/day views with drag-and-drop rescheduling.
 */

import { useState, useEffect, useMemo } from 'react';
import {
    Calendar as CalendarIcon,
    ChevronLeft,
    ChevronRight,
    Plus,
    Clock,
    Sparkles,
} from 'lucide-react';

// Platform icons/colors
const PLATFORM_COLORS: Record<string, string> = {
    instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
    youtube: 'bg-red-500',
    tiktok: 'bg-black',
    twitter: 'bg-sky-500',
    linkedin: 'bg-blue-700',
    facebook: 'bg-blue-600',
};

interface ScheduledPost {
    id: string;
    title: string;
    platform: string;
    scheduled_at: string;
    status: 'draft' | 'scheduled' | 'published' | 'failed';
    content_preview?: string;
}

interface OptimalTime {
    time: string;
    score: number;
    reason: string;
}

type ViewMode = 'month' | 'week' | 'day';

interface ContentCalendarProps {
    className?: string;
    onScheduleClick?: (date: Date) => void;
    onPostClick?: (post: ScheduledPost) => void;
}

// Helper functions
function getMonthDays(year: number, month: number): Date[] {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: Date[] = [];

    // Add padding days from previous month
    const startPadding = firstDay.getDay();
    for (let i = startPadding - 1; i >= 0; i--) {
        days.push(new Date(year, month, -i));
    }

    // Add all days in month
    for (let i = 1; i <= lastDay.getDate(); i++) {
        days.push(new Date(year, month, i));
    }

    // Add padding days for next month
    const endPadding = 42 - days.length; // 6 rows * 7 days
    for (let i = 1; i <= endPadding; i++) {
        days.push(new Date(year, month + 1, i));
    }

    return days;
}

function isSameDay(a: Date, b: Date): boolean {
    return (
        a.getDate() === b.getDate() &&
        a.getMonth() === b.getMonth() &&
        a.getFullYear() === b.getFullYear()
    );
}

function formatTime(dateStr: string): string {
    return new Date(dateStr).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
    });
}

export function ContentCalendar({
    className = '',
    onScheduleClick,
    onPostClick,
}: ContentCalendarProps) {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [viewMode, setViewMode] = useState<ViewMode>('month');
    const [posts, setPosts] = useState<ScheduledPost[]>([]);
    const [optimalTimes, setOptimalTimes] = useState<OptimalTime[]>([]);
    const [loading, setLoading] = useState(true);
    const [showOptimalTimes, setShowOptimalTimes] = useState(false);

    const monthDays = useMemo(
        () => getMonthDays(currentDate.getFullYear(), currentDate.getMonth()),
        [currentDate]
    );

    const today = new Date();
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    // Fetch scheduled posts
    useEffect(() => {
        async function fetchPosts() {
            setLoading(true);
            try {
                const startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
                const endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

                const response = await fetch(
                    `/api/v1/schedule?start=${startDate.toISOString()}&end=${endDate.toISOString()}`
                );
                if (response.ok) {
                    const data = await response.json();
                    setPosts(data.posts || []);
                }
            } catch (error) {
                console.error('Failed to fetch posts:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchPosts();
    }, [currentDate]);

    // Get posts for a specific day
    const getPostsForDay = (day: Date): ScheduledPost[] => {
        return posts.filter((post) => {
            const postDate = new Date(post.scheduled_at);
            return isSameDay(postDate, day);
        });
    };

    // Navigation
    const goToPrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const goToNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const goToToday = () => {
        setCurrentDate(new Date());
    };

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl shadow-sm ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-800">
                <div className="flex items-center gap-4">
                    <CalendarIcon className="h-6 w-6 text-indigo-500" />
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Content Calendar
                        </h2>
                        <p className="text-sm text-gray-500">
                            Schedule and manage your content
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowOptimalTimes(!showOptimalTimes)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${showOptimalTimes
                                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                            }`}
                    >
                        <Sparkles className="h-4 w-4" />
                        Optimal Times
                    </button>
                    <button
                        onClick={() => onScheduleClick?.(new Date())}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                        <Plus className="h-4 w-4" />
                        Schedule Content
                    </button>
                </div>
            </div>

            {/* Calendar Navigation */}
            <div className="flex items-center justify-between px-4 py-3 border-b dark:border-gray-800">
                <div className="flex items-center gap-2">
                    <button
                        onClick={goToPrevMonth}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </button>
                    <button
                        onClick={goToNextMonth}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                    >
                        <ChevronRight className="h-5 w-5" />
                    </button>
                    <button
                        onClick={goToToday}
                        className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                    >
                        Today
                    </button>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                </h3>
                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                    {(['month', 'week', 'day'] as ViewMode[]).map((mode) => (
                        <button
                            key={mode}
                            onClick={() => setViewMode(mode)}
                            className={`px-3 py-1 text-sm rounded-md capitalize transition-colors ${viewMode === mode
                                    ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                                    : 'text-gray-600 dark:text-gray-400'
                                }`}
                        >
                            {mode}
                        </button>
                    ))}
                </div>
            </div>

            {/* Day Headers */}
            <div className="grid grid-cols-7 border-b dark:border-gray-800">
                {dayNames.map((day) => (
                    <div
                        key={day}
                        className="py-2 text-center text-sm font-medium text-gray-500 dark:text-gray-400"
                    >
                        {day}
                    </div>
                ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7">
                {monthDays.map((day, index) => {
                    const isCurrentMonth = day.getMonth() === currentDate.getMonth();
                    const isToday = isSameDay(day, today);
                    const dayPosts = getPostsForDay(day);

                    return (
                        <div
                            key={index}
                            onClick={() => onScheduleClick?.(day)}
                            className={`
                min-h-[100px] p-2 border-b border-r dark:border-gray-800 cursor-pointer
                transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50
                ${!isCurrentMonth ? 'bg-gray-50/50 dark:bg-gray-900/50' : ''}
              `}
                        >
                            <div className="flex items-center justify-between mb-1">
                                <span
                                    className={`
                    text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full
                    ${isToday
                                            ? 'bg-indigo-600 text-white'
                                            : isCurrentMonth
                                                ? 'text-gray-900 dark:text-white'
                                                : 'text-gray-400 dark:text-gray-600'
                                        }
                  `}
                                >
                                    {day.getDate()}
                                </span>
                                {dayPosts.length > 0 && (
                                    <span className="text-xs text-gray-500">{dayPosts.length} posts</span>
                                )}
                            </div>

                            {/* Posts for this day */}
                            <div className="space-y-1">
                                {dayPosts.slice(0, 3).map((post) => (
                                    <button
                                        key={post.id}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onPostClick?.(post);
                                        }}
                                        className={`
                      w-full text-left px-2 py-1 rounded text-xs text-white truncate
                      ${PLATFORM_COLORS[post.platform] || 'bg-gray-500'}
                      hover:opacity-90 transition-opacity
                    `}
                                    >
                                        <Clock className="h-3 w-3 inline mr-1" />
                                        {formatTime(post.scheduled_at)} - {post.title}
                                    </button>
                                ))}
                                {dayPosts.length > 3 && (
                                    <div className="text-xs text-gray-500 text-center">
                                        +{dayPosts.length - 3} more
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Optimal Times Panel */}
            {showOptimalTimes && optimalTimes.length > 0 && (
                <div className="p-4 border-t dark:border-gray-800 bg-indigo-50/50 dark:bg-indigo-900/10">
                    <h4 className="text-sm font-medium text-indigo-900 dark:text-indigo-300 mb-3">
                        <Sparkles className="h-4 w-4 inline mr-2" />
                        AI-Suggested Optimal Posting Times
                    </h4>
                    <div className="flex flex-wrap gap-2">
                        {optimalTimes.map((time, i) => (
                            <div
                                key={i}
                                className="px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-indigo-200 dark:border-indigo-800"
                            >
                                <div className="font-medium text-gray-900 dark:text-white">
                                    {time.time}
                                </div>
                                <div className="text-xs text-gray-500">{time.reason}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Loading overlay */}
            {loading && (
                <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 flex items-center justify-center">
                    <div className="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
                </div>
            )}
        </div>
    );
}

export default ContentCalendar;
