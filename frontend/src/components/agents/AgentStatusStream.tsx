'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import {
    Activity,
    Bot,
    CheckCircle2,
    Clock,
    Loader2,
    Users,
    Zap,
    AlertCircle,
    ArrowRight,
    Pause,
    Play,
} from 'lucide-react';

// Agent status types
type AgentStatus = 'idle' | 'working' | 'awaiting_approval' | 'error' | 'offline';

interface Agent {
    agent_id: string;
    agent_name: string;
    agent_type: string;
    status: AgentStatus;
    current_task: string | null;
    tasks_completed: number;
    autonomy_level: string;
    last_activity: string;
}

interface TaskEvent {
    agent_id: string;
    agent_name: string;
    task_id: string;
    task_type: string;
    task_description: string;
    progress?: number;
    stage?: string;
    message?: string;
    started_at?: string;
    completed_at?: string;
    duration_seconds?: number;
    result_summary?: string;
    requires_approval?: boolean;
}

interface CollaborationEvent {
    collaboration_id: string;
    participating_agents: string[];
    current_phase: string;
    handoff?: {
        from: string | null;
        to: string | null;
    };
}

interface CrewStatus {
    agents: Agent[];
    active_tasks: number;
    pending_approvals: number;
    tasks_completed_today: number;
}

interface AgentStatusStreamProps {
    onAgentClick?: (agentId: string) => void;
    showActivityLog?: boolean;
    compact?: boolean;
}

