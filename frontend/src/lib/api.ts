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

// ==================== Payouts ====================

export interface ConnectAccountResponse {
  id: string;
  stripe_account_id: string;
  status: "pending" | "active" | "restricted" | "disabled";
  details_submitted: boolean;
  charges_enabled: boolean;
  payouts_enabled: boolean;
  country: string;
  default_currency: string;
  requirements?: {
    currently_due: string[];
    eventually_due: string[];
    pending_verification: string[];
  };
  created_at: string;
}

export interface OnboardingLinkResponse {
  url: string;
  expires_at?: string;
}

export interface BalanceAmount {
  amount_cents: number;
  currency: string;
}

export interface BalanceResponse {
  available: BalanceAmount[];
  pending: BalanceAmount[];
  total_available_cents: number;
  total_pending_cents: number;
}

export interface TransferHistoryResponse {
  id: string;
  stripe_transfer_id: string;
  amount_cents: number;
  currency: string;
  status: string;
  description?: string;
  source_type?: string;
  created_at: string;
  completed_at?: string;
}

export interface PayoutHistoryResponse {
  id: string;
  stripe_payout_id: string;
  amount_cents: number;
  currency: string;
  status: string;
  arrival_date?: string;
  failure_message?: string;
  created_at: string;
}

export interface PayoutListResponse {
  transfers: TransferHistoryResponse[];
  payouts: PayoutHistoryResponse[];
  total_transferred_cents: number;
  total_paid_out_cents: number;
}

export interface InitiatePayoutResponse {
  payout_id: string;
  amount_cents: number;
  currency: string;
  status: string;
  estimated_arrival?: string;
}

export const payouts = {
  startOnboarding: () =>
    apiRequest<OnboardingLinkResponse>("/api/v1/payouts/onboard", {
      method: "POST",
    }),

  getAccountStatus: () =>
    apiRequest<ConnectAccountResponse>("/api/v1/payouts/account"),

  getBalance: () =>
    apiRequest<BalanceResponse>("/api/v1/payouts/balance"),

  getHistory: (limit = 50, offset = 0) =>
    apiRequest<PayoutListResponse>(
      `/api/v1/payouts/history?limit=${limit}&offset=${offset}`
    ),

  initiatePayout: (amountCents: number, currency = "usd") =>
    apiRequest<InitiatePayoutResponse>("/api/v1/payouts/initiate", {
      method: "POST",
      body: { amount_cents: amountCents, currency },
    }),

  getDashboardLink: () =>
    apiRequest<{ url: string }>("/api/v1/payouts/dashboard-link"),
};

// ==================== ROI Calculator ====================

export interface RevenueBreakdown {
  brand_deals: number;
  affiliate: number;
  subscriptions: number;
  royalties: number;
  other: number;
  total: number;
}

export interface CostBreakdown {
  platform_fees: number;
  content_creation: number;
  advertising: number;
  software: number;
  equipment: number;
  labor: number;
  other: number;
  total: number;
}

export interface ROIMetrics {
  net_profit_cents: number;
  roi_percentage: number;
  profit_margin: number;
  revenue_per_content: number;
  revenue_per_view: number;
  revenue_per_follower: number;
  engagement_rate: number;
}

export interface ROIReportResponse {
  id: string;
  period_start: string;
  period_end: string;
  period_type: string;
  revenue: RevenueBreakdown;
  costs: CostBreakdown;
  metrics: ROIMetrics;
  total_views: number;
  total_engagements: number;
  new_followers: number;
  content_pieces: number;
  created_at: string;
}

export interface ROISummaryResponse {
  current_period: ROIReportResponse;
  previous_period: ROIReportResponse | null;
  revenue_change_percent: number;
  profit_change_percent: number;
  roi_change_percent: number;
}

export interface ProjectionDataPoint {
  date: string;
  projected_revenue_cents: number;
  projected_costs_cents: number;
  projected_profit_cents: number;
  confidence: number;
}

