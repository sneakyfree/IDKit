'use client';

/**
 * AI Twin Lab Component
 * 
 * Interface for managing AI Twins:
 * - Create new twins
 * - Upload training media
 * - Generate video/audio content
 * - Track training progress
 */

import React, { useEffect, useState } from 'react';
import { useTwins, AITwin, TrainingJob } from '@/hooks/useTwins';

export function TwinLab() {
    const {
        getTwins,
        createTwin,
        trainAvatar,
        trainVoice,
        generateVideo,
        synthesizeSpeech,
        loading,
        error
    } = useTwins();

    const [twins, setTwins] = useState<AITwin[]>([]);
    const [selectedTwin, setSelectedTwin] = useState<AITwin | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newTwinName, setNewTwinName] = useState('');
    const [generateText, setGenerateText] = useState('');
    const [generatingType, setGeneratingType] = useState<'video' | 'audio' | null>(null);

    useEffect(() => {
        loadTwins();
    }, []);

    async function loadTwins() {
        const data = await getTwins();
        setTwins(data);
        if (data.length > 0 && !selectedTwin) {
            setSelectedTwin(data[0]);
        }
    }

    async function handleCreateTwin() {
        if (!newTwinName.trim()) return;

        const twin = await createTwin(newTwinName, {
            description: 'My AI Twin',
            communication_style: 'conversational',
        });

        if (twin) {
            setTwins([twin, ...twins]);
            setSelectedTwin(twin);
            setShowCreateModal(false);
            setNewTwinName('');
        }
    }

    async function handleStartTraining(type: 'avatar' | 'voice') {
        if (!selectedTwin) return;

        if (type === 'avatar') {
            await trainAvatar(selectedTwin.id);
        } else {
            await trainVoice(selectedTwin.id);
        }

        loadTwins();
    }

    async function handleGenerate() {
        if (!selectedTwin || !generateText.trim()) return;

        if (generatingType === 'video') {
            await generateVideo(selectedTwin.id, { text: generateText });
        } else {
            await synthesizeSpeech(selectedTwin.id, generateText);
        }

        setGenerateText('');
        setGeneratingType(null);
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ready': return '#10B981';
            case 'processing_voice':
            case 'processing_avatar': return '#F59E0B';
            case 'failed': return '#EF4444';
            default: return '#6B7280';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'ready': return 'Ready';
            case 'pending': return 'Pending Setup';
            case 'processing_voice': return 'Training Voice...';
            case 'processing_avatar': return 'Training Avatar...';
            case 'failed': return 'Failed';
            default: return status;
        }
    };

    return (
        <div className="twin-lab">
            {/* Header */}
            <header className="lab-header">
                <h1>🧬 AI Twin Lab</h1>
                <p>Create your digital clone in minutes</p>
                <button
                    className="create-btn"
                    onClick={() => setShowCreateModal(true)}
                >
                    + Create New Twin
                </button>
            </header>

            <div className="lab-content">
                {/* Twin Selector */}
                <aside className="twin-sidebar">
                    <h3>Your Twins</h3>
                    {twins.length === 0 ? (
                        <p className="empty">No twins yet. Create your first one!</p>
                    ) : (
                        <ul className="twin-list">
                            {twins.map((twin) => (
                                <li
                                    key={twin.id}
                                    className={selectedTwin?.id === twin.id ? 'active' : ''}
                                    onClick={() => setSelectedTwin(twin)}
                                >
                                    <div className="twin-preview">
                                        {twin.avatar_preview_url ? (
                                            <img src={twin.avatar_preview_url} alt={twin.name} />
                                        ) : (
                                            <div className="placeholder-avatar">👤</div>
                                        )}
                                    </div>
                                    <div className="twin-info">
                                        <span className="name">{twin.name}</span>
                                        <span
                                            className="status"
                                            style={{ color: getStatusColor(twin.status) }}
                                        >
                                            {getStatusLabel(twin.status)}
                                        </span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </aside>

                {/* Main Panel */}
                <main className="twin-main">
                    {selectedTwin ? (
                        <>
                            {/* Twin Header */}
                            <div className="twin-header">
                                <div className="avatar-large">
                                    {selectedTwin.avatar_preview_url ? (
                                        <img src={selectedTwin.avatar_preview_url} alt={selectedTwin.name} />
                                    ) : (
                                        <div className="placeholder-avatar">👤</div>
                                    )}
                                </div>
                                <div className="twin-details">
                                    <h2>{selectedTwin.name}</h2>
                                    <span
                                        className="status-badge"
                                        style={{ backgroundColor: getStatusColor(selectedTwin.status) }}
                                    >
                                        {getStatusLabel(selectedTwin.status)}
                                    </span>
                                    <div className="stats">
                                        <span>🎬 {selectedTwin.video_count} videos</span>
                                        <span>🎤 {selectedTwin.audio_count} audio</span>
                                        <span>⏱️ {selectedTwin.total_minutes_generated.toFixed(1)} min</span>
                                    </div>
                                </div>
                            </div>

                            {/* Training Section */}
                            {selectedTwin.status === 'pending' && (
                                <section className="training-section">
                                    <h3>🎓 Training Required</h3>
                                    <p>Upload a 5-minute video to train your AI Twin</p>

                                    <div className="training-cards">
                                        <div className="training-card">
                                            <span className="icon">📹</span>
                                            <h4>Avatar Training</h4>
                                            <p>Upload video to create your visual avatar</p>
                                            <button
                                                onClick={() => handleStartTraining('avatar')}
                                                disabled={loading}
                                            >
                                                Start Avatar Training
                                            </button>
                                        </div>
                                        <div className="training-card">
                                            <span className="icon">🎤</span>
                                            <h4>Voice Cloning</h4>
                                            <p>Clone your voice for speech synthesis</p>
                                            <button
                                                onClick={() => handleStartTraining('voice')}
                                                disabled={loading}
                                            >
                                                Start Voice Clone
                                            </button>
                                        </div>
                                    </div>
                                </section>
                            )}

                            {/* Generation Section */}
                            {selectedTwin.status === 'ready' && (
                                <section className="generate-section">
                                    <h3>✨ Generate Content</h3>

                                    <div className="generate-tabs">
                                        <button
                                            className={generatingType === 'video' ? 'active' : ''}
                                            onClick={() => setGeneratingType('video')}
                                        >
                                            🎬 Video
                                        </button>
                                        <button
                                            className={generatingType === 'audio' ? 'active' : ''}
                                            onClick={() => setGeneratingType('audio')}
                                        >
                                            🎤 Audio
                                        </button>
                                    </div>

                                    {generatingType && (
                                        <div className="generate-form">
                                            <textarea
                                                placeholder={`Enter the script for your ${generatingType}...`}
                                                value={generateText}
                                                onChange={(e) => setGenerateText(e.target.value)}
                                                rows={4}
                                            />
                                            <button
                                                className="generate-btn"
                                                onClick={handleGenerate}
                                                disabled={loading || !generateText.trim()}
                                            >
                                                {loading ? 'Generating...' : `Generate ${generatingType === 'video' ? 'Video' : 'Audio'}`}
                                            </button>
                                        </div>
                                    )}
                                </section>
                            )}
                        </>
                    ) : (
                        <div className="no-selection">
                            <p>Select a twin or create a new one to get started</p>
                        </div>
                    )}
                </main>
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <h2>Create AI Twin</h2>
                        <input
                            type="text"
                            placeholder="Twin name..."
                            value={newTwinName}
                            onChange={(e) => setNewTwinName(e.target.value)}
                            autoFocus
                        />
                        <div className="modal-actions">
                            <button className="cancel" onClick={() => setShowCreateModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="confirm"
                                onClick={handleCreateTwin}
                                disabled={!newTwinName.trim() || loading}
                            >
                                {loading ? 'Creating...' : 'Create Twin'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {error && (
                <div className="error-toast">
                    {error}
                </div>
            )}

            <style jsx>{`
        .twin-lab {
          min-height: 100vh;
          background: #0D0D0D;
          color: white;
        }

        .lab-header {
          padding: 32px;
          text-align: center;
          border-bottom: 1px solid #333;
        }

        .lab-header h1 {
          font-size: 36px;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .lab-header p {
          color: #888;
          margin-bottom: 24px;
        }

        .create-btn {
          background: linear-gradient(135deg, #8B5CF6, #EC4899);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .create-btn:hover {
          transform: scale(1.05);
        }

        .lab-content {
          display: grid;
          grid-template-columns: 280px 1fr;
          min-height: calc(100vh - 150px);
        }

        .twin-sidebar {
          background: #1A1A2E;
          padding: 24px;
          border-right: 1px solid #333;
        }

        .twin-sidebar h3 {
          font-size: 14px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 16px;
        }

        .twin-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .twin-list li {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 12px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .twin-list li:hover,
        .twin-list li.active {
          background: #16213E;
        }

        .twin-preview {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          overflow: hidden;
          background: #333;
        }

        .twin-preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .placeholder-avatar {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          background: linear-gradient(135deg, #1A1A2E, #16213E);
        }

        .twin-info .name {
          display: block;
          font-weight: 600;
        }

        .twin-info .status {
          font-size: 12px;
        }

        .twin-main {
          padding: 32px;
        }

        .twin-header {
          display: flex;
          gap: 24px;
          margin-bottom: 32px;
        }

        .avatar-large {
          width: 120px;
          height: 120px;
          border-radius: 24px;
          overflow: hidden;
          background: #333;
        }

        .avatar-large .placeholder-avatar {
          font-size: 48px;
        }

        .twin-details h2 {
          font-size: 28px;
          margin-bottom: 8px;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        .stats {
          display: flex;
          gap: 24px;
          color: #888;
        }

        .training-section,
        .generate-section {
          background: #1A1A2E;
          border-radius: 16px;
          padding: 24px;
        }

        .training-section h3,
        .generate-section h3 {
          margin-bottom: 8px;
        }

        .training-cards {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-top: 24px;
        }

        .training-card {
          background: #16213E;
          border: 1px solid #333;
          border-radius: 12px;
          padding: 24px;
          text-align: center;
        }

        .training-card .icon {
          font-size: 36px;
          display: block;
          margin-bottom: 12px;
        }

        .training-card h4 {
          margin-bottom: 8px;
        }

        .training-card p {
          color: #888;
          font-size: 14px;
          margin-bottom: 16px;
        }

        .training-card button {
          background: #8B5CF6;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          cursor: pointer;
        }

        .generate-tabs {
          display: flex;
          gap: 8px;
          margin: 16px 0;
        }

        .generate-tabs button {
          padding: 10px 20px;
          background: #16213E;
          border: 1px solid #333;
          border-radius: 8px;
          color: #888;
          cursor: pointer;
        }

        .generate-tabs button.active {
          background: #8B5CF6;
          color: white;
          border-color: #8B5CF6;
        }

        .generate-form textarea {
          width: 100%;
          background: #16213E;
          border: 1px solid #333;
          border-radius: 12px;
          padding: 16px;
          color: white;
          font-size: 16px;
          resize: vertical;
        }

        .generate-btn {
          margin-top: 16px;
          background: linear-gradient(135deg, #8B5CF6, #EC4899);
          color: white;
          border: none;
          padding: 14px 28px;
          border-radius: 12px;
          font-weight: 600;
          cursor: pointer;
        }

        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: #1A1A2E;
          border-radius: 16px;
          padding: 32px;
          width: 400px;
        }

        .modal h2 {
          margin-bottom: 20px;
        }

        .modal input {
          width: 100%;
          padding: 14px;
          background: #16213E;
          border: 1px solid #333;
          border-radius: 8px;
          color: white;
          font-size: 16px;
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 24px;
        }

        .modal-actions button {
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        .modal-actions .cancel {
          background: transparent;
          border: 1px solid #333;
          color: #888;
        }

        .modal-actions .confirm {
          background: #8B5CF6;
          border: none;
          color: white;
        }

        .error-toast {
          position: fixed;
          bottom: 24px;
          right: 24px;
          background: #EF4444;
          color: white;
          padding: 16px 24px;
          border-radius: 12px;
        }

        .empty {
          color: #666;
          font-size: 14px;
        }

        .no-selection {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 300px;
          color: #666;
        }
      `}</style>
        </div>
    );
}

export default TwinLab;
