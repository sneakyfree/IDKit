"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Users,
    Plus,
    MessageCircle,
    Send,
    UserPlus,
    Loader2,
    FolderOpen,
    Trash2,
} from "lucide-react";

/**
 * Co-Creation Workspace
 *
 * Project management, team collaboration, and messaging for content co-creation.
 * Closes Helix Scan gap L07.
 */

interface Project {
    id: string;
    name: string;
    description: string | null;
    project_type: string;
    created_at: string;
    members?: { user_id: string; role: string }[];
}

interface Message {
    id: string;
    content: string;
    sender_id: string;
    message_type: string;
    created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CoCreationPage() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [showInvite, setShowInvite] = useState(false);
    const [newMessage, setNewMessage] = useState("");
    const [projectName, setProjectName] = useState("");
    const [projectDesc, setProjectDesc] = useState("");
    const [inviteUserId, setInviteUserId] = useState("");

    const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` };

    const fetchProjects = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/co-creation/projects`, { headers });
            if (res.ok) {
                const data = await res.json();
                setProjects(data.projects || []);
            }
        } catch {
            // silent
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const fetchMessages = useCallback(async (projectId: string) => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/co-creation/projects/${projectId}/messages`, { headers });
            if (res.ok) {
                const data = await res.json();
                setMessages(data.messages || []);
            }
        } catch {
            // silent
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    useEffect(() => {
        if (selectedProject) {
            fetchMessages(selectedProject.id);
            const interval = setInterval(() => fetchMessages(selectedProject.id), 5000);
            return () => clearInterval(interval);
        }
    }, [selectedProject, fetchMessages]);

    const handleCreateProject = async () => {
        if (!projectName) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/co-creation/projects`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ name: projectName, description: projectDesc }),
            });
            if (res.ok) {
                setShowCreate(false);
                setProjectName("");
                setProjectDesc("");
                fetchProjects();
            }
        } catch {
            // silent
        }
    };

    const handleSendMessage = async () => {
        if (!newMessage || !selectedProject) return;
        try {
            await fetch(`${API_BASE}/api/v1/co-creation/projects/${selectedProject.id}/messages`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ content: newMessage }),
            });
            setNewMessage("");
            fetchMessages(selectedProject.id);
        } catch {
            // silent
        }
    };

    const handleInvite = async () => {
        if (!inviteUserId || !selectedProject) return;
        try {
            await fetch(`${API_BASE}/api/v1/co-creation/projects/${selectedProject.id}/invite`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: inviteUserId }),
            });
            setShowInvite(false);
            setInviteUserId("");
        } catch {
            // silent
        }
    };

    const handleDelete = async (projectId: string) => {
        try {
            await fetch(`${API_BASE}/api/v1/co-creation/projects/${projectId}`, {
                method: "DELETE",
                headers,
            });
            if (selectedProject?.id === projectId) setSelectedProject(null);
            fetchProjects();
        } catch {
            // silent
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-950">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-white flex">
            {/* Sidebar — Project List */}
            <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
                <div className="p-4 border-b border-gray-800">
                    <div className="flex items-center justify-between mb-2">
                        <h2 className="font-bold text-lg">Co-Creation</h2>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="p-2 bg-purple-600 rounded-lg hover:bg-purple-500"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="text-xs text-gray-500">{projects.length} projects</p>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {projects.map((p) => (
                        <button
                            key={p.id}
                            onClick={() => setSelectedProject(p)}
                            className={`w-full text-left p-4 border-b border-gray-800/50 hover:bg-gray-800/50 transition-colors ${selectedProject?.id === p.id ? "bg-gray-800" : ""
                                }`}
                        >
                            <div className="flex items-center justify-between">
                                <p className="font-medium text-sm truncate">{p.name}</p>
                                <button
                                    onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }}
                                    className="p-1 hover:bg-gray-700 rounded opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 className="w-3 h-3 text-gray-500" />
                                </button>
                            </div>
                            {p.description && (
                                <p className="text-xs text-gray-500 mt-0.5 truncate">{p.description}</p>
                            )}
                        </button>
                    ))}
                    {projects.length === 0 && (
                        <div className="p-8 text-center text-gray-600 text-sm">
                            <FolderOpen className="w-8 h-8 mx-auto mb-2 opacity-30" />
                            No projects yet
                        </div>
                    )}
                </div>
            </div>

            {/* Main Area — Messages */}
            <div className="flex-1 flex flex-col">
                {selectedProject ? (
                    <>
                        {/* Header */}
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                            <div>
                                <h3 className="font-bold">{selectedProject.name}</h3>
                                <p className="text-xs text-gray-500">{selectedProject.description}</p>
                            </div>
                            <button
                                onClick={() => setShowInvite(true)}
                                className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 text-sm"
                            >
                                <UserPlus className="w-4 h-4" /> Invite
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {messages.map((m) => (
                                <div key={m.id} className="flex gap-3">
                                    <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center text-xs text-purple-400">
                                        {m.sender_id.slice(0, 2).toUpperCase()}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-medium">{m.sender_id.slice(0, 8)}</span>
                                            <span className="text-xs text-gray-600">{new Date(m.created_at).toLocaleTimeString()}</span>
                                        </div>
                                        <p className="text-sm text-gray-300 mt-0.5">{m.content}</p>
                                    </div>
                                </div>
                            ))}
                            {messages.length === 0 && (
                                <div className="text-center py-16 text-gray-600">
                                    <MessageCircle className="w-10 h-10 mx-auto mb-2 opacity-30" />
                                    <p className="text-sm">No messages yet. Start the conversation!</p>
                                </div>
                            )}
                        </div>

                        {/* Message Input */}
                        <div className="p-4 border-t border-gray-800">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                                    placeholder="Type a message..."
                                    className="flex-1 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                                />
                                <button
                                    onClick={handleSendMessage}
                                    disabled={!newMessage}
                                    className="px-4 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-600">
                        <div className="text-center">
                            <Users className="w-16 h-16 mx-auto mb-4 opacity-20" />
                            <p className="text-lg font-medium">Select a project</p>
                            <p className="text-sm">or create a new co-creation workspace</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Create Project Modal */}
            {showCreate && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">New Project</h2>
                        <div className="space-y-4">
                            <input
                                type="text"
                                value={projectName}
                                onChange={(e) => setProjectName(e.target.value)}
                                placeholder="Project name"
                                className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                            />
                            <textarea
                                value={projectDesc}
                                onChange={(e) => setProjectDesc(e.target.value)}
                                placeholder="Description (optional)"
                                rows={3}
                                className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none resize-none"
                            />
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">Cancel</button>
                            <button onClick={handleCreateProject} disabled={!projectName} className="flex-1 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50">Create</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Invite Modal */}
            {showInvite && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Invite Member</h2>
                        <input
                            type="text"
                            value={inviteUserId}
                            onChange={(e) => setInviteUserId(e.target.value)}
                            placeholder="User ID or email"
                            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                        />
                        <div className="flex gap-3 mt-6">
                            <button onClick={() => setShowInvite(false)} className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">Cancel</button>
                            <button onClick={handleInvite} disabled={!inviteUserId} className="flex-1 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50">Invite</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