export interface ROIProjectionResponse {
  projections: ProjectionDataPoint[];
  average_monthly_revenue: number;
  average_monthly_costs: number;
  trend: "growing" | "stable" | "declining";
  confidence_score: number;
}

export interface CostEntryResponse {
  id: string;
  amount_cents: number;
  currency: string;
  category: string;
  description: string | null;
  expense_date: string;
  is_recurring: boolean;
  recurrence_period: string | null;
  created_at: string;
}

export interface CostEntryListResponse {
  entries: CostEntryResponse[];
  total_cents: number;
  by_category: Record<string, number>;
}

export const roi = {
  calculate: (startDate: string, endDate: string) =>
    apiRequest<ROIReportResponse>("/api/v1/roi/calculate", {
      method: "POST",
      body: { start_date: startDate, end_date: endDate },
    }),

  getSummary: () =>
    apiRequest<ROISummaryResponse>("/api/v1/roi/summary"),

  getHistory: (limit = 12) =>
    apiRequest<ROIReportResponse[]>(`/api/v1/roi/history?limit=${limit}`),

  getProjections: (months = 6) =>
    apiRequest<ROIProjectionResponse>(`/api/v1/roi/projections?months=${months}`),

  addCost: (data: {
    amount_cents: number;
    category: string;
    expense_date: string;
    description?: string;
    is_recurring?: boolean;
    recurrence_period?: string;
  }) =>
    apiRequest<CostEntryResponse>("/api/v1/roi/costs", {
      method: "POST",
      body: data,
    }),

  getCosts: (filters?: { start_date?: string; end_date?: string; category?: string }) => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append("start_date", filters.start_date);
    if (filters?.end_date) params.append("end_date", filters.end_date);
    if (filters?.category) params.append("category", filters.category);
    const queryString = params.toString();
    return apiRequest<CostEntryListResponse>(
      `/api/v1/roi/costs${queryString ? `?${queryString}` : ""}`
    );
  },

  deleteCost: (entryId: string) =>
    apiRequest<{ success: boolean }>(`/api/v1/roi/costs/${entryId}`, {
      method: "DELETE",
    }),
};

// ==================== Developer Portal API ====================

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  scopes: string[];
  status: "active" | "revoked";
  last_used_at?: string;
}

interface CreateApiKeyRequest {
  name: string;
  scopes: string[];
}

export const developersApi = {
  listApiKeys: () =>
    apiRequest<ApiKey[]>("/api/v1/api-keys"),

  createApiKey: (data: CreateApiKeyRequest) =>
    apiRequest<ApiKey & { secret: string }>("/api/v1/api-keys", {
      method: "POST",
      body: data,
    }),

  revokeApiKey: (id: string) =>
    apiRequest<void>(`/api/v1/api-keys/${id}`, { method: "DELETE" }),

  getUsage: (keyId: string, period: "day" | "week" | "month" = "week") =>
    apiRequest<{ timestamps: string[]; requests: number[] }>(
      `/api/v1/api-keys/${keyId}/usage?period=${period}`
    ),
};

// ==================== Contracts API ====================

interface Contract {
  id: string;
  title: string;
  brand_name: string;
  status: "draft" | "pending" | "active" | "completed" | "expired";
  value_cents: number;
  created_at: string;
  signed_at?: string;
  expires_at?: string;
  deliverables: Deliverable[];
}

interface Deliverable {
  id: string;
  description: string;
  due_date: string;
  status: "pending" | "in_progress" | "completed" | "overdue";
}

interface CreateContractRequest {
  title: string;
  brand_name: string;
  value_cents: number;
  template_id?: string;
  deliverables: Omit<Deliverable, "id" | "status">[];
}

