/**
 * useTwins Hook
 * 
 * React hook for AI Twin Lab APIs:
 * - Twin creation and management
 * - Content generation (Script → Voice → Video)
 * - Training status and progress
 */

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface VoiceSettings {
    stability: number;
    similarity_boost: number;
    style: number;
    use_speaker_boost: boolean;
}

export interface AvatarSettings {
    background_type: string;
    background_color?: string;
    camera_angle?: string;
    emotion_default?: string;
}

export interface AITwin {
    id: string;
    name: string;
    description?: string;
    status: 'pending' | 'processing_voice' | 'processing_avatar' | 'ready' | 'failed';
    avatar_status: string;
    voice_status: string;
    avatar_preview_url?: string;
    voice_preview_url?: string;
    video_count: number;
    audio_count: number;
    total_minutes_generated: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface TwinContent {
    id: string;
    twin_id: string;
    asset_type: string;
    input_text?: string;
    output_url: string;
    thumbnail_url?: string;
    duration_seconds: number;
    status: string;
    created_at: string;
}

export interface TrainingJob {
    id: string;
    job_type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    estimated_completion?: string;
    result_url?: string;
    error_message?: string;
}

export function useTwins() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getAuthHeaders = useCallback(() => {
        const token = localStorage.getItem('token');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
        };
    }, []);

    // ============== Twin CRUD ==============

    const createTwin = useCallback(async (
        name: string,
        options?: {
            description?: string;
            personality_prompt?: string;
            communication_style?: string;
        }
    ): Promise<AITwin | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/twins`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    name,
                    description: options?.description,
                    personality_prompt: options?.personality_prompt,
                    communication_style: options?.communication_style ?? 'conversational',
                }),
            });

            if (!response.ok) throw new Error('Failed to create twin');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getTwins = useCallback(async (): Promise<AITwin[]> => {
        try {
            const response = await fetch(`${API_BASE}/twins`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) throw new Error('Failed to get twins');
            return await response.json();
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    const getTwin = useCallback(async (twinId: string): Promise<AITwin | null> => {
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) throw new Error('Failed to get twin');
            return await response.json();
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    const deleteTwin = useCallback(async (twinId: string): Promise<boolean> => {
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });
            return response.ok;
        } catch {
            return false;
        }
    }, [getAuthHeaders]);

    // ============== Media Upload ==============

    const addMedia = useCallback(async (
        twinId: string,
        media: {
            media_type: 'photo' | 'video' | 'audio';
            purpose: 'avatar_training' | 'voice_training';
            file_url: string;
            file_name: string;
            file_size_bytes: number;
            mime_type: string;
            duration_seconds?: number;
        }
    ): Promise<boolean> => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}/media`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(media),
            });
            return response.ok;
        } catch {
            return false;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    // ============== Training ==============

    const trainAvatar = useCallback(async (twinId: string): Promise<TrainingJob | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}/avatar/train`, {
                method: 'POST',
                headers: getAuthHeaders(),
            });

            if (!response.ok) throw new Error('Failed to start avatar training');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const trainVoice = useCallback(async (twinId: string): Promise<TrainingJob | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}/voice/train`, {
                method: 'POST',
                headers: getAuthHeaders(),
            });

            if (!response.ok) throw new Error('Failed to start voice training');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getTrainingJob = useCallback(async (jobId: string): Promise<TrainingJob | null> => {
        try {
            const response = await fetch(`${API_BASE}/twins/jobs/${jobId}`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) return null;
            return await response.json();
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    // ============== Content Generation ==============

    const generateVideo = useCallback(async (
        twinId: string,
        options: {
            text?: string;
            audio_url?: string;
            resolution?: '720p' | '1080p' | '4k';
            aspect_ratio?: '16:9' | '9:16' | '1:1';
        }
    ): Promise<TwinContent | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}/generate/video`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    text: options.text,
                    audio_url: options.audio_url,
                    resolution: options.resolution ?? '1080p',
                    aspect_ratio: options.aspect_ratio ?? '16:9',
                }),
            });

            if (!response.ok) throw new Error('Failed to generate video');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const synthesizeSpeech = useCallback(async (
        twinId: string,
        text: string,
        options?: {
            stability?: number;
            similarity_boost?: number;
        }
    ): Promise<TwinContent | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/twins/${twinId}/generate/speech`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    text,
                    stability: options?.stability ?? 0.5,
                    similarity_boost: options?.similarity_boost ?? 0.75,
                }),
            });

            if (!response.ok) throw new Error('Failed to synthesize speech');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getGeneratedAssets = useCallback(async (
        twinId: string,
        assetType?: 'video' | 'audio'
    ): Promise<TwinContent[]> => {
        try {
            const params = new URLSearchParams();
            if (assetType) params.append('asset_type', assetType);

            const response = await fetch(
                `${API_BASE}/twins/${twinId}/assets?${params}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) return [];
            return await response.json();
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    const getAssetStatus = useCallback(async (assetId: string): Promise<TwinContent | null> => {
        try {
            const response = await fetch(`${API_BASE}/twins/assets/${assetId}`, {
                headers: getAuthHeaders(),
            });

            if (!response.ok) return null;
            return await response.json();
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    return {
        loading,
        error,
        // Twin CRUD
        createTwin,
        getTwins,
        getTwin,
        deleteTwin,
        // Media
        addMedia,
        // Training
        trainAvatar,
        trainVoice,
        getTrainingJob,
        // Generation
        generateVideo,
        synthesizeSpeech,
        getGeneratedAssets,
        getAssetStatus,
    };
}
