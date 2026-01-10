/**
 * API Client
 *
 * Axios-based API client for the IDKit backend.
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';

// API base URL - use environment variable or default
const API_BASE_URL =
  Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearAuthToken();
          // The auth context will handle the redirect
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = null;
  }

  // Generic request methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // =========================================================================
  // Feed Endpoints
  // =========================================================================

  async getFeed(page: number = 1, pageSize: number = 20) {
    return this.get<{ posts: any[]; has_more: boolean }>('/feed', {
      params: { page, page_size: pageSize },
    });
  }

  async getFollowingFeed(page: number = 1, pageSize: number = 20) {
    return this.get<{ posts: any[]; has_more: boolean }>('/feed/following', {
      params: { page, page_size: pageSize },
    });
  }

  // =========================================================================
  // Posts Endpoints
  // =========================================================================

  async createPost(data: {
    content_text?: string;
    media_urls?: string[];
    post_type: string;
    visibility?: string;
  }) {
    return this.post('/posts', data);
  }

  async getPost(postId: string) {
    return this.get(`/posts/${postId}`);
  }

  async likePost(postId: string) {
    return this.post(`/posts/${postId}/like`);
  }

  async unlikePost(postId: string) {
    return this.delete(`/posts/${postId}/like`);
  }

  async savePost(postId: string) {
    return this.post(`/posts/${postId}/save`);
  }

  async getComments(postId: string, page: number = 1) {
    return this.get(`/posts/${postId}/comments`, {
      params: { page },
    });
  }

  async addComment(postId: string, content: string) {
    return this.post(`/posts/${postId}/comments`, { content });
  }

  // =========================================================================
  // Profile Endpoints
  // =========================================================================

  async getProfile(username: string) {
    return this.get(`/profiles/${username}`);
  }

  async updateProfile(data: {
    display_name?: string;
    bio?: string;
    avatar_url?: string;
    website_url?: string;
  }) {
    return this.patch('/profiles/me', data);
  }

  async followUser(username: string) {
    return this.post(`/profiles/${username}/follow`);
  }

  async unfollowUser(username: string) {
    return this.delete(`/profiles/${username}/follow`);
  }

  // =========================================================================
  // Trends Endpoints
  // =========================================================================

  async getTrends(platforms?: string[], limit: number = 20) {
    return this.get('/trends', {
      params: { platforms, limit },
    });
  }

  async getTrendAlerts() {
    return this.get('/trends/alerts');
  }

  // =========================================================================
  // Inbox Endpoints
  // =========================================================================

  async getInbox(params?: {
    message_type?: string;
    status?: string;
    page?: number;
  }) {
    return this.get('/inbox/messages', { params });
  }

  async getConversations(page: number = 1) {
    return this.get('/inbox/conversations', {
      params: { page },
    });
  }

  async getInboxStats() {
    return this.get('/inbox/stats');
  }

  // =========================================================================
  // Analytics Endpoints
  // =========================================================================

  async getAnalyticsOverview(params?: {
    start_date?: string;
    end_date?: string;
    platforms?: string[];
  }) {
    return this.get('/analytics/overview', { params });
  }

  async getAnalyticsTrends(periodDays: number = 30) {
    return this.get('/analytics/trends', {
      params: { period_days: periodDays },
    });
  }

  // =========================================================================
  // Content Endpoints
  // =========================================================================

  async generateContent(data: {
    content_type: string;
    topic: string;
    tone?: string;
    platforms?: string[];
  }) {
    return this.post('/content/generate', data);
  }

  async repurposeContent(contentId: string, targetFormats: string[]) {
    return this.post('/repurpose/all', {
      content_id: contentId,
      target_formats: targetFormats,
    });
  }

  // =========================================================================
  // Podcast Endpoints
  // =========================================================================

  async createPodcast(data: {
    title: string;
    description?: string;
    category?: string;
  }) {
    return this.post('/podcasts', data);
  }

  async generateEpisode(podcastId: string, data: {
    topic: string;
    style?: string;
    duration_target?: number;
  }) {
    return this.post(`/podcasts/${podcastId}/episodes/generate`, data);
  }

  // =========================================================================
  // AI Twin Endpoints
  // =========================================================================

  async getAITwins() {
    return this.get('/twins');
  }

  async createAITwin(data: {
    name: string;
    personality_traits?: string[];
  }) {
    return this.post('/twins', data);
  }

  async generateVideo(twinId: string, data: {
    script: string;
    style?: string;
  }) {
    return this.post(`/twins/${twinId}/generate/video`, data);
  }

  // =========================================================================
  // Media Endpoints
  // =========================================================================

  async getUploadUrl(data: {
    filename: string;
    content_type: string;
    file_size: number;
  }) {
    return this.post<{ upload_url: string; file_key: string }>('/media/upload-url', data);
  }

  async confirmUpload(fileKey: string) {
    return this.post('/media/confirm', { file_key: fileKey });
  }
}

export const api = new ApiClient();