export const contractsApi = {
  list: () =>
    apiRequest<Contract[]>("/api/v1/contracts"),

  get: (id: string) =>
    apiRequest<Contract>(`/api/v1/contracts/${id}`),

  create: (data: CreateContractRequest) =>
    apiRequest<Contract>("/api/v1/contracts", { method: "POST", body: data }),

  sign: (id: string) =>
    apiRequest<Contract>(`/api/v1/contracts/${id}/sign`, { method: "POST" }),

  updateDeliverable: (contractId: string, deliverableId: string, status: Deliverable["status"]) =>
    apiRequest<Deliverable>(`/api/v1/contracts/${contractId}/deliverables/${deliverableId}`, {
      method: "PATCH",
      body: { status },
    }),
};

// ==================== Contract Templates API ====================

interface ContractTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  variables: { name: string; type: string; required: boolean }[];
  content: string;
  usage_count: number;
}

export const contractTemplatesApi = {
  list: () =>
    apiRequest<ContractTemplate[]>("/api/v1/contracts/templates"),

  get: (id: string) =>
    apiRequest<ContractTemplate>(`/api/v1/contracts/templates/${id}`),

  create: (data: Omit<ContractTemplate, "id" | "usage_count">) =>
    apiRequest<ContractTemplate>("/api/v1/contracts/templates", { method: "POST", body: data }),
};

// ==================== Collaboration API ====================

interface CollaborationProject {
  id: string;
  name: string;
  description: string;
  status: "planning" | "in_progress" | "completed";
  collaborators: Collaborator[];
  created_at: string;
  messages: Message[];
}

interface Collaborator {
  id: string;
  name: string;
  avatar_url: string;
  role: "owner" | "collaborator";
}

interface Message {
  id: string;
  sender_id: string;
  content: string;
  sent_at: string;
}

export const collaborateApi = {
  listProjects: () =>
    apiRequest<CollaborationProject[]>("/api/v1/collaborations"),

  createProject: (data: { name: string; description: string }) =>
    apiRequest<CollaborationProject>("/api/v1/collaborations", { method: "POST", body: data }),

  getProject: (id: string) =>
    apiRequest<CollaborationProject>(`/api/v1/collaborations/${id}`),

  inviteCollaborator: (projectId: string, email: string) =>
    apiRequest<void>(`/api/v1/collaborations/${projectId}/invite`, {
      method: "POST",
      body: { email },
    }),

  sendMessage: (projectId: string, content: string) =>
    apiRequest<Message>(`/api/v1/collaborations/${projectId}/messages`, {
      method: "POST",
      body: { content },
    }),
};

// ==================== Revenue Sharing API ====================

interface RevenueAgreement {
  id: string;
  partner_name: string;
  partner_avatar: string;
  split_percentage: number;
  total_earned_cents: number;
  total_paid_cents: number;
  status: "active" | "paused" | "completed";
  created_at: string;
}

interface ProcessPayoutResponse {
  payout_id: string;
  amount_cents: number;
  status: string;
}

export const revenueSharingApi = {
  listAgreements: () =>
    apiRequest<RevenueAgreement[]>("/api/v1/revenue-sharing"),

  createAgreement: (data: { partner_email: string; split_percentage: number }) =>
    apiRequest<RevenueAgreement>("/api/v1/revenue-sharing", { method: "POST", body: data }),

  processPayout: (id: string) =>
    apiRequest<ProcessPayoutResponse>(`/api/v1/revenue-sharing/${id}/payout`, { method: "POST" }),

  pauseAgreement: (id: string) =>
    apiRequest<RevenueAgreement>(`/api/v1/revenue-sharing/${id}/pause`, { method: "POST" }),
};

// ==================== Social Listening API ====================

interface ListeningQuery {
  id: string;
  name: string;
  keywords: string[];
  platforms: string[];
  status: "active" | "paused";
  mentions_count: number;
  sentiment_breakdown: { positive: number; neutral: number; negative: number };
  created_at: string;
}

interface Mention {
  id: string;
  platform: string;
  author_name: string;
  author_avatar: string;
  content: string;
  sentiment: "positive" | "neutral" | "negative";
  engagement: number;
  posted_at: string;
  url: string;
}

