"use client";

import { useState, useEffect } from "react";
import { Users, Plus, MessageSquare, FileText, Video, Loader2, CheckCircle, Clock, Send, Sparkles } from "lucide-react";
import { collaborateApi } from "@/lib/api";

/**
 * Content Co-Creation UI
 * 
 * Collaborative content creation with other creators
 */

interface Collaboration {
    id: string;
    title: string;
    type: "video" | "podcast" | "article" | "campaign";
    status: "planning" | "in-progress" | "review" | "published";
    collaborators: Collaborator[];
    createdAt: string;
    deadline?: string;
    assets: CollabAsset[];
}

interface Collaborator {
    id: string;
    name: string;
    avatar?: string;
    role: "owner" | "editor" | "contributor" | "reviewer";
    joinedAt: string;
}

interface CollabAsset {
    id: string;
    name: string;
    type: "script" | "video" | "audio" | "image" | "document";
    uploadedBy: string;
    uploadedAt: string;
    status: "draft" | "approved";
}

interface ChatMessage {
    id: string;
    userId: string;
    userName: string;
    content: string;
    timestamp: string;
}



export default function CoCreationPage() {
    const [collaborations, setCollaborations] = useState<Collaboration[]>([]);
    const [selectedCollab, setSelectedCollab] = useState<Collaboration | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchProjects() {
            try {
                setLoading(true);
                const response = await collaborateApi.listProjects();
                setCollaborations((response.projects || []).map((p: any) => ({
                    id: p.id as string,
                    title: (p.name as string) || "Untitled",
                    type: ((p.project_type as string) || "video") as Collaboration["type"],
                    status: ((p.status as string) === "active" ? "in-progress" : (p.status as string) === "completed" ? "published" : "planning") as Collaboration["status"],
                    collaborators: [],
                    createdAt: p.created_at as string || new Date().toISOString(),
                    assets: [],
                })));
            } catch {
                setCollaborations([]);
            } finally {
                setLoading(false);
            }
        }
        fetchProjects();
    }, []);

    const stats = {
        active: collaborations.filter(c => c.status === "in-progress").length,
        planning: collaborations.filter(c => c.status === "planning").length,
        completed: collaborations.filter(c => c.status === "published").length,
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Content Co-Creation</h1>
                        <p className="text-gray-400">Collaborate with other creators on shared projects</p>
                    </div>
                    <button
                        onClick={() => setShowCreate(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        New Collaboration
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold text-blue-400">{stats.active}</p>
                        <p className="text-sm text-gray-500">Active Projects</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold text-yellow-400">{stats.planning}</p>
                        <p className="text-sm text-gray-500">In Planning</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold text-green-400">{stats.completed}</p>
                        <p className="text-sm text-gray-500">Published</p>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : collaborations.length === 0 ? (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <Users className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No collaborations yet</h3>
                        <p className="text-gray-500 mb-6">Start collaborating with other creators.</p>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Start Collaboration
                        </button>
                    </div>
                ) : (
                    <div className="grid md:grid-cols-2 gap-4">
                        {collaborations.map((collab) => (
                            <CollabCard
                                key={collab.id}
                                collab={collab}
                                onClick={() => setSelectedCollab(collab)}
                            />
                        ))}
                    </div>
                )}

                {/* Detail Modal */}
                {selectedCollab && (
                    <CollabDetailModal
                        collab={selectedCollab}
                        onClose={() => setSelectedCollab(null)}
                    />
                )}

                {/* Create Modal */}
                {showCreate && (
                    <CreateCollabModal
                        onClose={() => setShowCreate(false)}
                        onCreate={(collab) => {
                            setCollaborations(prev => [...prev, collab]);
                            setShowCreate(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function CollabCard({ collab, onClick }: { collab: Collaboration; onClick: () => void }) {
    const statusColors = {
        planning: "text-yellow-400 bg-yellow-400/10",
        "in-progress": "text-blue-400 bg-blue-400/10",
        review: "text-purple-400 bg-purple-400/10",
        published: "text-green-400 bg-green-400/10",
    };

    const typeIcons = {
        video: Video,
        podcast: Sparkles,
        article: FileText,
        campaign: Users,
    };

    const TypeIcon = typeIcons[collab.type];

    return (
        <div
            onClick={onClick}
            className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors cursor-pointer"
        >
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center">
                        <TypeIcon className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold">{collab.title}</h3>
                        <p className="text-sm text-gray-500 capitalize">{collab.type}</p>
                    </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full capitalize ${statusColors[collab.status]}`}>
                    {collab.status.replace("-", " ")}
                </span>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex -space-x-2">
                    {collab.collaborators.slice(0, 4).map((c, i) => (
                        <div
                            key={c.id}
                            className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-xs font-medium border-2 border-gray-900"
                            title={c.name}
                        >
                            {c.name.charAt(0)}
                        </div>
                    ))}
                    {collab.collaborators.length > 4 && (
                        <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-xs border-2 border-gray-900">
                            +{collab.collaborators.length - 4}
                        </div>
                    )}
                </div>
                {collab.deadline && (
                    <span className="text-xs text-gray-500">
                        Due {new Date(collab.deadline).toLocaleDateString()}
                    </span>
                )}
            </div>
        </div>
    );
}

function CollabDetailModal({ collab, onClose }: { collab: Collaboration; onClose: () => void }) {
    const [activeTab, setActiveTab] = useState<"overview" | "assets" | "chat">("overview");
    const [messages, setMessages] = useState<ChatMessage[]>([
        { id: "1", userId: "2", userName: "TechReviewer", content: "Just uploaded the B-roll!", timestamp: "2024-01-12T10:30:00Z" },
        { id: "2", userId: "1", userName: "You", content: "Great! I'll review it today.", timestamp: "2024-01-12T11:00:00Z" },
    ]);
    const [newMessage, setNewMessage] = useState("");

    const sendMessage = () => {
        if (!newMessage.trim()) return;
        setMessages(prev => [...prev, {
            id: Date.now().toString(),
            userId: "1",
            userName: "You",
            content: newMessage,
            timestamp: new Date().toISOString(),
        }]);
        setNewMessage("");
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold">{collab.title}</h2>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                    {/* Tabs */}
                    <div className="flex gap-2 mt-4">
                        {(["overview", "assets", "chat"] as const).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 py-2 rounded-lg text-sm capitalize ${activeTab === tab ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                    }`}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {activeTab === "overview" && (
                        <div className="space-y-6">
                            {/* Collaborators */}
                            <div>
                                <h3 className="font-medium mb-3">Team ({collab.collaborators.length})</h3>
                                <div className="space-y-2">
                                    {collab.collaborators.map((c) => (
                                        <div key={c.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                                                    {c.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <p className="font-medium">{c.name}</p>
                                                    <p className="text-sm text-gray-500 capitalize">{c.role}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Invite */}
                            <button className="w-full py-3 bg-gray-800 rounded-xl hover:bg-gray-700 flex items-center justify-center gap-2">
                                <Plus className="w-4 h-4" />
                                Invite Collaborator
                            </button>
                        </div>
                    )}

                    {activeTab === "assets" && (
                        <div className="space-y-4">
                            {collab.assets.length === 0 ? (
                                <div className="text-center py-8">
                                    <FileText className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                                    <p className="text-gray-500">No assets uploaded yet</p>
                                </div>
                            ) : (
                                collab.assets.map((asset) => (
                                    <div key={asset.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-purple-400" />
                                            <div>
                                                <p className="font-medium">{asset.name}</p>
                                                <p className="text-sm text-gray-500">by {asset.uploadedBy}</p>
                                            </div>
                                        </div>
                                        <span className={`text-xs px-2 py-1 rounded-full ${asset.status === "approved" ? "text-green-400 bg-green-400/10" : "text-yellow-400 bg-yellow-400/10"
                                            }`}>
                                            {asset.status}
                                        </span>
                                    </div>
                                ))
                            )}
                            <button className="w-full py-3 bg-purple-600 rounded-xl hover:bg-purple-700 flex items-center justify-center gap-2">
                                <Plus className="w-4 h-4" />
                                Upload Asset
                            </button>
                        </div>
                    )}

                    {activeTab === "chat" && (
                        <div className="flex flex-col h-[400px]">
                            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                                {messages.map((msg) => (
                                    <div key={msg.id} className={`flex ${msg.userId === "1" ? "justify-end" : "justify-start"}`}>
                                        <div className={`max-w-[70%] p-3 rounded-lg ${msg.userId === "1" ? "bg-purple-600" : "bg-gray-800"
                                            }`}>
                                            {msg.userId !== "1" && <p className="text-xs text-gray-400 mb-1">{msg.userName}</p>}
                                            <p>{msg.content}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-2">
                                <input
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                                    placeholder="Type a message..."
                                    className="flex-1 px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                                />
                                <button onClick={sendMessage} className="p-3 bg-purple-600 rounded-xl hover:bg-purple-700">
                                    <Send className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function CreateCollabModal({ onClose, onCreate }: { onClose: () => void; onCreate: (c: Collaboration) => void }) {
    const [title, setTitle] = useState("");
    const [type, setType] = useState<Collaboration["type"]>("video");
    const [deadline, setDeadline] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            id: Date.now().toString(),
            title,
            type,
            status: "planning",
            collaborators: [{ id: "1", name: "You", role: "owner", joinedAt: new Date().toISOString() }],
            createdAt: new Date().toISOString(),
            deadline: deadline || undefined,
            assets: [],
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-6">New Collaboration</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Project Title *</label>
                        <input
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Type</label>
                        <select
                            value={type}
                            onChange={(e) => setType(e.target.value as Collaboration["type"])}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        >
                            <option value="video">Video</option>
                            <option value="podcast">Podcast</option>
                            <option value="article">Article</option>
                            <option value="campaign">Campaign</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Deadline</label>
                        <input
                            type="date"
                            value={deadline}
                            onChange={(e) => setDeadline(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>
                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button type="submit" disabled={!title} className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50">
                            Create
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
