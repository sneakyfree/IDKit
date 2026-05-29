'use client';

/**
 * Agent Memory Panel
 * 
 * Displays and manages agent memory for the current user.
 * Allows viewing, searching, and clearing agent memories.
 */

import { useState, useEffect } from 'react';
import { Brain, Trash2, RefreshCw, ChevronDown, ChevronRight, Clock, Tag } from 'lucide-react';

interface MemoryItem {
    id: string;
    agent_type: string;
    memory_type: string;
    summary: string;
    content: Record<string, unknown>;
    importance_score: number;
    tags: string[] | null;
    created_at: string;
    expires_at: string | null;
}

interface MemorySummary {
    total_memories: number;
    by_agent: Record<string, Array<{
        id: string;
        summary: string;
        memory_type: string;
        importance: number;
        created_at: string;
    }>>;
}

const AGENT_LABELS: Record<string, string> = {
    orchestrator: 'Orchestrator',
    content: 'Content Agent',
    analytics: 'Analytics Agent',
    publishing: 'Publishing Agent',
    discovery: 'Discovery Agent',
    engagement: 'Engagement Agent',
    revenue: 'Revenue Agent',
    moderation: 'Moderation Agent',
};

const AGENT_COLORS: Record<string, string> = {
    orchestrator: 'bg-purple-500',
    content: 'bg-blue-500',
    analytics: 'bg-green-500',
    publishing: 'bg-orange-500',
    discovery: 'bg-cyan-500',
    engagement: 'bg-pink-500',
    revenue: 'bg-yellow-500',
    moderation: 'bg-red-500',
};

interface AgentMemoryPanelProps {
    className?: string;
}

export function AgentMemoryPanel({ className = '' }: AgentMemoryPanelProps) {
    const [summary, setSummary] = useState<MemorySummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
    const [clearing, setClearing] = useState(false);
    const [clearingAgent, setClearingAgent] = useState<string | null>(null);

    const fetchMemorySummary = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/agent-memory/summary');
            if (!response.ok) throw new Error('Failed to fetch memory summary');
            const data = await response.json();
            setSummary(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const clearMemories = async (agentType?: string) => {
        const confirmMessage = agentType
            ? `Clear all memories for ${AGENT_LABELS[agentType] || agentType}?`
            : 'Clear ALL agent memories? This cannot be undone.';

        if (!confirm(confirmMessage)) return;

        if (agentType) {
            setClearingAgent(agentType);
        } else {
            setClearing(true);
        }

        try {
            const response = await fetch('/api/v1/agent-memory/clear', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_type: agentType || null }),
            });
            if (!response.ok) throw new Error('Failed to clear memories');
            await fetchMemorySummary();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to clear');
        } finally {
            setClearing(false);
            setClearingAgent(null);
        }
    };

    const toggleAgent = (agent: string) => {
        const newExpanded = new Set(expandedAgents);
        if (newExpanded.has(agent)) {
            newExpanded.delete(agent);
        } else {
            newExpanded.add(agent);
        }
        setExpandedAgents(newExpanded);
    };

    useEffect(() => {
        fetchMemorySummary();
    }, []);

    if (loading) {
        return (
            <div className={`bg-white dark:bg-gray-900 rounded-xl p-6 ${className}`}>
                <div className="flex items-center gap-3 mb-4">
                    <Brain className="h-6 w-6 text-purple-500 animate-pulse" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Agent Memory
                    </h2>
                </div>
                <div className="text-center py-8 text-gray-300">Loading memories...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`bg-white dark:bg-gray-900 rounded-xl p-6 ${className}`}>
                <div className="flex items-center gap-3 mb-4">
                    <Brain className="h-6 w-6 text-purple-500" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Agent Memory
                    </h2>
                </div>
                <div className="text-center py-8">
                    <p className="text-red-500 mb-4">{error}</p>
                    <button
                        onClick={fetchMemorySummary}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                        <RefreshCw className="h-4 w-4 inline mr-2" />
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl p-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Brain className="h-6 w-6 text-purple-500" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Agent Memory
                    </h2>
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-200 dark:text-gray-200 text-sm rounded-full">
                        {summary?.total_memories || 0} memories
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchMemorySummary}
                        className="p-2 text-gray-300 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                        title="Refresh"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => clearMemories()}
                        disabled={clearing || !summary?.total_memories}
                        className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg disabled:opacity-80"
                    >
                        <Trash2 className="h-4 w-4 inline mr-1" />
                        Clear All
                    </button>
                </div>
            </div>

            {/* No memories state */}
            {!summary?.total_memories && (
                <div className="text-center py-12 text-gray-300 dark:text-gray-200">
                    <Brain className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>No agent memories yet</p>
                    <p className="text-sm mt-1">Memories will be stored as you interact with agents</p>
                </div>
            )}

            {/* Memory by agent */}
            <div className="space-y-3">
                {summary?.by_agent && Object.entries(summary.by_agent).map(([agent, memories]) => (
                    <div
                        key={agent}
                        className="border dark:border-gray-800 rounded-lg overflow-hidden"
                    >
                        {/* Agent header */}
                        <button
                            onClick={() => toggleAgent(agent)}
                            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-3 h-3 rounded-full ${AGENT_COLORS[agent] || 'bg-gray-500'}`} />
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {AGENT_LABELS[agent] || agent}
                                </span>
                                <span className="text-sm text-gray-300">
                                    {memories.length} memories
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        clearMemories(agent);
                                    }}
                                    disabled={clearingAgent === agent}
                                    className="p-1.5 text-gray-200 hover:text-red-500 rounded"
                                    title={`Clear ${AGENT_LABELS[agent]} memories`}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                                {expandedAgents.has(agent) ? (
                                    <ChevronDown className="h-5 w-5 text-gray-200" />
                                ) : (
                                    <ChevronRight className="h-5 w-5 text-gray-200" />
                                )}
                            </div>
                        </button>

                        {/* Expanded memories */}
                        {expandedAgents.has(agent) && (
                            <div className="border-t dark:border-gray-800 divide-y dark:divide-gray-800">
                                {memories.map((memory) => (
                                    <div key={memory.id} className="p-4 bg-gray-50/50 dark:bg-gray-800/30">
                                        <p className="text-gray-700 dark:text-gray-300 mb-2">
                                            {memory.summary}
                                        </p>
                                        <div className="flex items-center gap-4 text-sm text-gray-300">
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3.5 w-3.5" />
                                                {new Date(memory.created_at).toLocaleDateString()}
                                            </span>
                                            <span className={`px-2 py-0.5 rounded text-xs ${memory.memory_type === 'long_term'
                                                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                                    : 'bg-gray-100 text-gray-200 dark:bg-gray-800 dark:text-gray-200'
                                                }`}>
                                                {memory.memory_type.replace('_', ' ')}
                                            </span>
                                            <span className="text-gray-200">
                                                {Math.round(memory.importance * 100)}% importance
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default AgentMemoryPanel;