export const listeningApi = {
  listQueries: () =>
    apiRequest<ListeningQuery[]>("/api/v1/listening/queries"),

  createQuery: (data: { name: string; keywords: string[]; platforms: string[] }) =>
    apiRequest<ListeningQuery>("/api/v1/listening/queries", { method: "POST", body: data }),

  getMentions: (queryId: string, filters?: { sentiment?: string; platform?: string }) => {
    const params = new URLSearchParams();
    if (filters?.sentiment) params.append("sentiment", filters.sentiment);
    if (filters?.platform) params.append("platform", filters.platform);
    const qs = params.toString();
    return apiRequest<Mention[]>(`/api/v1/listening/queries/${queryId}/mentions${qs ? `?${qs}` : ""}`);
  },

  toggleQuery: (queryId: string, active: boolean) =>
    apiRequest<ListeningQuery>(`/api/v1/listening/queries/${queryId}`, {
      method: "PATCH",
      body: { status: active ? "active" : "paused" },
    }),
};

// ==================== Custom Reports API ====================

interface Report {
  id: string;
  name: string;
  description: string;
  metrics: string[];
  platforms: string[];
  schedule?: { frequency: string; next_run: string };
  last_generated_at?: string;
  created_at: string;
}

interface ReportResult {
  report_id: string;
  generated_at: string;
  data: Record<string, unknown>;
  download_url: string;
}

export const reportsApi = {
  list: () =>
    apiRequest<Report[]>("/api/v1/reports"),

  create: (data: { name: string; description: string; metrics: string[]; platforms: string[] }) =>
    apiRequest<Report>("/api/v1/reports", { method: "POST", body: data }),

  generate: (id: string) =>
    apiRequest<ReportResult>(`/api/v1/reports/${id}/generate`, { method: "POST" }),

  schedule: (id: string, schedule: { frequency: string; time: string }) =>
    apiRequest<Report>(`/api/v1/reports/${id}/schedule`, { method: "PUT", body: schedule }),

  delete: (id: string) =>
    apiRequest<void>(`/api/v1/reports/${id}`, { method: "DELETE" }),
};

// ==================== Joint Analytics API ====================

interface JointMetrics {
  collaboration_id: string;
  combined_reach: number;
  combined_engagement: number;
  revenue_total_cents: number;
  content_count: number;
  top_performing: { platform: string; engagement: number }[];
}

export const jointAnalyticsApi = {
  getCollaborationMetrics: (collaborationId: string) =>
    apiRequest<JointMetrics>(`/api/v1/collaborations/${collaborationId}/analytics`),
};

// ==================== Tax Documentation API ====================

interface TaxInfo {
  business_type: "individual" | "llc" | "corporation";
  tax_id: string;
  legal_name: string;
  address: { street: string; city: string; state: string; zip: string; country: string };
  w9_submitted: boolean;
}

interface TaxDocument {
  id: string;
  type: "1099" | "w9" | "invoice";
  year: number;
  status: "available" | "pending";
  download_url?: string;
  created_at: string;
}

export const taxApi = {
  getTaxInfo: () =>
    apiRequest<TaxInfo>("/api/v1/tax"),

  updateTaxInfo: (data: Partial<TaxInfo>) =>
    apiRequest<TaxInfo>("/api/v1/tax", { method: "PUT", body: data }),

  listDocuments: (year?: number) => {
    const qs = year ? `?year=${year}` : "";
    return apiRequest<TaxDocument[]>(`/api/v1/tax/documents${qs}`);
  },

  downloadDocument: (documentId: string) =>
    apiRequest<{ download_url: string }>(`/api/v1/tax/documents/${documentId}/download`),
};

// ==================== Compliance Reporting API ====================

interface ComplianceReport {
  id: string;
  type: "gdpr" | "content_moderation" | "platform_compliance" | "security";
  status: "passed" | "warning" | "failed";
  generated_at: string;
  findings: { category: string; status: string; message: string }[];
}

