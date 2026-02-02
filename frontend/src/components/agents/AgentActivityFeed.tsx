'use client';

/**
 * Agent Activity Feed
 * 
 * Real-time activity stream showing agent actions, decisions, and status updates.
 */

import { useState, useEffect } from 'react';
import { Bot, CheckCircle, AlertCircle, Clock, MessageSquare, Zap, ChevronDown, Filter } from 'lucide-react';

interface ActivityItem {
    id: string;
    agent_type: string;
    action_type: 'task_completed' | 'decision_made' | 'approval_requested' | 'error' | 'info';
    title: string;
    description: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
}

const AGENT_COLORS: Record<string, string> = {
    orchestrator: 'from-purple-500 to-indigo-500',
    content: 'from-blue-500 to-cyan-500',
    analytics: 'from-green-500 to-emerald-500',
    publishing: 'from-orange-500 to-amber-500',
    discovery: 'from-cyan-500 to-teal-500',
    engagement: 'from-pink-500 to-rose-500',
    revenue: 'from-yellow-500 to-orange-500',
    moderation: 'from-red-500 to-pink-500',
};

const ACTION_ICONS = {
    task_completed: CheckCircle,
    decision_made: Zap,
    approval_requested: Clock,
    error: AlertCircle,
    info: MessageSquare,
};

const ACTION_COLORS = {
    task_completed: 'text-green-500',
    decision_made: 'text-blue-500',
    approval_requested: 'text-yellow-500',
    error: 'text-red-500',
    info: 'text-gray-500',
};

interface AgentActivityFeedProps {
    maxItems?: number;
    showFilters?: boolean;
    autoRefresh?: boolean;
    refreshInterval?: number;
    className?: string;
}

export function AgentActivityFeed({
    maxItems = 20,
    showFilters = true,
    autoRefresh = true,
    refreshInterval = 10000,
    className = '',
}: AgentActivityFeedProps) {
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterAgent, setFilterAgent] = useState<string | null>(null);
    const [filterAction, setFilterAction] = useState<string | null>(null);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const fetchActivities = async () => {
        try {
            const res = await fetch('/api/v1/agents/activity');
            if (res.ok) {
                const data = await res.json();
                setActivities(data.activities || []);
            } else {
                // Mock data for demo
                setActivities([
                    {
                        id: '1',
                        agent_type: 'content',
                        action_type: 'task_completed',
                        title: 'Content Analysis Completed',
                        description: 'Analyzed 5 draft posts and suggested optimizations',
                        timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
                        metadata: { posts_analyzed: 5, suggestions: 12 },
                    },
                    {
                        id: '2',
                        agent_type: 'analytics',
                        action_type: 'decision_made',
                        title: 'Optimal Posting Time Identified',
                        description: 'Based on engagement patterns, recommending 7 PM EST for next post',
                        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
                        metadata: { confidence: 0.89 },
                    },
                    {
                        id: '3',
                        agent_type: 'revenue',
                        action_type: 'approval_requested',
                        title: 'Brand Deal Rate Adjustment',
                        description: 'Recommending to increase sponsored post rate to $750',
                        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
                        metadata: { current_rate: 500, proposed_rate: 750 },
                    },
                    {
                        id: '4',
                        agent_type: 'moderation',
                        action_type: 'info',
                        title: 'Comment Moderation Active',
                        description: 'Monitoring 3 new posts for policy violations',
                        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                    },
                ]);
            }
        } catch (error) {
            console.error('Failed to fetch activities:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchActivities();

        if (autoRefresh) {
            const interval = setInterval(fetchActivities, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, refreshInterval]);

    const toggleExpand = (id: string) => {
        const newExpanded = new Set(expanded);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpanded(newExpanded);
    };

    const formatTimeAgo = (timestamp: string): string => {
        const diff = Date.now() - new Date(timestamp).getTime();
        const minutes = Math.floor(diff / (1000 * 60));

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        return new Date(timestamp).toLocaleDateString();
    };

    const filteredActivities = activities
        .filter(a => !filterAgent || a.agent_type === filterAgent)
        .filter(a => !filterAction || a.action_type === filterAction)
        .slice(0, maxItems);

    const agentTypes = [...new Set(activities.map(a => a.agent_type))];
    const actionTypes = [...new Set(activities.map(a => a.action_type))];

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-800">
                <div className="flex items-center gap-3">
                    <Bot className="h-5 w-5 text-indigo-500" />
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                        Agent Activity
                    </h3>
                    <span className="text-sm text-gray-500">
                        {filteredActivities.length} events
                    </span>
                </div>

                {showFilters && (
                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-gray-400" />
                        <select
                            value={filterAgent || ''}
                            onChange={(e) => setFilterAgent(e.target.value || null)}
                            className="text-sm border dark:border-gray-700 rounded px-2 py-1 bg-white dark:bg-gray-800"
                        >
                            <option value="">All Agents</option>
                            {agentTypes.map(type => (
                                <option key={type} value={type}>{type}</option>
                            ))}
                        </select>
                        <select
                            value={filterAction || ''}
                            onChange={(e) => setFilterAction(e.target.value || null)}
                            className="text-sm border dark:border-gray-700 rounded px-2 py-1 bg-white dark:bg-gray-800"
                        >
                            <option value="">All Actions</option>
                            {actionTypes.map(type => (
                                <option key={type} value={type}>{type.replace('_', ' ')}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            {/* Activity List */}
            <div className="divide-y dark:divide-gray-800 max-h-[500px] overflow-y-auto">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading activities...</div>
                ) : filteredActivities.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No activity to show</div>
                ) : (
                    filteredActivities.map((activity) => {
                        const Icon = ACTION_ICONS[activity.action_type];
                        const iconColor = ACTION_COLORS[activity.action_type];
                        const gradientColor = AGENT_COLORS[activity.agent_type] || 'from-gray-500 to-gray-600';
                        const isExpanded = expanded.has(activity.id);

                        return (
                            <div
                                key={activity.id}
                                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                            >
                                <div className="flex items-start gap-3">
                                    {/* Agent Avatar */}
                                    <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${gradientColor} flex items-center justify-center flex-shrink-0`}>
                                        <Bot className="h-4 w-4 text-white" />
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-gray-900 dark:text-white">
                                                        {activity.title}
                                                    </span>
                                                    <Icon className={`h-4 w-4 ${iconColor}`} />
                                                </div>
                                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                                                    {activity.description}
                                                </p>
                                            </div>
                                            <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                                                {formatTimeAgo(activity.timestamp)}
                                            </span>
                                        </div>

                                        {/* Metadata / Actions */}
                                        {activity.metadata && (
                                            <button
                                                onClick={() => toggleExpand(activity.id)}
                                                className="mt-2 flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                                            >
                                                <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                                                {isExpanded ? 'Hide details' : 'Show details'}
                                            </button>
                                        )}

                                        {isExpanded && activity.metadata && (
                                            <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">
                                                {Object.entries(activity.metadata).map(([key, value]) => (
                                                    <div key={key} className="flex gap-2">
                                                        <span className="text-gray-500">{key}:</span>
                                                        <span className="text-gray-900 dark:text-gray-100">{String(value)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Agent badge */}
                                        <div className="mt-2">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r ${gradientColor} text-white`}>
                                                {activity.agent_type}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default AgentActivityFeed;
