'use client';

import { useState } from 'react';
import {
    Info,
    AlertTriangle,
    CheckCircle,
    XCircle,
    ChevronDown,
    ChevronRight,
    Search,
    Filter,
    Lightbulb,
    Shield,
    DollarSign,
    TrendingUp,
    Users,
    FileWarning,
} from 'lucide-react';

type ReasonCategory =
    | 'pricing'
    | 'performance'
    | 'compliance'
    | 'engagement'
    | 'risk'
    | 'opportunity';

type ReasonSeverity = 'info' | 'warning' | 'success' | 'error';

interface ReasonCode {
    code: string;
    category: ReasonCategory;
    severity: ReasonSeverity;
    title: string;
    description: string;
    impact: string;
    evidence?: string[];
    recommendations?: string[];
}

interface ReasonCodesProps {
    reasonCodes: ReasonCode[];
    title?: string;
    showSearch?: boolean;
    groupByCategory?: boolean;
}

// Example reason codes for demonstration
const exampleReasonCodes: ReasonCode[] = [
    {
        code: 'PRC-001',
        category: 'pricing',
        severity: 'success',
        title: 'Competitive Rate Achieved',
        description: 'Your rate of $1,500/post is within the optimal range for your follower count and engagement metrics.',
        impact: 'Increases likelihood of brand acceptance by 85%',
        evidence: [
            'Industry average for 50K followers: $800-$2,000',
            'Your engagement rate (4.2%) is above average (2.8%)',
        ],
        recommendations: [
            'Consider rate increase for exclusive content',
            'Negotiate package deals for multiple posts',
        ],
    },
    {
        code: 'PER-002',
        category: 'performance',
        severity: 'warning',
        title: 'Engagement Decline Detected',
        description: 'Your last 30-day engagement rate shows a 15% decline compared to the previous period.',
        impact: 'May affect future brand deal valuations',
        evidence: [
            'Current: 4.2% (down from 4.9%)',
            'Industry trend: -3% average decline',
            'Your decline exceeds market average',
        ],
        recommendations: [
            'Increase posting frequency',
            'Experiment with new content formats',
            'Review optimal posting times',
        ],
    },
    {
        code: 'CMP-001',
        category: 'compliance',
        severity: 'error',
        title: 'Missing FTC Disclosure',
        description: 'Sponsored post #1234 is missing required #ad disclosure per FTC guidelines.',
        impact: 'Potential legal liability and brand relationship damage',
        evidence: [
            'Post published: Jan 25, 2026',
            'Brand: TechCorp Inc.',
            'Disclosure scan: Not detected',
        ],
        recommendations: [
            'Edit post to include #ad or #sponsored',
            'Review disclosure guidelines',
            'Enable auto-disclosure for future posts',
        ],
    },
    {
        code: 'OPP-001',
        category: 'opportunity',
        severity: 'info',
        title: 'Cross-Platform Expansion',
        description: 'Based on your content style, TikTok expansion could increase reach by 200%.',
        impact: 'Estimated additional revenue: $2,500/month',
        evidence: [
            'Similar creators see 3x growth on TikTok',
            'Your video content performs well',
            'Target demographic active on TikTok',
        ],
        recommendations: [
            'Repurpose top 10 Instagram reels for TikTok',
            'Use our AI Twin for consistent posting',
        ],
    },
];

