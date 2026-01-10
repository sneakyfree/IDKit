/**
 * API Client for IDKit Backend
 *
 * Provides typed methods for interacting with the Python/FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  // Get token from localStorage
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ==================== Auth ====================

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  is_verified: boolean;
  subscription_tier: string;
}

export interface ProfileResponse {
  id: string;
  user_id: string;
  username: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  cover_image_url: string | null;
  website_url: string | null;
  follower_count: number;
  following_count: number;
  post_count: number;
  is_verified: boolean;
  niche_tags: string[];
  is_following: boolean;
}

export interface MeResponse {
  user: UserResponse;
  profile: ProfileResponse | null;
}

export const auth = {
  getGoogleLoginUrl: () => `${API_BASE}/api/v1/auth/google`,

  getMe: () => apiRequest<MeResponse>("/api/v1/auth/me"),

  refresh: (refreshToken: string) =>
    apiRequest<TokenResponse>("/api/v1/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    }),

  logout: () => apiRequest("/api/v1/auth/logout", { method: "POST" }),
};

// ==================== Feed ====================

export interface FeedPostResponse {
  id: string;
  user_id: string;
  post_type: string;
  content_text: string | null;
  media_urls: string[];
  thumbnail_url: string | null;
  view_count: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  save_count: number;
  hashtags: string[];
  ai_generated: boolean;
  visibility: string;
  created_at: string;
  author: {
    username: string;
    display_name: string;
    avatar_url: string | null;
    is_verified: boolean;
  };
  is_liked: boolean;
  is_saved: boolean;
}

export interface FeedResponse {
  posts: FeedPostResponse[];
  next_cursor: string | null;
}

export const feed = {
  getPersonalized: (cursor?: string, pageSize = 20) =>
    apiRequest<FeedResponse>(
      `/api/v1/feed?page_size=${pageSize}${cursor ? `&cursor=${cursor}` : ""}`
    ),

  getFollowing: (page = 1, pageSize = 20) =>
    apiRequest<FeedResponse>(
      `/api/v1/feed/following?page=${page}&page_size=${pageSize}`
    ),

  getTrending: (page = 1, pageSize = 20) =>
    apiRequest<FeedResponse>(
      `/api/v1/feed/trending?page=${page}&page_size=${pageSize}`
    ),
};

// ==================== Posts ====================

export interface CreatePostRequest {
  post_type: string;
  content_text?: string;
  media_urls?: string[];
  thumbnail_url?: string;
  hashtags?: string[];
  mentions?: string[];
  visibility?: string;
  ai_generated?: boolean;
}

export interface CommentResponse {
  id: string;
  user_id: string;
  content: string;
  like_count: number;
  parent_comment_id: string | null;
  created_at: string;
}

export const posts = {
  create: (data: CreatePostRequest) =>
    apiRequest<FeedPostResponse>("/api/v1/posts", {
      method: "POST",
      body: data,
    }),

  get: (postId: string) =>
    apiRequest<FeedPostResponse>(`/api/v1/posts/${postId}`),

  delete: (postId: string) =>
    apiRequest(`/api/v1/posts/${postId}`, { method: "DELETE" }),

  like: (postId: string) =>
    apiRequest<{ success: boolean; like_count: number }>(
      `/api/v1/posts/${postId}/like`,
      { method: "POST" }
    ),

  unlike: (postId: string) =>
    apiRequest<{ success: boolean; like_count: number }>(
      `/api/v1/posts/${postId}/like`,
      { method: "DELETE" }
    ),

  save: (postId: string, collection = "Saved") =>
    apiRequest<{ success: boolean; save_count: number }>(
      `/api/v1/posts/${postId}/save?collection=${collection}`,
      { method: "POST" }
    ),

  unsave: (postId: string, collection = "Saved") =>
    apiRequest<{ success: boolean; save_count: number }>(
      `/api/v1/posts/${postId}/save?collection=${collection}`,
      { method: "DELETE" }
    ),

  getComments: (postId: string, page = 1, pageSize = 20) =>
    apiRequest<CommentResponse[]>(
      `/api/v1/posts/${postId}/comments?page=${page}&page_size=${pageSize}`
    ),

  addComment: (postId: string, content: string, parentId?: string) =>
    apiRequest<CommentResponse>(`/api/v1/posts/${postId}/comments`, {
      method: "POST",
      body: { content, parent_comment_id: parentId },
    }),
};

// ==================== Profiles ====================

export interface ProfileListResponse {
  profiles: ProfileResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface PostPreviewResponse {
  id: string;
  post_type: string;
  thumbnail_url: string | null;
  media_urls: string[];
  like_count: number;
  comment_count: number;
  created_at: string;
}

export const profiles = {
  getMe: () => apiRequest<ProfileResponse>("/api/v1/profiles/me"),

  updateMe: (data: Partial<ProfileResponse>) =>
    apiRequest<ProfileResponse>("/api/v1/profiles/me", {
      method: "PUT",
      body: data,
    }),

  get: (username: string) =>
    apiRequest<ProfileResponse>(`/api/v1/profiles/${username}`),

  getPosts: (username: string, page = 1, pageSize = 20) =>
    apiRequest<PostPreviewResponse[]>(
      `/api/v1/profiles/${username}/posts?page=${page}&page_size=${pageSize}`
    ),

  follow: (username: string) =>
    apiRequest<{ success: boolean; follower_count: number; is_following: boolean }>(
      `/api/v1/profiles/${username}/follow`,
      { method: "POST" }
    ),

  unfollow: (username: string) =>
    apiRequest<{ success: boolean; follower_count: number; is_following: boolean }>(
      `/api/v1/profiles/${username}/follow`,
      { method: "DELETE" }
    ),

  getFollowers: (username: string, page = 1, pageSize = 20) =>
    apiRequest<ProfileListResponse>(
      `/api/v1/profiles/${username}/followers?page=${page}&page_size=${pageSize}`
    ),

  getFollowing: (username: string, page = 1, pageSize = 20) =>
    apiRequest<ProfileListResponse>(
      `/api/v1/profiles/${username}/following?page=${page}&page_size=${pageSize}`
    ),
};

// ==================== Schedule ====================

export interface ScheduledItemResponse {
  id: string;
  content_id: string;
  title: string;
  content_type: string;
  platform: string;
  scheduled_at: string;
  status: string;
  thumbnail_url: string | null;
  created_at: string;
}

export interface ScheduleContentRequest {
  content_id: string;
  platform: string;
  scheduled_at: string;
  timezone?: string;
}

export const schedule = {
  getItems: (status?: string, page = 1, pageSize = 50) =>
    apiRequest<ScheduledItemResponse[]>(
      `/api/v1/social/posts?status_filter=${status || "scheduled"}&page=${page}&page_size=${pageSize}`
    ),

  scheduleContent: (data: ScheduleContentRequest) =>
    apiRequest<ScheduledItemResponse>("/api/v1/social/posts/publish", {
      method: "POST",
      body: {
        account_id: data.content_id,
        content_type: "post",
        text: "",
        scheduled_at: data.scheduled_at,
      },
    }),

  reschedule: (itemId: string, newDate: string) =>
    apiRequest<ScheduledItemResponse>(`/api/v1/social/posts/${itemId}/reschedule`, {
      method: "PUT",
      body: { scheduled_at: newDate },
    }),

  cancel: (itemId: string) =>
    apiRequest(`/api/v1/social/posts/${itemId}`, { method: "DELETE" }),
};

// ==================== Privacy & GDPR ====================

export interface PrivacySettingsResponse {
  profile_visibility: string;
  activity_visibility: string;
  search_visibility: boolean;
  analytics_enabled: boolean;
  personalization_enabled: boolean;
  marketing_emails: boolean;
  product_updates: boolean;
  third_party_sharing: boolean;
}

export interface DataRequestResponse {
  id: string;
  request_type: string;
  status: string;
  categories: string[];
  created_at: string;
  completed_at: string | null;
  download_url: string | null;
  expires_at: string | null;
}

export interface DataCategoryResponse {
  id: string;
  name: string;
  description: string;
}

export interface GDPRRightResponse {
  article: string;
  name: string;
  description: string;
  endpoint: string;
}

export const privacy = {
  getSettings: () =>
    apiRequest<PrivacySettingsResponse>("/api/v1/privacy/settings"),

  updateSettings: (data: Partial<PrivacySettingsResponse>) =>
    apiRequest<PrivacySettingsResponse>("/api/v1/privacy/settings", {
      method: "PUT",
      body: data,
    }),

  updateConsent: (consentType: string, granted: boolean) =>
    apiRequest<{ id: string; consent_type: string; granted: boolean; recorded_at: string }>(
      "/api/v1/privacy/consent",
      {
        method: "POST",
        body: { consent_type: consentType, granted },
      }
    ),

  getDataCategories: () =>
    apiRequest<{ categories: DataCategoryResponse[] }>("/api/v1/privacy/data-categories"),

  getGDPRRights: () =>
    apiRequest<{ rights: GDPRRightResponse[]; contact: { email: string; dpo: string }; response_time: string }>(
      "/api/v1/privacy/rights"
    ),

  createDataRequest: (requestType: string, categories?: string[]) =>
    apiRequest<DataRequestResponse>("/api/v1/privacy/data-requests", {
      method: "POST",
      body: { request_type: requestType, categories },
    }),

  listDataRequests: (status?: string) =>
    apiRequest<DataRequestResponse[]>(
      `/api/v1/privacy/data-requests${status ? `?status=${status}` : ""}`
    ),

  downloadExport: (categories?: string[]) =>
    `${API_BASE}/api/v1/privacy/export${categories?.length ? `?categories=${categories.join(",")}` : ""}`,

  deleteData: (categories?: string[]) =>
    apiRequest<{ deleted_at: string; categories_deleted: string[]; items_deleted: Record<string, number> }>(
      `/api/v1/privacy/data?confirm=true${categories?.length ? `&categories=${categories.join(",")}` : ""}`,
      { method: "DELETE" }
    ),

  deleteAccount: () =>
    apiRequest("/api/v1/privacy/account?confirm=true", { method: "DELETE" }),
};

// ==================== A/B Testing ====================

export interface ABTestVariant {
  id: string;
  name: string;
  content: Record<string, unknown>;
  weight: number;
  impressions: number;
  engagements: number;
  engagement_rate: number;
}

export interface ABTestResponse {
  id: string;
  name: string;
  description: string | null;
  test_type: string;
  status: string;
  variants: ABTestVariant[];
  winner_criteria: string;
  winner_variant_id: string | null;
  statistical_significance: number | null;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
}

export interface CreateABTestRequest {
  name: string;
  description?: string;
  test_type: string;
  variants: { name: string; content: Record<string, unknown>; weight?: number }[];
  winner_criteria?: string;
  min_sample_size?: number;
  confidence_level?: number;
}

export const testing = {
  create: (data: CreateABTestRequest) =>
    apiRequest<ABTestResponse>("/api/v1/testing", {
      method: "POST",
      body: data,
    }),

  list: (status?: string, testType?: string, limit = 20, offset = 0) =>
    apiRequest<ABTestResponse[]>(
      `/api/v1/testing?limit=${limit}&offset=${offset}${status ? `&status=${status}` : ""}${testType ? `&test_type=${testType}` : ""}`
    ),

  get: (testId: string) =>
    apiRequest<ABTestResponse>(`/api/v1/testing/${testId}`),

  start: (testId: string) =>
    apiRequest<ABTestResponse>(`/api/v1/testing/${testId}/start`, { method: "POST" }),

  end: (testId: string) =>
    apiRequest<ABTestResponse>(`/api/v1/testing/${testId}/end`, { method: "POST" }),

  analyze: (testId: string) =>
    apiRequest<{
      test_id: string;
      winner: ABTestVariant | null;
      statistical_significance: number;
      is_significant: boolean;
      recommendation: string;
    }>(`/api/v1/testing/${testId}/analyze`),

  delete: (testId: string) =>
    apiRequest(`/api/v1/testing/${testId}`, { method: "DELETE" }),
};

// ==================== Approvals ====================

export interface ApprovalWorkflowConfig {
  is_enabled: boolean;
  require_approval_for: string[];
  approvers: string[];
  auto_approve_for_roles: string[];
  notification_settings: Record<string, unknown>;
}

export interface ContentApprovalResponse {
  id: string;
  content_id: string;
  status: string;
  requested_by: string;
  reviewed_by: string | null;
  notes: string | null;
  review_notes: string | null;
  requested_at: string;
  reviewed_at: string | null;
}

export const approvals = {
  getWorkflowConfig: (orgId: string) =>
    apiRequest<ApprovalWorkflowConfig>(`/api/v1/enterprise/organizations/${orgId}/approval-workflow`),

  updateWorkflowConfig: (orgId: string, config: ApprovalWorkflowConfig) =>
    apiRequest<ApprovalWorkflowConfig>(`/api/v1/enterprise/organizations/${orgId}/approval-workflow`, {
      method: "PUT",
      body: config,
    }),

  submitForApproval: (contentId: string, notes?: string) =>
    apiRequest<ContentApprovalResponse>(`/api/v1/enterprise/content/${contentId}/submit-for-approval`, {
      method: "POST",
      body: { content_id: contentId, notes },
    }),

  approve: (contentId: string, notes?: string) =>
    apiRequest<ContentApprovalResponse>(`/api/v1/enterprise/content/${contentId}/approve`, {
      method: "POST",
      body: { notes },
    }),

  reject: (contentId: string, reason: string) =>
    apiRequest<ContentApprovalResponse>(`/api/v1/enterprise/content/${contentId}/reject`, {
      method: "POST",
      body: { reason },
    }),

  getPendingApprovals: (orgId: string) =>
    apiRequest<ContentApprovalResponse[]>(`/api/v1/enterprise/organizations/${orgId}/pending-approvals`),
};

export { ApiError };
