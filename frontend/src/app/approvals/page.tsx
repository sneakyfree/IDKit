"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { approvals, type ContentApprovalResponse } from "@/lib/api";

type TabType = "pending" | "approved" | "rejected";
type FilterType = "all" | "post" | "video" | "podcast";

export default function ApprovalsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("pending");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [approvalItems, setApprovalItems] = useState<ContentApprovalResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<ContentApprovalResponse | null>(null);
  const [showReviewModal, setShowReviewModal] = useState(false);

  const loadApprovals = useCallback(async () => {
    setIsLoading(true);
    try {
      // Try to load from API — uses default org if available
      const token = localStorage.getItem("token");
      if (token) {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/enterprise/content/approvals`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (response.ok) {
          const items = await response.json();
          setApprovalItems(Array.isArray(items) ? items : []);
        } else {
          setApprovalItems([]);
        }
      } else {
        setApprovalItems([]);
      }
    } catch (error) {
      console.error("Failed to load approvals:", error);
      setApprovalItems([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const handleApprove = async (itemId: string, notes?: string) => {
    try {
      const item = approvalItems.find((i) => i.id === itemId);
      if (!item) return;

      try {
        await approvals.approve(item.content_id, notes);
      } catch {
        // Optimistic update if API fails
      }

      setApprovalItems(
        approvalItems.map((i) =>
          i.id === itemId
            ? {
              ...i,
              status: "approved",
              review_notes: notes || null,
              reviewed_at: new Date().toISOString(),
            }
            : i
        )
      );
      setShowReviewModal(false);
      setSelectedItem(null);
    } catch (error) {
      console.error("Failed to approve:", error);
    }
  };

  const handleReject = async (itemId: string, reason: string) => {
    try {
      const item = approvalItems.find((i) => i.id === itemId);
      if (!item) return;

      try {
        await approvals.reject(item.content_id, reason);
      } catch {
        // Optimistic update if API fails
      }

      setApprovalItems(
        approvalItems.map((i) =>
          i.id === itemId
            ? {
              ...i,
              status: "rejected",
              review_notes: reason,
              reviewed_at: new Date().toISOString(),
            }
            : i
        )
      );
      setShowReviewModal(false);
      setSelectedItem(null);
    } catch (error) {
      console.error("Failed to reject:", error);
    }
  };

  // Derive content info from the approval item itself
  const getContentInfo = (item: ContentApprovalResponse) => ({
    title: item.notes || `Content ${item.content_id}`,
    type: "post" as string,
    author: item.requested_by || "Unknown",
    thumbnailUrl: null as string | null,
  });

  const filteredItems = approvalItems.filter((item) => {
    const matchesTab =
      activeTab === "pending"
        ? item.status === "pending_review"
        : activeTab === "approved"
          ? item.status === "approved"
          : item.status === "rejected";

    const matchesFilter = filterType === "all";

    return matchesTab && matchesFilter;
  });

  const pendingCount = approvalItems.filter((i) => i.status === "pending_review").length;

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-white">Approvals</h1>
            {pendingCount > 0 && (
              <span className="px-2 py-0.5 bg-purple-600 rounded-full text-xs font-medium">
                {pendingCount}
              </span>
            )}
          </div>
          <Link
            href="/approvals/settings"
            aria-label="Approvals settings"
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <SettingsIcon className="w-5 h-5" />
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-4 pb-3">
          {(["pending", "approved", "rejected"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${activeTab === tab
                ? "bg-white text-black"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === "pending" && pendingCount > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 bg-purple-600 rounded-full text-xs">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content Type Filter */}
        <div className="flex gap-2 px-4 pb-3 overflow-x-auto">
          {(["all", "post", "video", "podcast"] as FilterType[]).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${filterType === type
                ? "bg-purple-600 text-white"
                : "bg-gray-800/50 text-gray-200 hover:bg-gray-700"
                }`}
            >
              {type === "all" ? "All Types" : type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      <div className="px-4 py-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <LoaderIcon className="w-8 h-8 animate-spin text-purple-500" />
          </div>
        ) : filteredItems.length === 0 ? (
          <EmptyState tab={activeTab} />
        ) : (
          <div className="space-y-3">
            {filteredItems.map((item) => (
              <ApprovalCard
                key={item.id}
                item={item}
                content={getContentInfo(item)}
                onReview={() => {
                  setSelectedItem(item);
                  setShowReviewModal(true);
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Review Modal */}
      {showReviewModal && selectedItem && (
        <ReviewModal
          item={selectedItem}
          content={getContentInfo(selectedItem)}
          onApprove={(notes) => handleApprove(selectedItem.id, notes)}
          onReject={(reason) => handleReject(selectedItem.id, reason)}
          onClose={() => {
            setShowReviewModal(false);
            setSelectedItem(null);
          }}
        />
      )}

      <BottomNav />
    </main>
  );
}

// Components
function ApprovalCard({
  item,
  content,
  onReview,
}: {
  item: ContentApprovalResponse;
  content: { title: string; type: string; author: string; thumbnailUrl: string | null };
  onReview: () => void;
}) {
  const requestedDate = new Date(item.requested_at);
  const reviewedDate = item.reviewed_at ? new Date(item.reviewed_at) : null;

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <div className="flex gap-3">
        {/* Thumbnail */}
        <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center flex-shrink-0">
          <ContentTypeIcon type={content.type} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-medium text-sm truncate">{content.title}</h3>
              <p className="text-xs text-gray-200 mt-0.5">{content.author}</p>
            </div>
            <StatusBadge status={item.status} />
          </div>

          {item.notes && (
            <p className="text-xs text-gray-300 mt-2 line-clamp-2">{item.notes}</p>
          )}

          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-gray-300">
              {item.status === "pending_review"
                ? `Submitted ${formatRelativeTime(requestedDate)}`
                : reviewedDate
                  ? `Reviewed ${formatRelativeTime(reviewedDate)}`
                  : ""}
            </span>

            {item.status === "pending_review" ? (
              <button
                onClick={onReview}
                className="px-3 py-1.5 bg-purple-600 rounded-full text-xs font-medium hover:bg-purple-700 transition-colors"
              >
                Review
              </button>
            ) : (
              <Link
                href={`/studio/edit/${item.content_id}`}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                View Content &rarr;
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Review Notes */}
      {item.review_notes && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-200">
            <span className="font-medium">Review Notes:</span> {item.review_notes}
          </p>
        </div>
      )}
    </div>
  );
}

function ReviewModal({
  item,
  content,
  onApprove,
  onReject,
  onClose,
}: {
  item: ContentApprovalResponse;
  content: { title: string; type: string; author: string; thumbnailUrl: string | null };
  onApprove: (notes?: string) => void;
  onReject: (reason: string) => void;
  onClose: () => void;
}) {
  const [mode, setMode] = useState<"review" | "approve" | "reject">("review");
  const [notes, setNotes] = useState("");

  const handleSubmit = () => {
    if (mode === "approve") {
      onApprove(notes || undefined);
    } else if (mode === "reject") {
      if (!notes.trim()) {
        alert("Please provide a reason for rejection");
        return;
      }
      onReject(notes);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-gray-900 rounded-t-3xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">
            {mode === "review" ? "Review Content" : mode === "approve" ? "Approve Content" : "Reject Content"}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full">
            <CloseIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content Preview */}
        <div className="bg-gray-800 rounded-xl p-4 mb-6">
          <div className="flex gap-3">
            <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center flex-shrink-0">
              <ContentTypeIcon type={content.type} />
            </div>
            <div>
              <h3 className="font-medium">{content.title}</h3>
              <p className="text-sm text-gray-200 mt-1">{content.author}</p>
              <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs ${getTypeColor(content.type)}`}>
                {content.type}
              </span>
            </div>
          </div>

          {item.notes && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <p className="text-xs text-gray-200">
                <span className="font-medium">Submitter Notes:</span> {item.notes}
              </p>
            </div>
          )}
        </div>

        {mode === "review" ? (
          <>
            {/* Quick Actions */}
            <div className="space-y-3 mb-6">
              <Link
                href={`/studio/edit/${item.content_id}`}
                className="flex items-center justify-between p-4 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <EyeIcon className="w-5 h-5 text-gray-200" />
                  <span className="text-sm font-medium">Preview Full Content</span>
                </div>
                <ChevronRightIcon className="w-5 h-5 text-gray-300" />
              </Link>

              <button className="w-full flex items-center justify-between p-4 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors">
                <div className="flex items-center gap-3">
                  <HistoryIcon className="w-5 h-5 text-gray-200" />
                  <span className="text-sm font-medium">View Edit History</span>
                </div>
                <ChevronRightIcon className="w-5 h-5 text-gray-300" />
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setMode("reject")}
                className="flex-1 px-4 py-3 bg-red-600/20 text-red-400 rounded-full text-sm font-medium hover:bg-red-600/30 transition-colors"
              >
                Reject
              </button>
              <button
                onClick={() => setMode("approve")}
                className="flex-1 px-4 py-3 bg-green-600 rounded-full text-sm font-medium hover:bg-green-700 transition-colors"
              >
                Approve
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Notes Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-200 mb-2">
                {mode === "approve" ? "Approval Notes (Optional)" : "Reason for Rejection *"}
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={
                  mode === "approve"
                    ? "Add any notes for the content creator..."
                    : "Please explain why this content is being rejected..."
                }
                rows={4}
                className="w-full bg-gray-800 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setMode("review");
                  setNotes("");
                }}
                className="flex-1 px-4 py-3 bg-gray-800 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                className={`flex-1 px-4 py-3 rounded-full text-sm font-medium transition-colors ${mode === "approve"
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-red-600 hover:bg-red-700"
                  }`}
              >
                {mode === "approve" ? "Confirm Approval" : "Confirm Rejection"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ tab }: { tab: TabType }) {
  const messages = {
    pending: {
      title: "No pending approvals",
      description: "All content has been reviewed. Check back later for new submissions.",
    },
    approved: {
      title: "No approved content",
      description: "Content that you approve will appear here.",
    },
    rejected: {
      title: "No rejected content",
      description: "Content that you reject will appear here for reference.",
    },
  };

  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
        <CheckCircleIcon className="w-8 h-8 text-gray-200" />
      </div>
      <h3 className="font-medium text-gray-200">{messages[tab].title}</h3>
      <p className="text-sm text-gray-300 mt-1">{messages[tab].description}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending_review: "bg-yellow-500/20 text-yellow-400",
    approved: "bg-green-500/20 text-green-400",
    rejected: "bg-red-500/20 text-red-400",
    draft: "bg-gray-500/20 text-gray-200",
  };

  const labels: Record<string, string> = {
    pending_review: "Pending",
    approved: "Approved",
    rejected: "Rejected",
    draft: "Draft",
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.draft}`}>
      {labels[status] || status}
    </span>
  );
}

function ContentTypeIcon({ type }: { type: string }) {
  switch (type) {
    case "video":
      return <VideoIcon className="w-6 h-6 text-gray-300" />;
    case "podcast":
      return <MicIcon className="w-6 h-6 text-gray-300" />;
    default:
      return <EditIcon className="w-6 h-6 text-gray-300" />;
  }
}

function getTypeColor(type: string): string {
  switch (type) {
    case "video":
      return "bg-red-500/20 text-red-400";
    case "podcast":
      return "bg-purple-500/20 text-purple-400";
    default:
      return "bg-blue-500/20 text-blue-400";
  }
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// Icons
function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function VideoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function EditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function HistoryIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}
