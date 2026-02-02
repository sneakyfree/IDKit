'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Download,
  Calendar,
  User,
  Bot,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  MoreVertical,
  RefreshCw,
} from 'lucide-react';

type ActionType = 
  | 'agent_action'
  | 'user_action'
  | 'system_event'
  | 'approval'
  | 'rejection'
  | 'data_change';

type ActionStatus = 'success' | 'failure' | 'pending';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action_type: ActionType;
  actor_type: 'user' | 'agent' | 'system';
  actor_id: string;
  actor_name: string;
  action: string;
  target_type?: string;
  target_id?: string;
  target_name?: string;
  status: ActionStatus;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
}

interface AuditLogViewerProps {
  entityType?: string;
  entityId?: string;
  userId?: string;
  onViewDetails?: (entry: AuditLogEntry) => void;
  pageSize?: number;
}

// Mock audit log data
const mockAuditLogs: AuditLogEntry[] = [
  {
    id: 'log-001',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    action_type: 'agent_action',
    actor_type: 'agent',
    actor_id: 'content-agent',
    actor_name: 'Content Agent',
    action: 'Generated draft post',
    target_type: 'content',
    target_id: 'post-123',
    target_name: 'Instagram caption for Nike',
    status: 'success',
    details: {
      word_count: 150,
      hashtags: 8,
      mentions: 2,
    },
  },
  {
    id: 'log-002',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    action_type: 'approval',
    actor_type: 'user',
    actor_id: 'user-456',
    actor_name: 'John Creator',
    action: 'Approved publishing',
    target_type: 'content',
    target_id: 'post-122',
    target_name: 'Sponsored post for TechCorp',
    status: 'success',
    details: {
      approval_type: 'content_publish',
      scheduled_for: '2026-01-26T10:00:00Z',
    },
    ip_address: '192.168.1.1',
    user_agent: 'Chrome/120.0',
  },
  {
    id: 'log-003',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    action_type: 'rejection',
    actor_type: 'user',
    actor_id: 'user-456',
    actor_name: 'John Creator',
    action: 'Rejected brand deal',
    target_type: 'deal',
    target_id: 'deal-789',
    target_name: '$500 post from CryptoScam Inc.',
    status: 'success',
    details: {
      reason: 'Brand does not align with values',
      deal_value: 500,
    },
  },
  {
    id: 'log-004',
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    action_type: 'agent_action',
    actor_type: 'agent',
    actor_id: 'analytics-agent',
    actor_name: 'Analytics Agent',
    action: 'Generated weekly report',
    target_type: 'report',
    target_id: 'report-456',
    target_name: 'Weekly Performance Report',
    status: 'success',
    details: {
      metrics_analyzed: 42,
      insights_generated: 8,
    },
  },
  {
    id: 'log-005',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    action_type: 'system_event',
    actor_type: 'system',
    actor_id: 'system',
    actor_name: 'System',
    action: 'Platform connected',
    target_type: 'integration',
    target_id: 'int-tiktok',
    target_name: 'TikTok Account',
    status: 'success',
    details: {
      platform: 'tiktok',
      followers_synced: 125000,
    },
  },
  {
    id: 'log-006',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    action_type: 'data_change',
    actor_type: 'user',
    actor_id: 'user-456',
    actor_name: 'John Creator',
    action: 'Updated profile',
    target_type: 'profile',
    target_id: 'profile-456',
    target_name: 'Creator Profile',
    status: 'success',
    details: {
      fields_changed: ['bio', 'niche', 'rates'],
    },
  },
  {
    id: 'log-007',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    action_type: 'agent_action',
    actor_type: 'agent',
    actor_id: 'publishing-agent',
    actor_name: 'Publishing Agent',
    action: 'Failed to publish',
    target_type: 'content',
    target_id: 'post-120',
    target_name: 'Scheduled Story',
    status: 'failure',
    details: {
      error: 'Instagram API rate limit exceeded',
      retry_at: new Date(Date.now() + 1000 * 60 * 60).toISOString(),
    },
  },
];

