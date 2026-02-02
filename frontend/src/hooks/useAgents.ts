'use client';

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5857';

interface AgentCapability {
    id: string;
    name: string;
    description: string;
    status: 'available' | 'busy' | 'offline';
    taskTypes: string[];
}

interface AgentTask {
    id: string;
    agentId: string;
    taskType: string;
    input: Record<string, unknown>;
    status: 'pending' | 'running' | 'completed' | 'failed';
    result?: Record<string, unknown>;
    error?: string;
    createdAt: string;
    completedAt?: string;
}

interface PendingApproval {
    id: string;
    agentId: string;
    agentName: string;
    actionType: string;
    description: string;
    payload: Record<string, unknown>;
    priority: 'low' | 'medium' | 'high';
    createdAt: string;
}

interface UseAgentsReturn {
    // State
    capabilities: AgentCapability[];
    pendingApprovals: PendingApproval[];
    taskHistory: AgentTask[];
    isLoading: boolean;
    error: string | null;

    // Actions
    fetchCapabilities: () => Promise<void>;
    fetchPendingApprovals: () => Promise<void>;
    fetchTaskHistory: () => Promise<void>;
    submitTask: (agentId: string, taskType: string, input: Record<string, unknown>) => Promise<AgentTask | null>;
    approveAction: (approvalId: string) => Promise<boolean>;
    rejectAction: (approvalId: string, reason?: string) => Promise<boolean>;
}

export function useAgents(authToken?: string): UseAgentsReturn {
    const [capabilities, setCapabilities] = useState<AgentCapability[]>([]);
    const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
    const [taskHistory, setTaskHistory] = useState<AgentTask[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const fetchCapabilities = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/capabilities`, { headers });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to fetch agent capabilities');
            }
            const data = await res.json();
            setCapabilities(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    const fetchPendingApprovals = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/pending`, { headers });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to fetch pending approvals');
            }
            const data = await res.json();
            setPendingApprovals(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    const fetchTaskHistory = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/history`, { headers });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to fetch task history');
            }
            const data = await res.json();
            setTaskHistory(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    const submitTask = useCallback(async (agentId: string, taskType: string, input: Record<string, unknown>) => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/task`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ agent_id: agentId, task_type: taskType, input }),
            });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to submit task');
            }
            const data = await res.json();
            return data as AgentTask;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    const approveAction = useCallback(async (approvalId: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/approve/${approvalId}`, {
                method: 'POST',
                headers,
            });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to approve action');
            }
            // Remove from pending list
            setPendingApprovals(prev => prev.filter(a => a.id !== approvalId));
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return false;
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    const rejectAction = useCallback(async (approvalId: string, reason?: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/agents/agents/reject/${approvalId}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ reason }),
            });
            if (!res.ok) {
                if (res.status === 401) throw new Error('Authentication required');
                throw new Error('Failed to reject action');
            }
            // Remove from pending list
            setPendingApprovals(prev => prev.filter(a => a.id !== approvalId));
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return false;
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    return {
        capabilities,
        pendingApprovals,
        taskHistory,
        isLoading,
        error,
        fetchCapabilities,
        fetchPendingApprovals,
        fetchTaskHistory,
        submitTask,
        approveAction,
        rejectAction,
    };
}

export default useAgents;