export function ReasonCodes({
    reasonCodes = exampleReasonCodes,
    title = 'Decision Reason Codes',
    showSearch = true,
    groupByCategory = true,
}: ReasonCodesProps) {
    const [expandedCodes, setExpandedCodes] = useState<Set<string>>(new Set());
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState<ReasonCategory | 'all'>('all');

    const toggleExpanded = (code: string) => {
        const newExpanded = new Set(expandedCodes);
        if (newExpanded.has(code)) {
            newExpanded.delete(code);
        } else {
            newExpanded.add(code);
        }
        setExpandedCodes(newExpanded);
    };

    const getSeverityIcon = (severity: ReasonSeverity) => {
        switch (severity) {
            case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
            case 'error': return <XCircle className="w-5 h-5 text-red-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const getSeverityColors = (severity: ReasonSeverity) => {
        switch (severity) {
            case 'success': return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20';
            case 'warning': return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
            case 'error': return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
            default: return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
        }
    };

    const getCategoryIcon = (category: ReasonCategory) => {
        switch (category) {
            case 'pricing': return <DollarSign className="w-4 h-4" />;
            case 'performance': return <TrendingUp className="w-4 h-4" />;
            case 'compliance': return <Shield className="w-4 h-4" />;
            case 'engagement': return <Users className="w-4 h-4" />;
            case 'risk': return <FileWarning className="w-4 h-4" />;
            case 'opportunity': return <Lightbulb className="w-4 h-4" />;
            default: return <Info className="w-4 h-4" />;
        }
    };

    const getCategoryLabel = (category: ReasonCategory) => {
        return category.charAt(0).toUpperCase() + category.slice(1);
    };

    const filteredCodes = reasonCodes.filter((rc) => {
        const matchesSearch = searchQuery === '' ||
            rc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            rc.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
            rc.description.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesCategory = categoryFilter === 'all' || rc.category === categoryFilter;

        return matchesSearch && matchesCategory;
    });

    const groupedCodes = groupByCategory
        ? filteredCodes.reduce((acc, rc) => {
            if (!acc[rc.category]) {
                acc[rc.category] = [];
            }
            acc[rc.category].push(rc);
            return acc;
        }, {} as Record<string, ReasonCode[]>)
        : { all: filteredCodes };

    const categories: ReasonCategory[] = ['pricing', 'performance', 'compliance', 'engagement', 'risk', 'opportunity'];

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                        <Info className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
                        <p className="text-sm text-gray-300">{filteredCodes.length} reason codes</p>
                    </div>
                </div>

                {/* Search and Filter */}
                <div className="flex gap-3">
                    {showSearch && (
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-200" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search reason codes..."
                                className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                    )}

                    <div className="relative">
                        <select aria-label="Filter or select option"
                            value={categoryFilter}
                            onChange={(e) => setCategoryFilter(e.target.value as ReasonCategory | 'all')}
                            className="appearance-none pl-8 pr-10 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                            <option value="all">All Categories</option>
                            {categories.map((cat) => (
                                <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                            ))}
                        </select>
                        <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-200" />
                    </div>
                </div>
            </div>

            {/* Reason Code List */}
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {Object.entries(groupedCodes).map(([category, codes]) => (
                    <div key={category}>
                        {groupByCategory && category !== 'all' && (
                            <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900/50 flex items-center gap-2 text-sm font-medium text-gray-200 dark:text-gray-200">
                                {getCategoryIcon(category as ReasonCategory)}
                                {getCategoryLabel(category as ReasonCategory)}
                                <span className="ml-auto text-xs bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded-full">
                                    {codes.length}
                                </span>
                            </div>
                        )}

                        {codes.map((rc) => (
                            <div key={rc.code} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                {/* Code Header */}
                                <button
                                    onClick={() => toggleExpanded(rc.code)}
                                    className="w-full p-4 flex items-start gap-3 text-left"
                                >
                                    {getSeverityIcon(rc.severity)}

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-mono text-xs text-gray-300 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                                                {rc.code}
                                            </span>
                                            <span className="font-medium text-gray-900 dark:text-white">
                                                {rc.title}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-200 dark:text-gray-200 line-clamp-2">
                                            {rc.description}
                                        </p>
                                        <p className="text-xs text-gray-300 mt-1">
                                            Impact: {rc.impact}
                                        </p>
                                    </div>

                                    {expandedCodes.has(rc.code) ? (
                                        <ChevronDown className="w-5 h-5 text-gray-200" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-gray-200" />
                                    )}
                                </button>

                                {/* Expanded Details */}
                                {expandedCodes.has(rc.code) && (
                                    <div className="px-4 pb-4 ml-8">
                                        <div className={`rounded-lg p-4 border ${getSeverityColors(rc.severity)}`}>
                                            {/* Evidence */}
                                            {rc.evidence && rc.evidence.length > 0 && (
                                                <div className="mb-4">
                                                    <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                        Evidence
                                                    </h5>
                                                    <ul className="space-y-1">
                                                        {rc.evidence.map((item, i) => (
                                                            <li key={i} className="text-sm text-gray-200 dark:text-gray-200 flex items-start gap-2">
                                                                <span className="text-gray-200 mt-1">•</span>
                                                                {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}

                                            {/* Recommendations */}
                                            {rc.recommendations && rc.recommendations.length > 0 && (
                                                <div>
                                                    <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                                                        <Lightbulb className="w-4 h-4 text-yellow-500" />
                                                        Recommendations
                                                    </h5>
                                                    <ul className="space-y-1">
                                                        {rc.recommendations.map((item, i) => (
                                                            <li key={i} className="text-sm text-gray-200 dark:text-gray-200 flex items-start gap-2">
                                                                <span className="text-indigo-500 font-bold mt-0.5">{i + 1}.</span>
                                                                {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            {filteredCodes.length === 0 && (
                <div className="p-8 text-center text-gray-300">
                    No reason codes match your criteria
                </div>
            )}
        </div>
    );
}

export default ReasonCodes;