export function AuditLogViewer({
  entityType,
  entityId,
  userId,
  onViewDetails,
  pageSize = 10,
}: AuditLogViewerProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionTypeFilter, setActionTypeFilter] = useState<ActionType | 'all'>('all');
  const [actorTypeFilter, setActorTypeFilter] = useState<'all' | 'user' | 'agent' | 'system'>('all');
  const [dateRange, setDateRange] = useState<'all' | '1h' | '24h' | '7d' | '30d'>('all');

  const fetchLogs = useCallback(() => {
    setLoading(true);
    
    // Simulated API call with filtering
    setTimeout(() => {
      let filtered = mockAuditLogs;
      
      if (actionTypeFilter !== 'all') {
        filtered = filtered.filter((log) => log.action_type === actionTypeFilter);
      }
      
      if (actorTypeFilter !== 'all') {
        filtered = filtered.filter((log) => log.actor_type === actorTypeFilter);
      }
      
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter((log) =>
          log.action.toLowerCase().includes(query) ||
          log.actor_name.toLowerCase().includes(query) ||
          log.target_name?.toLowerCase().includes(query)
        );
      }
      
      if (dateRange !== 'all') {
        const now = Date.now();
        const ranges: Record<string, number> = {
          '1h': 60 * 60 * 1000,
          '24h': 24 * 60 * 60 * 1000,
          '7d': 7 * 24 * 60 * 60 * 1000,
          '30d': 30 * 24 * 60 * 60 * 1000,
        };
        const cutoff = now - ranges[dateRange];
        filtered = filtered.filter((log) => new Date(log.timestamp).getTime() > cutoff);
      }
      
      setTotalPages(Math.ceil(filtered.length / pageSize));
      const start = (currentPage - 1) * pageSize;
      setLogs(filtered.slice(start, start + pageSize));
      setLoading(false);
    }, 300);
  }, [actionTypeFilter, actorTypeFilter, searchQuery, dateRange, currentPage, pageSize]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActorIcon = (actorType: string) => {
    switch (actorType) {
      case 'user': return <User className="w-4 h-4" />;
      case 'agent': return <Bot className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: ActionStatus) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failure': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getActionTypeColor = (type: ActionType) => {
    switch (type) {
      case 'agent_action': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      case 'user_action': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
      case 'approval': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'rejection': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'data_change': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Actor', 'Action', 'Target', 'Status'],
      ...logs.map((log) => [
        log.timestamp,
        log.actor_name,
        log.action,
        log.target_name || '',
        log.status,
      ]),
    ].map((row) => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audit-log.csv';
    a.click();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
              <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Audit Log</h3>
              <p className="text-sm text-gray-500">Complete activity history</p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={fetchLogs}
              className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleExport}
              className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              title="Export CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search actions..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          <select
            value={actionTypeFilter}
            onChange={(e) => setActionTypeFilter(e.target.value as ActionType | 'all')}
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
          >
            <option value="all">All Actions</option>
            <option value="agent_action">Agent Actions</option>
            <option value="user_action">User Actions</option>
            <option value="approval">Approvals</option>
            <option value="rejection">Rejections</option>
            <option value="data_change">Data Changes</option>
          </select>
          
          <select
            value={actorTypeFilter}
            onChange={(e) => setActorTypeFilter(e.target.value as 'all' | 'user' | 'agent' | 'system')}
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
          >
            <option value="all">All Actors</option>
            <option value="user">Users</option>
            <option value="agent">Agents</option>
            <option value="system">System</option>
          </select>
          
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as 'all' | '1h' | '24h' | '7d' | '30d')}
            className="px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
          >
            <option value="all">All Time</option>
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Log Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-gray-400 mx-auto" />
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No audit logs found
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 bg-gray-100 dark:bg-gray-700 rounded">
                        {getActorIcon(log.actor_type)}
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {log.actor_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getActionTypeColor(log.action_type)}`}>
                        {log.action_type.replace('_', ' ')}
                      </span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {log.action}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {log.target_name || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getStatusIcon(log.status)}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onViewDetails?.(log)}
                      className="p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                      title="View details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + 1;
              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`w-8 h-8 text-sm rounded-lg ${
                    currentPage === page
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {page}
                </button>
              );
            })}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditLogViewer;