export function AgentStatusStream({
    onAgentClick,
    showActivityLog = true,
    compact = false,
}: AgentStatusStreamProps) {
    const [connected, setConnected] = useState(false);
    const [crewStatus, setCrewStatus] = useState<CrewStatus | null>(null);
    const [activityLog, setActivityLog] = useState<TaskEvent[]>([]);
    const [collaborations, setCollaborations] = useState<CollaborationEvent[]>([]);
    const [isPaused, setIsPaused] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    // Connect to WebSocket
    const connect = useCallback(() => {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/agents/status`;

        try {
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                setConnected(true);
                console.log('Connected to agent status stream');
            };

            ws.onmessage = (event) => {
                if (isPaused) return;

                try {
                    const data = JSON.parse(event.data);
                    handleEvent(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                // Attempt to reconnect after 3 seconds
                setTimeout(connect, 3000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            wsRef.current = ws;
        } catch (e) {
            console.error('Failed to connect to WebSocket:', e);
            setTimeout(connect, 5000);
        }
    }, [isPaused]);

    // Handle incoming events
    const handleEvent = useCallback((data: any) => {
        const { type } = data;

        switch (type) {
            case 'agent_crew_status':
                setCrewStatus(data.data);
                break;

            case 'agent_status_update':
                setCrewStatus((prev) => {
                    if (!prev) return prev;
                    const agents = prev.agents.map((agent) =>
                        agent.agent_id === data.data.agent_id
                            ? { ...agent, ...data.data }
                            : agent
                    );
                    return { ...prev, agents };
                });
                break;

            case 'agent_task_started':
            case 'agent_task_completed':
                setActivityLog((prev) => [data.data, ...prev].slice(0, 50));
                break;

            case 'agent_task_progress':
                // Update existing task in activity log
                setActivityLog((prev) =>
                    prev.map((task) =>
                        task.task_id === data.data.task_id
                            ? { ...task, ...data.data }
                            : task
                    )
                );
                break;

            case 'agent_collaboration_update':
                setCollaborations((prev) => {
                    const existing = prev.findIndex(
                        (c) => c.collaboration_id === data.data.collaboration_id
                    );
                    if (existing >= 0) {
                        const updated = [...prev];
                        updated[existing] = data.data;
                        return updated;
                    }
                    return [data.data, ...prev];
                });
                break;
        }
    }, []);

    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [connect]);

    // Send ping every 30 seconds
    useEffect(() => {
        const interval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: AgentStatus) => {
        switch (status) {
            case 'working': return 'bg-green-500';
            case 'idle': return 'bg-gray-400';
            case 'awaiting_approval': return 'bg-yellow-500';
            case 'error': return 'bg-red-500';
            case 'offline': return 'bg-gray-300';
            default: return 'bg-gray-400';
        }
    };

    const getAgentIcon = (type: string) => {
        switch (type) {
            case 'content': return '✍️';
            case 'analytics': return '📊';
            case 'publishing': return '📤';
            case 'discovery': return '🔍';
            case 'engagement': return '💬';
            case 'revenue': return '💰';
            case 'moderation': return '🛡️';
            case 'orchestrator': return '🎯';
            default: return '🤖';
        }
    };

    if (compact) {
        return (
            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-200 dark:text-gray-200">
                    {crewStatus ? `${crewStatus.agents.filter(a => a.status === 'working').length} agents working` : 'Connecting...'}
                </span>
                {crewStatus && crewStatus.pending_approvals > 0 && (
                    <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                        {crewStatus.pending_approvals} pending
                    </span>
                )}
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                        <Zap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">Agent Crew Status</h3>
                        <div className="flex items-center gap-2 text-sm text-gray-300">
                            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                            {connected ? 'Live' : 'Reconnecting...'}
                        </div>
                    </div>
                </div>
                <button
                    onClick={() => setIsPaused(!isPaused)}
                    className="p-2 text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                    aria-label={isPaused ? 'Resume updates' : 'Pause updates'}
                >
                    {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                </button>
            </div>

            {/* Stats Bar */}
            {crewStatus && (
                <div className="grid grid-cols-4 gap-px bg-gray-200 dark:bg-gray-700">
                    <div className="p-3 bg-white dark:bg-gray-800 text-center">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {crewStatus.agents.length}
                        </div>
                        <div className="text-xs text-gray-300">Agents</div>
                    </div>
                    <div className="p-3 bg-white dark:bg-gray-800 text-center">
                        <div className="text-2xl font-bold text-green-600">
                            {crewStatus.active_tasks}
                        </div>
                        <div className="text-xs text-gray-300">Active</div>
                    </div>
                    <div className="p-3 bg-white dark:bg-gray-800 text-center">
                        <div className="text-2xl font-bold text-yellow-600">
                            {crewStatus.pending_approvals}
                        </div>
                        <div className="text-xs text-gray-300">Pending</div>
                    </div>
                    <div className="p-3 bg-white dark:bg-gray-800 text-center">
                        <div className="text-2xl font-bold text-indigo-600">
                            {crewStatus.tasks_completed_today}
                        </div>
                        <div className="text-xs text-gray-300">Today</div>
                    </div>
                </div>
            )}

            {/* Agent Grid */}
            <div className="p-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Active Agents</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {crewStatus?.agents.map((agent) => (
                        <button
                            key={agent.agent_id}
                            onClick={() => onAgentClick?.(agent.agent_id)}
                            className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-lg">{getAgentIcon(agent.agent_type)}</span>
                                <span className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                            </div>
                            <div className="font-medium text-sm text-gray-900 dark:text-white truncate">
                                {agent.agent_name}
                            </div>
                            <div className="text-xs text-gray-300 truncate">
                                {agent.current_task || 'Idle'}
                            </div>
                            {agent.status === 'working' && (
                                <div className="mt-2 flex items-center gap-1 text-xs text-green-600">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    Working...
                                </div>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Collaborations */}
            {collaborations.length > 0 && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        Active Collaborations
                    </h4>
                    <div className="space-y-2">
                        {collaborations.map((collab) => (
                            <div
                                key={collab.collaboration_id}
                                className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800"
                            >
                                <div className="flex items-center gap-2 text-sm">
                                    {collab.participating_agents.map((agent, i) => (
                                        <span key={agent} className="flex items-center gap-1">
                                            <span className="font-medium text-indigo-700 dark:text-indigo-300">
                                                {agent}
                                            </span>
                                            {i < collab.participating_agents.length - 1 && (
                                                <ArrowRight className="w-3 h-3 text-indigo-400" />
                                            )}
                                        </span>
                                    ))}
                                </div>
                                <div className="text-xs text-indigo-600 dark:text-indigo-400 mt-1">
                                    Phase: {collab.current_phase}
                                    {collab.handoff && collab.handoff.from && (
                                        <span className="ml-2">
                                            Handoff: {collab.handoff.from} → {collab.handoff.to}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Activity Log */}
            {showActivityLog && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Recent Activity
                    </h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                        {activityLog.length === 0 ? (
                            <div className="text-sm text-gray-300 text-center py-4">
                                No recent activity
                            </div>
                        ) : (
                            activityLog.map((task, i) => (
                                <div
                                    key={`${task.task_id}-${i}`}
                                    className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50"
                                >
                                    {task.completed_at ? (
                                        <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                                    ) : task.progress !== undefined && task.progress > 0 ? (
                                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin mt-0.5" />
                                    ) : (
                                        <Clock className="w-4 h-4 text-gray-200 mt-0.5" />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                            {task.agent_name}: {task.task_description}
                                        </div>
                                        {task.progress !== undefined && task.progress < 100 && (
                                            <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                                                <div
                                                    className="bg-blue-500 h-1 rounded-full transition-all"
                                                    style={{ width: `${task.progress}%` }}
                                                />
                                            </div>
                                        )}
                                        {task.result_summary && (
                                            <div className="text-xs text-gray-300 mt-1 truncate">
                                                {task.result_summary}
                                            </div>
                                        )}
                                        {task.requires_approval && (
                                            <div className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                                                <AlertCircle className="w-3 h-3" />
                                                Requires Approval
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

// Export hook for using in other components
export function useAgentStatus() {
    const [connected, setConnected] = useState(false);
    const [crewStatus, setCrewStatus] = useState<CrewStatus | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const connect = useCallback(() => {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/agents/status`;

        try {
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => setConnected(true);
            ws.onclose = () => {
                setConnected(false);
                setTimeout(connect, 3000);
            };
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'agent_crew_status') {
                    setCrewStatus(data.data);
                }
            };

            wsRef.current = ws;
        } catch (e) {
            setTimeout(connect, 5000);
        }
    }, []);

    useEffect(() => {
        connect();
        return () => wsRef.current?.close();
    }, [connect]);

    return { connected, crewStatus };
}
