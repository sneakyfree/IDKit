/**
 * useExplainability Hook
 * 
 * React hook for Multi-View Explainability APIs:
 * - Render insights for different views (creator, manager, technical, audit)
 * - Audit snapshots
 * - Version tracking and delta reports
 */

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types
export type ViewType = 'creator' | 'manager' | 'technical' | 'audit';

export interface Insight {
    insight_id: string;
    insight_type: string;
    title: string;
    summary: string;
    data: Record<string, unknown>;
    confidence?: number;
    sample_size?: number;
    p_value?: number;
    evidence_chain: string[];
    data_sources: string[];
    generated_at: string;
}

export interface RenderedInsight {
    view_type: ViewType;
    headline: string;
    body: string;
    action_items: string[];
    formatted_data: Record<string, unknown>;
    footnotes: string[];
    evidence_summary?: string;
    statistical_notes?: string;
    audit_trail?: string[];
}

export interface AuditSnapshot {
    snapshot_id: string;
    snapshot_type: string;
    created_at: string;
    analysis_type?: string;
    description?: string;
    data_sources: Array<{
        source_name: string;
        data_hash: string;
        queried_at: string;
    }>;
    model_versions: Record<string, string>;
    rule_versions: Record<string, string>;
    recommendations: unknown[];
    confidence_scores: Record<string, number>;
    content_hash: string;
    is_sealed: boolean;
}

export interface DeltaChange {
    field: string;
    old_value: unknown;
    new_value: unknown;
    change_type: string;
    impact: string;
}

export interface DeltaReport {
    before_snapshot_id: string;
    after_snapshot_id: string;
    changes: DeltaChange[];
    summary: string;
    recommendations_added: number;
    recommendations_removed: number;
    recommendations_modified: number;
}

export interface VersionInfo {
    name: string;
    version: string;
    version_type: string;
    is_active: boolean;
    registered_at: string;
}

export function useExplainability() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getAuthHeaders = useCallback(() => {
        const token = localStorage.getItem('token');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
        };
    }, []);

    // ============== Insight Rendering ==============

    const renderInsight = useCallback(async (
        insight: Insight,
        viewType: ViewType
    ): Promise<RenderedInsight | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/api/v1/explainability/render`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    insight,
                    view_type: viewType,
                }),
            });

            if (!response.ok) throw new Error('Failed to render insight');
            const data = await response.json();
            return data.rendered_insight;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const renderAllViews = useCallback(async (
        insight: Insight
    ): Promise<Record<ViewType, RenderedInsight> | null> => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/v1/explainability/render-all`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ insight }),
            });

            if (!response.ok) throw new Error('Failed to render all views');
            const data = await response.json();
            return data.views;
        } catch {
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getAvailableViews = useCallback(async (): Promise<Array<{
        view_type: ViewType;
        description: string;
    }>> => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/explainability/views`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) return [];
            const data = await response.json();
            return data.views;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    // ============== Audit Snapshots ==============

    const createSnapshot = useCallback(async (
        snapshotType: string,
        options?: {
            analysis_type?: string;
            description?: string;
            configuration?: Record<string, unknown>;
            recommendations?: unknown[];
        }
    ): Promise<AuditSnapshot | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/api/v1/audit/snapshots`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    snapshot_type: snapshotType,
                    ...options,
                }),
            });

            if (!response.ok) throw new Error('Failed to create snapshot');
            const data = await response.json();
            return data.snapshot;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getSnapshots = useCallback(async (
        snapshotType?: string
    ): Promise<AuditSnapshot[]> => {
        try {
            const params = snapshotType ? `?snapshot_type=${snapshotType}` : '';
            const response = await fetch(
                `${API_BASE}/api/v1/audit/snapshots${params}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) return [];
            const data = await response.json();
            return data.snapshots;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    const getSnapshot = useCallback(async (
        snapshotId: string
    ): Promise<AuditSnapshot | null> => {
        try {
            const response = await fetch(
                `${API_BASE}/api/v1/audit/snapshots/${snapshotId}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) return null;
            const data = await response.json();
            return data.snapshot;
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    // ============== Delta Reports ==============

    const generateDelta = useCallback(async (
        beforeId: string,
        afterId: string
    ): Promise<DeltaReport | null> => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/v1/audit/delta`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    before_snapshot_id: beforeId,
                    after_snapshot_id: afterId,
                }),
            });

            if (!response.ok) throw new Error('Failed to generate delta');
            const data = await response.json();
            return data.delta;
        } catch {
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    // ============== Version Registry ==============

    const getActiveVersions = useCallback(async (): Promise<VersionInfo[]> => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/audit/versions`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) return [];
            const data = await response.json();
            return data.versions;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    const getVersionHistory = useCallback(async (
        componentName: string
    ): Promise<VersionInfo[]> => {
        try {
            const response = await fetch(
                `${API_BASE}/api/v1/audit/versions/${componentName}/history`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) return [];
            const data = await response.json();
            return data.history;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    return {
        loading,
        error,
        // Insight Rendering
        renderInsight,
        renderAllViews,
        getAvailableViews,
        // Audit Snapshots
        createSnapshot,
        getSnapshots,
        getSnapshot,
        // Delta Reports
        generateDelta,
        // Version Registry
        getActiveVersions,
        getVersionHistory,
    };
}
