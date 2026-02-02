'use client';

/**
 * Publishing Queue Card
 * 
 * Displays scheduled posts with status, timing, and actions.
 */

import { useState } from 'react';
import {
    Clock,
    CheckCircle,
    AlertCircle,
    MoreVertical,
    Edit2,
    Trash2,
    Calendar,
    Play,
    Pause,
    RefreshCw
} from 'lucide-react';

interface ScheduledPost {
    id: string;
    title: string;
    platform: string;
    scheduled_at: string;
    status: 'pending' | 'scheduled' | 'publishing' | 'published' | 'failed';
    content_preview?: string;
    thumbnail_url?: string;
}

const PLATFORM_COLORS: Record<string, string> = {
    instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
    youtube: 'bg-red-500',
    tiktok: 'bg-black',
    twitter: 'bg-sky-500',
    linkedin: 'bg-blue-700',
    facebook: 'bg-blue-600',
};

const STATUS_CONFIG = {
    pending: { icon: Clock, color: 'text-gray-500', bg: 'bg-gray-100 dark:bg-gray-800' },
    scheduled: { icon: Calendar, color: 'text-blue-500', bg: 'bg-blue-100 dark:bg-blue-900/30' },
    publishing: { icon: RefreshCw, color: 'text-yellow-500', bg: 'bg-yellow-100 dark:bg-yellow-900/30', animate: true },
    published: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100 dark:bg-green-900/30' },
    failed: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-100 dark:bg-red-900/30' },
};

interface PublishingQueueCardProps {
    post: ScheduledPost;
    onEdit?: (post: ScheduledPost) => void;
    onDelete?: (postId: string) => void;
    onReschedule?: (post: ScheduledPost) => void;
    onRetry?: (postId: string) => void;
    onPause?: (postId: string) => void;
    className?: string;
}

