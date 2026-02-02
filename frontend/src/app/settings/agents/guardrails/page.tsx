'use client';

/**
 * Guardrail Settings Page
 * 
 * User interface for configuring agent guardrails, autonomy levels,
 * and action permissions.
 */

import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Zap, Lock, Unlock, Save, RotateCcw } from 'lucide-react';

interface GuardrailConfig {
    action_permissions: Record<string, string>;
    agent_autonomy: Record<string, string>;
    auto_approve_thresholds: Record<string, number>;
    risk_tolerance: 'conservative' | 'medium' | 'aggressive';
}

const ACTION_CATEGORIES = [
    { key: 'publishing', label: 'Publishing', description: 'Post content to platforms', icon: '📤' },
    { key: 'financial', label: 'Financial', description: 'Transactions and payments', icon: '💰' },
    { key: 'communication', label: 'Communication', description: 'Send DMs and emails', icon: '💬' },
    { key: 'analytics', label: 'Analytics', description: 'Read-only data analysis', icon: '📊' },
    { key: 'scheduling', label: 'Scheduling', description: 'Schedule future actions', icon: '📅' },
];

const AGENTS = [
    { key: 'content', label: 'Content Agent', color: 'blue' },
    { key: 'analytics', label: 'Analytics Agent', color: 'green' },
    { key: 'publishing', label: 'Publishing Agent', color: 'orange' },
    { key: 'revenue', label: 'Revenue Agent', color: 'yellow' },
    { key: 'engagement', label: 'Engagement Agent', color: 'pink' },
    { key: 'moderation', label: 'Moderation Agent', color: 'red' },
];

const PERMISSION_OPTIONS = [
    { value: 'prohibited', label: 'Prohibited', icon: Lock, color: 'red' },
    { value: 'gated', label: 'Requires Approval', icon: AlertTriangle, color: 'yellow' },
    { value: 'autonomous', label: 'Autonomous', icon: Unlock, color: 'green' },
];

const AUTONOMY_OPTIONS = [
    { value: 'low', label: 'Low', description: 'Approval required for most actions' },
    { value: 'medium', label: 'Medium', description: 'Approval for sensitive actions' },
    { value: 'high', label: 'High', description: 'Most actions auto-approved' },
];

export default function GuardrailSettingsPage() {
    const [config, setConfig] = useState<GuardrailConfig>({
        action_permissions: {},
        agent_autonomy: {},
        auto_approve_thresholds: {},
        risk_tolerance: 'medium',
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/agent-memory/guardrails');
            if (res.ok) {
                const data = await res.json();
                setConfig(data);
            }
        } catch (error) {
            console.error('Failed to fetch guardrail config:', error);
        } finally {
            setLoading(false);
        }
    };

    const saveConfig = async () => {
        setSaving(true);
        try {
            const res = await fetch('/api/v1/agent-memory/guardrails', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });
            if (res.ok) {
                setHasChanges(false);
            }
        } catch (error) {
            console.error('Failed to save guardrail config:', error);
        } finally {
            setSaving(false);
        }
    };

    const updatePermission = (category: string, value: string) => {
        setConfig(prev => ({
            ...prev,
            action_permissions: { ...prev.action_permissions, [category]: value },
        }));
        setHasChanges(true);
    };

    const updateAutonomy = (agent: string, value: string) => {
        setConfig(prev => ({
            ...prev,
            agent_autonomy: { ...prev.agent_autonomy, [agent]: value },
        }));
        setHasChanges(true);
    };

    const updateRiskTolerance = (value: 'conservative' | 'medium' | 'aggressive') => {
        setConfig(prev => ({ ...prev, risk_tolerance: value }));
        setHasChanges(true);
    };

    const resetToDefaults = () => {
        if (confirm('Reset all guardrail settings to defaults?')) {
            setConfig({
                action_permissions: {},
                agent_autonomy: {},
                auto_approve_thresholds: {},
                risk_tolerance: 'medium',
            });
            setHasChanges(true);
        }
    };

    if (loading) {
        return (
            <div className="p-8 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Shield className="h-8 w-8 text-indigo-500" />
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                            Guardrail Settings
                        </h1>
                        <p className="text-gray-500">
                            Configure agent permissions and autonomy levels
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={resetToDefaults}
                        className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg flex items-center gap-2"
                    >
                        <RotateCcw className="h-4 w-4" />
                        Reset
                    </button>
                    <button
                        onClick={saveConfig}
                        disabled={!hasChanges || saving}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                    >
                        <Save className="h-4 w-4" />
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>

            {/* Risk Tolerance */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Risk Tolerance
                </h2>
                <div className="grid grid-cols-3 gap-4">
                    {(['conservative', 'medium', 'aggressive'] as const).map((level) => (
                        <button
                            key={level}
                            onClick={() => updateRiskTolerance(level)}
                            className={`
                p-4 rounded-lg border-2 text-left transition-all
                ${config.risk_tolerance === level
                                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                                }
              `}
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <Zap className={`h-5 w-5 ${level === 'conservative' ? 'text-blue-500' :
                                        level === 'medium' ? 'text-yellow-500' : 'text-red-500'
                                    }`} />
                                <span className="font-medium capitalize text-gray-900 dark:text-white">
                                    {level}
                                </span>
                            </div>
                            <p className="text-sm text-gray-500">
                                {level === 'conservative' && 'Maximum oversight, all actions require approval'}
                                {level === 'medium' && 'Balanced autonomy with approval for sensitive actions'}
                                {level === 'aggressive' && 'Maximum autonomy, minimal approval required'}
                            </p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Action Permissions */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Action Permissions
                </h2>
                <div className="space-y-4">
                    {ACTION_CATEGORIES.map((category) => (
                        <div key={category.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{category.icon}</span>
                                <div>
                                    <div className="font-medium text-gray-900 dark:text-white">
                                        {category.label}
                                    </div>
                                    <div className="text-sm text-gray-500">{category.description}</div>
                                </div>
                            </div>
                            <select
                                value={config.action_permissions[category.key] || 'gated'}
                                onChange={(e) => updatePermission(category.key, e.target.value)}
                                className="px-3 py-2 bg-white dark:bg-gray-700 border dark:border-gray-600 rounded-lg"
                            >
                                {PERMISSION_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    ))}
                </div>
            </div>

            {/* Agent Autonomy */}
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Agent Autonomy Levels
                </h2>
                <div className="space-y-4">
                    {AGENTS.map((agent) => (
                        <div key={agent.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className={`w-3 h-3 rounded-full bg-${agent.color}-500`} />
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {agent.label}
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                {AUTONOMY_OPTIONS.map((opt) => (
                                    <button
                                        key={opt.value}
                                        onClick={() => updateAutonomy(agent.key, opt.value)}
                                        className={`
                      px-3 py-1.5 text-sm rounded-lg transition-colors
                      ${(config.agent_autonomy[agent.key] || 'medium') === opt.value
                                                ? 'bg-indigo-600 text-white'
                                                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                                            }
                    `}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