interface ComplianceCheck {
  id: string;
  name: string;
  category: string;
  last_checked: string;
  status: "passed" | "warning" | "failed";
}

export const complianceApi = {
  listReports: () =>
    apiRequest<ComplianceReport[]>("/api/v1/admin/compliance"),

  generateReport: (type: ComplianceReport["type"]) =>
    apiRequest<ComplianceReport>("/api/v1/admin/compliance/generate", {
      method: "POST",
      body: { type },
    }),

  getChecks: () =>
    apiRequest<ComplianceCheck[]>("/api/v1/admin/compliance/checks"),

  runCheck: (checkId: string) =>
    apiRequest<ComplianceCheck>(`/api/v1/admin/compliance/checks/${checkId}/run`, {
      method: "POST",
    }),
};

// ==================== Backup Management API ====================

interface Backup {
  id: string;
  type: "full" | "incremental";
  size_bytes: number;
  status: "completed" | "in_progress" | "failed";
  created_at: string;
  completed_at?: string;
}

interface BackupSchedule {
  id: string;
  name: string;
  frequency: "daily" | "weekly" | "monthly";
  next_run: string;
  last_run?: string;
  enabled: boolean;
}

export const backupsApi = {
  list: () =>
    apiRequest<Backup[]>("/api/v1/admin/backups"),

  create: (type: "full" | "incremental" = "full") =>
    apiRequest<Backup>("/api/v1/admin/backups", { method: "POST", body: { type } }),

  restore: (id: string) =>
    apiRequest<{ job_id: string }>(`/api/v1/admin/backups/${id}/restore`, { method: "POST" }),

  listSchedules: () =>
    apiRequest<BackupSchedule[]>("/api/v1/admin/backups/schedules"),

  toggleSchedule: (id: string, enabled: boolean) =>
    apiRequest<BackupSchedule>(`/api/v1/admin/backups/schedules/${id}`, {
      method: "PATCH",
      body: { enabled },
    }),
};

// ==================== Sponsorship Management API ====================

interface Sponsorship {
  id: string;
  brand_name: string;
  brand_logo: string;
  status: "negotiating" | "active" | "completed" | "cancelled";
  value_cents: number;
  start_date: string;
  end_date: string;
  deliverables: SponsorshipDeliverable[];
}

interface SponsorshipDeliverable {
  id: string;
  type: "post" | "story" | "video" | "mention";
  platform: string;
  description: string;
  due_date: string;
  status: "pending" | "submitted" | "approved" | "revision_requested";
}

export const sponsorshipsApi = {
  list: () =>
    apiRequest<Sponsorship[]>("/api/v1/sponsorships"),

  create: (data: {
    brand_name: string;
    value_cents: number;
    start_date: string;
    end_date: string;
    deliverables: Omit<SponsorshipDeliverable, "id" | "status">[];
  }) =>
    apiRequest<Sponsorship>("/api/v1/sponsorships", { method: "POST", body: data }),

  get: (id: string) =>
    apiRequest<Sponsorship>(`/api/v1/sponsorships/${id}`),

  updateDeliverable: (sponsorshipId: string, deliverableId: string, status: SponsorshipDeliverable["status"]) =>
    apiRequest<SponsorshipDeliverable>(
      `/api/v1/sponsorships/${sponsorshipId}/deliverables/${deliverableId}`,
      { method: "PATCH", body: { status } }
    ),
};

// ==================== Offline Mode API ====================

interface OfflineSyncStatus {
  last_synced_at: string;
  pending_actions: number;
  cached_items: number;
  storage_used_bytes: number;
}

export const offlineApi = {
  getSyncStatus: () =>
    apiRequest<OfflineSyncStatus>("/api/v1/offline/status"),

  syncNow: () =>
    apiRequest<{ synced_count: number }>("/api/v1/offline/sync", { method: "POST" }),

  clearCache: () =>
    apiRequest<void>("/api/v1/offline/cache", { method: "DELETE" }),
};

export { ApiError };