export function PublishingQueueCard({
    post,
    onEdit,
    onDelete,
    onReschedule,
    onRetry,
    onPause,
    className = '',
}: PublishingQueueCardProps) {
    const [showMenu, setShowMenu] = useState(false);

    const statusConfig = STATUS_CONFIG[post.status];
    const StatusIcon = statusConfig.icon;

    const scheduledDate = new Date(post.scheduled_at);
    const isUpcoming = scheduledDate > new Date();
    const timeUntil = isUpcoming
        ? formatTimeUntil(scheduledDate)
        : formatTimeAgo(scheduledDate);

    function formatTimeUntil(date: Date): string {
        const diff = date.getTime() - Date.now();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        if (hours > 24) {
            const days = Math.floor(hours / 24);
            return `in ${days} day${days > 1 ? 's' : ''}`;
        }
        if (hours > 0) {
            return `in ${hours}h ${minutes}m`;
        }
        return `in ${minutes}m`;
    }

    function formatTimeAgo(date: Date): string {
        const diff = Date.now() - date.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));

        if (hours > 24) {
            return date.toLocaleDateString();
        }
        if (hours > 0) {
            return `${hours}h ago`;
        }
        const minutes = Math.floor(diff / (1000 * 60));
        return `${minutes}m ago`;
    }

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 overflow-hidden ${className}`}>
            <div className="flex items-start gap-4 p-4">
                {/* Thumbnail */}
                <div className={`w-16 h-16 rounded-lg flex-shrink-0 overflow-hidden ${PLATFORM_COLORS[post.platform] || 'bg-gray-200'}`}>
                    {post.thumbnail_url ? (
                        <img src={post.thumbnail_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-white font-bold text-lg uppercase">
                            {post.platform.slice(0, 2)}
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                        <div>
                            <h3 className="font-medium text-gray-900 dark:text-white truncate">
                                {post.title}
                            </h3>
                            {post.content_preview && (
                                <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                                    {post.content_preview}
                                </p>
                            )}
                        </div>

                        {/* Actions Menu */}
                        <div className="relative">
                            <button
                                onClick={() => setShowMenu(!showMenu)}
                                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
                            >
                                <MoreVertical className="h-5 w-5" />
                            </button>

                            {showMenu && (
                                <>
                                    <div
                                        className="fixed inset-0 z-10"
                                        onClick={() => setShowMenu(false)}
                                    />
                                    <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-lg z-20 py-1">
                                        {onEdit && (
                                            <button
                                                onClick={() => { onEdit(post); setShowMenu(false); }}
                                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                                            >
                                                <Edit2 className="h-4 w-4" /> Edit
                                            </button>
                                        )}
                                        {onReschedule && post.status !== 'published' && (
                                            <button
                                                onClick={() => { onReschedule(post); setShowMenu(false); }}
                                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                                            >
                                                <Calendar className="h-4 w-4" /> Reschedule
                                            </button>
                                        )}
                                        {onPause && post.status === 'scheduled' && (
                                            <button
                                                onClick={() => { onPause(post.id); setShowMenu(false); }}
                                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20"
                                            >
                                                <Pause className="h-4 w-4" /> Pause
                                            </button>
                                        )}
                                        {onRetry && post.status === 'failed' && (
                                            <button
                                                onClick={() => { onRetry(post.id); setShowMenu(false); }}
                                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                                            >
                                                <RefreshCw className="h-4 w-4" /> Retry
                                            </button>
                                        )}
                                        {onDelete && (
                                            <button
                                                onClick={() => { onDelete(post.id); setShowMenu(false); }}
                                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                                            >
                                                <Trash2 className="h-4 w-4" /> Delete
                                            </button>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Status & Time */}
                    <div className="flex items-center gap-3 mt-3">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}>
                            <StatusIcon className={`h-3.5 w-3.5 ${statusConfig.animate ? 'animate-spin' : ''}`} />
                            {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                        </span>

                        <span className="text-sm text-gray-500">
                            {isUpcoming ? (
                                <span className="flex items-center gap-1">
                                    <Clock className="h-3.5 w-3.5" />
                                    {timeUntil}
                                </span>
                            ) : (
                                timeUntil
                            )}
                        </span>

                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-400 capitalize">
                            {post.platform}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

/**
 * Publishing Queue List
 */
interface PublishingQueueProps {
    posts: ScheduledPost[];
    onEdit?: (post: ScheduledPost) => void;
    onDelete?: (postId: string) => void;
    onReschedule?: (post: ScheduledPost) => void;
    onRetry?: (postId: string) => void;
    className?: string;
}

export function PublishingQueue({
    posts,
    onEdit,
    onDelete,
    onReschedule,
    onRetry,
    className = '',
}: PublishingQueueProps) {
    const upcoming = posts.filter(p => p.status === 'scheduled' || p.status === 'pending');
    const published = posts.filter(p => p.status === 'published');
    const failed = posts.filter(p => p.status === 'failed');

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Upcoming */}
            {upcoming.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-3">
                        Upcoming ({upcoming.length})
                    </h3>
                    <div className="space-y-3">
                        {upcoming.map(post => (
                            <PublishingQueueCard
                                key={post.id}
                                post={post}
                                onEdit={onEdit}
                                onDelete={onDelete}
                                onReschedule={onReschedule}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Failed */}
            {failed.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-red-500 mb-3">
                        Failed ({failed.length})
                    </h3>
                    <div className="space-y-3">
                        {failed.map(post => (
                            <PublishingQueueCard
                                key={post.id}
                                post={post}
                                onEdit={onEdit}
                                onDelete={onDelete}
                                onRetry={onRetry}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Published */}
            {published.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-green-500 mb-3">
                        Recently Published ({published.length})
                    </h3>
                    <div className="space-y-3">
                        {published.slice(0, 5).map(post => (
                            <PublishingQueueCard
                                key={post.id}
                                post={post}
                                onEdit={onEdit}
                            />
                        ))}
                    </div>
                </div>
            )}

            {posts.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                    <Calendar className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>No scheduled posts</p>
                </div>
            )}
        </div>
    );
}

export default PublishingQueueCard;
