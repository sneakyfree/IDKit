"use client";

import { useState, useEffect } from "react";
import { BarChart3, Users, TrendingUp, Loader2, Download, Calendar, ArrowUpRight, ArrowDownRight, Eye, Heart, Share2 } from "lucide-react";

/**
 * Joint Analytics UI
 * 
 * Shared performance data for collaborations
 */

interface JointProject {
    id: string;
    name: string;
    collaborators: string[];
    startDate: string;
    endDate?: string;
    status: "active" | "completed";
}

interface JointMetrics {
    projectId: string;
    period: string;
    combined: {
        views: number;
        engagement: number;
        revenue: number;
        followers: number;
    };
    byCollaborator: {
        name: string;
        views: number;
        engagement: number;
        revenue: number;
        contribution: number;
    }[];
    trends: {
        views: number;
        engagement: number;
        revenue: number;
    };
}

const MOCK_PROJECTS: JointProject[] = [
    {
        id: "1",
        name: "Tech Review Collab 2024",
        collaborators: ["You", "TechReviewer", "VideoEditor"],
        startDate: "2024-01-01",
        status: "active",
    },
    {
        id: "2",
        name: "Podcast: Creator Economy Series",
        collaborators: ["You", "Co-Host"],
        startDate: "2023-10-01",
        status: "active",
    },
];

const MOCK_METRICS: JointMetrics = {
    projectId: "1",
    period: "Last 30 days",
    combined: {
        views: 125000,
        engagement: 8500,
        revenue: 4200,
        followers: 3200,
    },
    byCollaborator: [
        { name: "You", views: 75000, engagement: 5100, revenue: 2520, contribution: 60 },
        { name: "TechReviewer", views: 35000, engagement: 2380, revenue: 1176, contribution: 28 },
        { name: "VideoEditor", views: 15000, engagement: 1020, revenue: 504, contribution: 12 },
    ],
    trends: {
        views: 15.2,
        engagement: 8.7,
        revenue: 22.5,
    },
};

export default function JointAnalyticsPage() {
    const [projects, setProjects] = useState<JointProject[]>([]);
    const [selectedProject, setSelectedProject] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<JointMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [dateRange, setDateRange] = useState("30d");

    useEffect(() => {
        setTimeout(() => {
            setProjects(MOCK_PROJECTS);
            setSelectedProject(MOCK_PROJECTS[0]?.id || null);
            setMetrics(MOCK_METRICS);
            setLoading(false);
        }, 800);
    }, []);

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Joint Analytics</h1>
                        <p className="text-gray-400">Shared performance data for collaborations</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-xl hover:bg-gray-700">
                        <Download className="w-5 h-5" />
                        Export Report
                    </button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : (
                    <div className="grid md:grid-cols-4 gap-6">
                        {/* Project Selector */}
                        <div className="space-y-4">
                            <h2 className="text-lg font-semibold">Collaborations</h2>
                            {projects.map((project) => (
                                <div
                                    key={project.id}
                                    onClick={() => setSelectedProject(project.id)}
                                    className={`p-4 rounded-xl cursor-pointer transition-all ${selectedProject === project.id
                                            ? "bg-purple-600/20 border border-purple-500"
                                            : "bg-gray-900 hover:bg-gray-800"
                                        }`}
                                >
                                    <h3 className="font-medium mb-1">{project.name}</h3>
                                    <div className="flex items-center gap-2 text-sm text-gray-500">
                                        <Users className="w-4 h-4" />
                                        {project.collaborators.length} collaborators
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Metrics */}
                        <div className="md:col-span-3 space-y-6">
                            {metrics && (
                                <>
                                    {/* Date Range */}
                                    <div className="flex gap-2">
                                        {["7d", "30d", "90d", "all"].map((range) => (
                                            <button
                                                key={range}
                                                onClick={() => setDateRange(range)}
                                                className={`px-4 py-2 rounded-lg text-sm ${dateRange === range ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                                    }`}
                                            >
                                                {range === "all" ? "All Time" : `Last ${range.replace("d", " days")}`}
                                            </button>
                                        ))}
                                    </div>

                                    {/* Combined Stats */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <StatCard
                                            label="Total Views"
                                            value={metrics.combined.views.toLocaleString()}
                                            trend={metrics.trends.views}
                                            icon={<Eye className="w-5 h-5" />}
                                        />
                                        <StatCard
                                            label="Engagement"
                                            value={metrics.combined.engagement.toLocaleString()}
                                            trend={metrics.trends.engagement}
                                            icon={<Heart className="w-5 h-5" />}
                                        />
                                        <StatCard
                                            label="Revenue"
                                            value={`$${metrics.combined.revenue.toLocaleString()}`}
                                            trend={metrics.trends.revenue}
                                            icon={<TrendingUp className="w-5 h-5" />}
                                        />
                                        <StatCard
                                            label="Followers"
                                            value={`+${metrics.combined.followers.toLocaleString()}`}
                                            icon={<Users className="w-5 h-5" />}
                                        />
                                    </div>

                                    {/* By Collaborator */}
                                    <div className="bg-gray-900 rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold mb-4">Performance by Collaborator</h3>
                                        <div className="space-y-4">
                                            {metrics.byCollaborator.map((collab) => (
                                                <div key={collab.name} className="flex items-center gap-4">
                                                    <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center">
                                                        {collab.name.charAt(0)}
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center justify-between mb-1">
                                                            <p className="font-medium">{collab.name}</p>
                                                            <span className="text-sm text-gray-400">{collab.contribution}%</span>
                                                        </div>
                                                        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-purple-500"
                                                                style={{ width: `${collab.contribution}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="grid grid-cols-3 gap-4 text-sm">
                                                        <div>
                                                            <p className="text-gray-500">Views</p>
                                                            <p className="font-medium">{(collab.views / 1000).toFixed(1)}K</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500">Engagement</p>
                                                            <p className="font-medium">{(collab.engagement / 1000).toFixed(1)}K</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500">Revenue</p>
                                                            <p className="font-medium text-green-400">${collab.revenue}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Chart Placeholder */}
                                    <div className="bg-gray-900 rounded-2xl p-6">
                                        <h3 className="text-lg font-semibold mb-4">Performance Over Time</h3>
                                        <div className="h-64 flex items-center justify-center border border-gray-800 rounded-xl">
                                            <div className="text-center text-gray-500">
                                                <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                                                <p>Charts render with actual data integration</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}

function StatCard({
    label,
    value,
    trend,
    icon,
}: {
    label: string;
    value: string;
    trend?: number;
    icon: React.ReactNode;
}) {
    return (
        <div className="bg-gray-900 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-500 mb-2">
                {icon}
                <span className="text-sm">{label}</span>
            </div>
            <div className="flex items-end justify-between">
                <p className="text-2xl font-bold">{value}</p>
                {trend !== undefined && (
                    <span className={`flex items-center text-sm ${trend >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {trend >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                        {Math.abs(trend)}%
                    </span>
                )}
            </div>
        </div>
    );
}
