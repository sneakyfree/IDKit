'use client';

import React, { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface AgentCapability {
    id: string;
    name: string;
    description: string;
    status: 'available' | 'busy' | 'offline';
    tasksCompleted: number;
    avgResponseTime: number;
}

interface PendingApproval {
    id: string;
    agentName: string;
    taskType: string;
    description: string;
    priority: 'low' | 'medium' | 'high';
    createdAt: string;
    status: 'pending' | 'approved' | 'rejected';
}

export default function AgentDashboard() {
    const [agents, setAgents] = useState<AgentCapability[]>([]);
    const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [agentsRes, approvalsRes] = await Promise.allSettled([
                    apiRequest<AgentCapability[]>('/api/v1/agents'),
                    apiRequest<PendingApproval[]>('/api/v1/agents/approvals'),
                ]);
                if (agentsRes.status === 'fulfilled') {
                    setAgents(Array.isArray(agentsRes.value) ? agentsRes.value : []);
                }
                if (approvalsRes.status === 'fulfilled') {
                    setPendingApprovals(Array.isArray(approvalsRes.value) ? approvalsRes.value : []);
                }
            } catch {
                // silently fail
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);
    const [taskInput, setTaskInput] = useState('');
    const [selectedAgent, setSelectedAgent] = useState('');

    const handleApprove = (id: string) => {
        setPendingApprovals(prev =>
            prev.map(a => (a.id === id ? { ...a, status: 'approved' as const } : a))
        );
    };

    const handleReject = (id: string) => {
        setPendingApprovals(prev =>
            prev.map(a => (a.id === id ? { ...a, status: 'rejected' as const } : a))
        );
    };

    const handleSubmitTask = (e: React.FormEvent) => {
        e.preventDefault();
        if (!taskInput.trim() || !selectedAgent) return;

        // In real app, would call API
        alert(`Task submitted to ${selectedAgent}: ${taskInput}`);
        setTaskInput('');
        setSelectedAgent('');
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'available':
                return 'bg-green-500';
            case 'busy':
                return 'bg-yellow-500';
            case 'offline':
                return 'bg-gray-500';
            default:
                return 'bg-gray-400';
        }
    };

    const getPriorityBadge = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
            case 'medium':
                return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
            case 'low':
                return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 text-white p-6">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                            AI Agent Dashboard
                        </h1>
                        <p className="text-gray-200 mt-1">Monitor, control, and approve AI agent actions</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="px-4 py-2 bg-purple-500/20 rounded-lg border border-purple-500/30">
                            <span className="text-purple-400 font-medium">{agents.filter(a => a.status === 'available').length}</span>
                            <span className="text-gray-200 ml-2">Agents Available</span>
                        </div>
                        <div className="px-4 py-2 bg-yellow-500/20 rounded-lg border border-yellow-500/30">
                            <span className="text-yellow-400 font-medium">{pendingApprovals.filter(a => a.status === 'pending').length}</span>
                            <span className="text-gray-200 ml-2">Pending Approvals</span>
                        </div>
                    </div>
                </div>

                {/* Task Submission */}
                <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        Submit New Task
                    </h2>
                    <form onSubmit={handleSubmitTask} className="flex gap-4">
                        <select aria-label="Filter or select option"
                            value={selectedAgent}
                            onChange={(e) => setSelectedAgent(e.target.value)}
                            className="bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="">Select Agent...</option>
                            {agents.filter(a => a.status === 'available').map(agent => (
                                <option key={agent.id} value={agent.name}>{agent.name}</option>
                            ))}
                        </select>
                        <input
                            type="text"
                            value={taskInput}
                            onChange={(e) => setTaskInput(e.target.value)}
                            placeholder="Describe the task you want the agent to perform..."
                            className="flex-1 bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                        <button
                            type="submit"
                            disabled={!taskInput.trim() || !selectedAgent}
                            className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-medium hover:opacity-90 disabled:opacity-80 disabled:cursor-not-allowed transition-opacity"
                        >
                            Submit Task
                        </button>
                    </form>
                </div>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Agent Capabilities */}
                    <div className="lg:col-span-1 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            Agent Capabilities
                        </h2>
                        <div className="space-y-4">
                            {agents.map(agent => (
                                <div key={agent.id} className="p-4 bg-gray-700/30 rounded-lg border border-gray-600/50 hover:border-purple-500/50 transition-colors">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-medium">{agent.name}</h3>
                                        <span className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                                    </div>
                                    <p className="text-sm text-gray-200 mb-3">{agent.description}</p>
                                    <div className="flex items-center gap-4 text-xs text-gray-300">
                                        <span>{agent.tasksCompleted} tasks</span>
                                        <span>~{agent.avgResponseTime}s avg</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Pending Approvals */}
                    <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Pending Approvals
                        </h2>
                        <div className="space-y-4">
                            {pendingApprovals.filter(a => a.status === 'pending').length === 0 ? (
                                <div className="text-center py-8 text-gray-300">
                                    <svg className="w-12 h-12 mx-auto mb-3 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <p>All caught up! No pending approvals.</p>
                                </div>
                            ) : (
                                pendingApprovals.filter(a => a.status === 'pending').map(approval => (
                                    <div key={approval.id} className="p-4 bg-gray-700/30 rounded-lg border border-gray-600/50">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className="text-sm text-purple-400 font-medium">{approval.agentName}</span>
                                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadge(approval.priority)}`}>
                                                        {approval.priority.toUpperCase()}
                                                    </span>
                                                    <span className="text-xs text-gray-300">{approval.createdAt}</span>
                                                </div>
                                                <p className="text-gray-300">{approval.description}</p>
                                                <span className="mt-2 inline-block text-xs text-gray-300 bg-gray-700/50 px-2 py-1 rounded">
                                                    {approval.taskType.replace('_', ' ')}
                                                </span>
                                            </div>
                                            <div className="flex gap-2 ml-4">
                                                <button
                                                    onClick={() => handleApprove(approval.id)}
                                                    className="px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors font-medium"
                                                >
                                                    Approve
                                                </button>
                                                <button
                                                    onClick={() => handleReject(approval.id)}
                                                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors font-medium"
                                                >
                                                    Reject
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* History Section */}
                        {pendingApprovals.filter(a => a.status !== 'pending').length > 0 && (
                            <div className="mt-6 pt-6 border-t border-gray-700">
                                <h3 className="text-lg font-medium mb-3 text-gray-200">Recent History</h3>
                                <div className="space-y-2">
                                    {pendingApprovals.filter(a => a.status !== 'pending').map(item => (
                                        <div key={item.id} className="flex items-center justify-between py-2 px-3 bg-gray-700/20 rounded-lg text-sm">
                                            <span className="text-gray-200">{item.description.substring(0, 50)}...</span>
                                            <span className={item.status === 'approved' ? 'text-green-400' : 'text-red-400'}>
                                                {item.status === 'approved' ? '✓ Approved' : '✗ Rejected'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
