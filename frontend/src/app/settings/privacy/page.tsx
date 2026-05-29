"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { privacy, type PrivacySettingsResponse, type DataRequestResponse, type DataCategoryResponse } from "@/lib/api";

type TabType = "settings" | "data" | "rights";

interface ConsentItem {
  key: keyof PrivacySettingsResponse;
  label: string;
  description: string;
  category: "visibility" | "personalization" | "communications";
}

const consentItems: ConsentItem[] = [
  {
    key: "profile_visibility",
    label: "Profile Visibility",
    description: "Control who can see your profile information",
    category: "visibility",
  },
  {
    key: "activity_visibility",
    label: "Activity Visibility",
    description: "Control who can see your activity (likes, comments)",
    category: "visibility",
  },
  {
    key: "search_visibility",
    label: "Appear in Search",
    description: "Allow others to find you through search",
    category: "visibility",
  },
  {
    key: "analytics_enabled",
    label: "Usage Analytics",
    description: "Help us improve by sharing anonymous usage data",
    category: "personalization",
  },
  {
    key: "personalization_enabled",
    label: "Content Personalization",
    description: "Allow AI to personalize your content recommendations",
    category: "personalization",
  },
  {
    key: "third_party_sharing",
    label: "Third-Party Sharing",
    description: "Share data with trusted partners for better services",
    category: "personalization",
  },
  {
    key: "marketing_emails",
    label: "Marketing Emails",
    description: "Receive promotional content and special offers",
    category: "communications",
  },
  {
    key: "product_updates",
    label: "Product Updates",
    description: "Get notified about new features and improvements",
    category: "communications",
  },
];

export default function PrivacySettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("settings");
  const [settings, setSettings] = useState<PrivacySettingsResponse | null>(null);
  const [dataCategories, setDataCategories] = useState<DataCategoryResponse[]>([]);
  const [dataRequests, setDataRequests] = useState<DataRequestResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [deleteType, setDeleteType] = useState<"data" | "account">("data");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load settings, categories, and requests in parallel
      const [settingsRes, categoriesRes, requestsRes] = await Promise.all([
        privacy.getSettings().catch(() => null),
        privacy.getDataCategories().catch(() => ({ categories: [] })),
        privacy.listDataRequests().catch(() => []),
      ]);

      if (settingsRes) setSettings(settingsRes);
      setDataCategories(categoriesRes.categories);
      setDataRequests(requestsRes);
    } catch (error) {
      console.error("Failed to load privacy data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSetting = async (key: keyof PrivacySettingsResponse, value: boolean | string) => {
    if (!settings) return;

    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setIsSaving(true);

    try {
      await privacy.updateSettings({ [key]: value });
    } catch (error) {
      // Revert on error
      setSettings(settings);
      console.error("Failed to update setting:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const requestDataExport = async (categories: string[]) => {
    try {
      const request = await privacy.createDataRequest("export", categories);
      setDataRequests([request, ...dataRequests]);
      setShowExportModal(false);
    } catch (error) {
      console.error("Failed to request export:", error);
    }
  };

  const handleDeleteData = async () => {
    try {
      if (deleteType === "account") {
        await privacy.deleteAccount();
        // Redirect to logout
        window.location.href = "/auth";
      } else {
        await privacy.deleteData();
        loadData();
      }
      setShowDeleteModal(false);
    } catch (error) {
      console.error("Failed to delete:", error);
    }
  };

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center gap-3 px-4 py-3">
          <Link href="/settings" className="p-2 -ml-2 hover:bg-gray-800 rounded-lg" aria-label="Back">
            <ChevronLeftIcon className="w-5 h-5" />
          </Link>
          <h1 className="text-xl font-bold text-white">Privacy & Data</h1>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-4 pb-3">
          {(["settings", "data", "rights"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "bg-white text-black"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {tab === "settings" ? "Settings" : tab === "data" ? "Your Data" : "Your Rights"}
            </button>
          ))}
        </div>
      </header>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <LoaderIcon className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      ) : (
        <>
          {/* Settings Tab */}
          {activeTab === "settings" && (
            <div className="px-4 py-4 space-y-6">
              <section className="bg-gray-900 rounded-xl p-4 space-y-3">
                <h3 className="text-sm font-medium text-gray-200">Data &amp; Privacy</h3>
                <button type="button" onClick={() => setShowExportModal(true)} className="w-full text-left px-4 py-2 bg-gray-800 rounded-lg text-white text-sm">Request Export</button>
                <button type="button" onClick={() => { setDeleteType("account"); setShowDeleteModal(true); }} className="w-full text-left px-4 py-2 bg-red-600/80 rounded-lg text-white text-sm">Delete Account</button>
              </section>
              {/* Visibility Settings */}
              <section>
                <h2 className="text-sm font-medium text-gray-200 mb-3 flex items-center gap-2">
                  <EyeIcon className="w-4 h-4" />
                  Visibility
                </h2>
                <div className="space-y-1">
                  {consentItems
                    .filter((item) => item.category === "visibility")
                    .map((item) => (
                      <ConsentToggle
                        key={item.key}
                        item={item}
                        value={settings?.[item.key] ?? false}
                        onChange={(value) => updateSetting(item.key, value)}
                        disabled={isSaving}
                      />
                    ))}
                </div>
              </section>

              {/* Personalization Settings */}
              <section>
                <h2 className="text-sm font-medium text-gray-200 mb-3 flex items-center gap-2">
                  <SparklesIcon className="w-4 h-4" />
                  Personalization & Analytics
                </h2>
                <div className="space-y-1">
                  {consentItems
                    .filter((item) => item.category === "personalization")
                    .map((item) => (
                      <ConsentToggle
                        key={item.key}
                        item={item}
                        value={settings?.[item.key] ?? false}
                        onChange={(value) => updateSetting(item.key, value)}
                        disabled={isSaving}
                      />
                    ))}
                </div>
              </section>

              {/* Communication Settings */}
              <section>
                <h2 className="text-sm font-medium text-gray-200 mb-3 flex items-center gap-2">
                  <MailIcon className="w-4 h-4" />
                  Communications
                </h2>
                <div className="space-y-1">
                  {consentItems
                    .filter((item) => item.category === "communications")
                    .map((item) => (
                      <ConsentToggle
                        key={item.key}
                        item={item}
                        value={settings?.[item.key] ?? false}
                        onChange={(value) => updateSetting(item.key, value)}
                        disabled={isSaving}
                      />
                    ))}
                </div>
              </section>

              {/* Info Notice */}
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
                <div className="flex gap-3">
                  <InfoIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-gray-300">
                    <p>
                      Your privacy choices are saved automatically. Some changes may take up to 24
                      hours to take effect across all systems.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Data Tab */}
          {activeTab === "data" && (
            <div className="px-4 py-4 space-y-6">
              {/* Data Categories */}
              <section>
                <h2 className="text-sm font-medium text-gray-200 mb-3">Data We Collect</h2>
                <div className="space-y-2">
                  {dataCategories.length > 0 ? (
                    dataCategories.map((category) => (
                      <div
                        key={category.id}
                        className="bg-gray-900 rounded-xl p-4"
                      >
                        <h3 className="font-medium text-sm">{category.name}</h3>
                        <p className="text-xs text-gray-200 mt-1">{category.description}</p>
                      </div>
                    ))
                  ) : (
                    <div className="bg-gray-900 rounded-xl p-4 space-y-2">
                      {[
                        { name: "Profile", desc: "Your profile information (name, bio, avatar)" },
                        { name: "Content", desc: "Posts, videos, and other content you create" },
                        { name: "Analytics", desc: "Usage patterns and engagement metrics" },
                        { name: "Interactions", desc: "Likes, comments, and social interactions" },
                      ].map((item) => (
                        <div key={item.name} className="py-2 border-b border-gray-800 last:border-0">
                          <h3 className="font-medium text-sm">{item.name}</h3>
                          <p className="text-xs text-gray-200 mt-0.5">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>

              {/* Data Actions */}
              <section>
                <h2 className="text-sm font-medium text-gray-200 mb-3">Data Actions</h2>
                <div className="space-y-2">
                  <button
                    onClick={() => setShowExportModal(true)}
                    className="w-full flex items-center justify-between p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                        <DownloadIcon className="w-5 h-5 text-blue-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="font-medium text-sm">Export Your Data</h3>
                        <p className="text-xs text-gray-200">Download a copy of all your data</p>
                      </div>
                    </div>
                    <ChevronRightIcon className="w-5 h-5 text-gray-300" />
                  </button>

                  <button
                    onClick={() => {
                      setDeleteType("data");
                      setShowDeleteModal(true);
                    }}
                    className="w-full flex items-center justify-between p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                        <TrashIcon className="w-5 h-5 text-yellow-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="font-medium text-sm">Delete Your Data</h3>
                        <p className="text-xs text-gray-200">Remove specific data categories</p>
                      </div>
                    </div>
                    <ChevronRightIcon className="w-5 h-5 text-gray-300" />
                  </button>

                  <button
                    onClick={() => {
                      setDeleteType("account");
                      setShowDeleteModal(true);
                    }}
                    className="w-full flex items-center justify-between p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                        <UserXIcon className="w-5 h-5 text-red-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="font-medium text-sm text-red-400">Delete Account</h3>
                        <p className="text-xs text-gray-200">Permanently delete your account and all data</p>
                      </div>
                    </div>
                    <ChevronRightIcon className="w-5 h-5 text-gray-300" />
                  </button>
                </div>
              </section>

              {/* Recent Requests */}
              {dataRequests.length > 0 && (
                <section>
                  <h2 className="text-sm font-medium text-gray-200 mb-3">Recent Requests</h2>
                  <div className="space-y-2">
                    {dataRequests.map((request) => (
                      <div key={request.id} className="bg-gray-900 rounded-xl p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-sm capitalize">{request.request_type} Request</h3>
                            <p className="text-xs text-gray-200 mt-1">
                              {new Date(request.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <RequestStatusBadge status={request.status} />
                        </div>
                        {request.download_url && request.status === "completed" && (
                          <a
                            href={request.download_url}
                            className="mt-3 inline-flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300"
                          >
                            <DownloadIcon className="w-4 h-4" />
                            Download
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}

          {/* Rights Tab */}
          {activeTab === "rights" && (
            <div className="px-4 py-4 space-y-6">
              <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4 mb-6">
                <h2 className="font-medium text-purple-400 mb-2">Your Privacy Rights</h2>
                <p className="text-sm text-gray-300">
                  Under GDPR and other privacy regulations, you have the following rights regarding
                  your personal data.
                </p>
              </div>

              <div className="space-y-3">
                {[
                  {
                    article: "15",
                    title: "Right of Access",
                    description: "You can request a copy of all personal data we hold about you.",
                    action: "Export Data",
                    onClick: () => setShowExportModal(true),
                  },
                  {
                    article: "16",
                    title: "Right to Rectification",
                    description: "You can correct inaccurate personal data we hold about you.",
                    action: "Edit Profile",
                    href: "/profile/edit",
                  },
                  {
                    article: "17",
                    title: "Right to Erasure",
                    description: 'Also known as the "right to be forgotten" - you can request deletion of your data.',
                    action: "Delete Data",
                    onClick: () => {
                      setDeleteType("data");
                      setShowDeleteModal(true);
                    },
                  },
                  {
                    article: "18",
                    title: "Right to Restrict Processing",
                    description: "You can limit how we use your data in certain circumstances.",
                    action: "Manage Settings",
                    onClick: () => setActiveTab("settings"),
                  },
                  {
                    article: "20",
                    title: "Right to Data Portability",
                    description: "You can receive your data in a machine-readable format.",
                    action: "Export Data",
                    onClick: () => setShowExportModal(true),
                  },
                  {
                    article: "21",
                    title: "Right to Object",
                    description: "You can object to certain types of processing like marketing.",
                    action: "Manage Consent",
                    onClick: () => setActiveTab("settings"),
                  },
                ].map((right) => (
                  <div key={right.article} className="bg-gray-900 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-purple-400">{right.article}</span>
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm">{right.title}</h3>
                        <p className="text-xs text-gray-200 mt-1">{right.description}</p>
                        {right.href ? (
                          <Link
                            href={right.href}
                            className="inline-block mt-2 text-xs text-purple-400 hover:text-purple-300"
                          >
                            {right.action} &rarr;
                          </Link>
                        ) : (
                          <button
                            onClick={right.onClick}
                            className="mt-2 text-xs text-purple-400 hover:text-purple-300"
                          >
                            {right.action} &rarr;
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Contact Information */}
              <div className="bg-gray-900 rounded-xl p-4">
                <h3 className="font-medium text-sm mb-3">Contact Our Data Protection Officer</h3>
                <div className="space-y-2 text-sm text-gray-200">
                  <p>Email: privacy@idkit.io</p>
                  <p>DPO: dpo@idkit.io</p>
                  <p className="text-xs">Response time: within 30 days</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          categories={dataCategories}
          onExport={requestDataExport}
          onClose={() => setShowExportModal(false)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <DeleteModal
          type={deleteType}
          onConfirm={handleDeleteData}
          onClose={() => setShowDeleteModal(false)}
        />
      )}
      <BottomNav />
    </main>
  );
}

// Components
function ConsentToggle({
  item,
  value,
  onChange,
  disabled,
}: {
  item: ConsentItem;
  value: boolean | string;
  onChange: (value: boolean | string) => void;
  disabled: boolean;
}) {
  const isBoolean = typeof value === "boolean";

  if (item.key === "profile_visibility" || item.key === "activity_visibility") {
    return (
      <div className="bg-gray-900 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium text-sm">{item.label}</h3>
            <p className="text-xs text-gray-200 mt-0.5">{item.description}</p>
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          {["public", "followers", "private"].map((option) => (
            <button
              key={option}
              onClick={() => onChange(option)}
              disabled={disabled}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                value === option
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800 text-gray-200 hover:bg-gray-700"
              } disabled:opacity-80`}
            >
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between bg-gray-900 rounded-xl p-4">
      <div className="flex-1 mr-4">
        <h3 className="font-medium text-sm">{item.label}</h3>
        <p className="text-xs text-gray-200 mt-0.5">{item.description}</p>
      </div>
      <Toggle
        enabled={isBoolean ? value : false}
        onChange={() => onChange(isBoolean ? !value : true)}
        disabled={disabled}
      />
    </div>
  );
}

function Toggle({
  enabled,
  onChange,
  disabled,
}: {
  enabled: boolean;
  onChange: () => void;
  disabled: boolean;
}) {
  return (
    <button
      onClick={onChange}
      disabled={disabled}
      className={`relative w-11 h-6 rounded-full transition-colors disabled:opacity-80 ${
        enabled ? "bg-purple-600" : "bg-gray-700"
      }`}
    >
      <div
        className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

function ExportModal({
  categories,
  onExport,
  onClose,
}: {
  categories: DataCategoryResponse[];
  onExport: (categories: string[]) => void;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(true);

  const defaultCategories = ["profile", "content", "analytics", "interactions", "messages", "settings"];
  const categoryList = categories.length > 0 ? categories.map((c) => c.id) : defaultCategories;

  const toggleCategory = (id: string) => {
    if (selected.includes(id)) {
      setSelected(selected.filter((c) => c !== id));
      setSelectAll(false);
    } else {
      setSelected([...selected, id]);
    }
  };

  const handleExport = () => {
    onExport(selectAll ? [] : selected);
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-gray-900 rounded-t-3xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Export Your Data</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full">
            <CloseIcon className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-gray-200 mb-4">
          Select the data categories you want to export. Your data will be prepared and you&apos;ll
          receive a download link.
        </p>

        <div className="space-y-2 mb-6">
          <label className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
            <input
              type="checkbox"
              checked={selectAll}
              onChange={(e) => {
                setSelectAll(e.target.checked);
                if (e.target.checked) setSelected([]);
              }}
              className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
            <span className="font-medium text-sm">All Data</span>
          </label>

          {!selectAll && (
            <div className="pl-4 space-y-1">
              {categoryList.map((cat) => (
                <label key={cat} className="flex items-center gap-3 p-2">
                  <input
                    type="checkbox"
                    checked={selected.includes(cat)}
                    onChange={() => toggleCategory(cat)}
                    className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm capitalize">{cat}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-800 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Request Export
          </button>
        </div>
      </div>
    </div>
  );
}

function DeleteModal({
  type,
  onConfirm,
  onClose,
}: {
  type: "data" | "account";
  onConfirm: () => void;
  onClose: () => void;
}) {
  const [confirmText, setConfirmText] = useState("");
  const isAccount = type === "account";
  const requiredText = isAccount ? "DELETE MY ACCOUNT" : "DELETE";

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-gray-900 rounded-t-3xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-red-400">
            {isAccount ? "Delete Forever" : "Confirm Delete"}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full">
            <CloseIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
          <div className="flex gap-3">
            <AlertIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div className="text-sm text-gray-300">
              {isAccount ? (
                <p>
                  This action is <strong>permanent and irreversible</strong>. All your data,
                  content, and account information will be permanently deleted. You will not be
                  able to recover your account.
                </p>
              ) : (
                <p>
                  This will delete selected data categories. Some data may be retained for legal
                  compliance. This action cannot be undone.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-200 mb-2">
            Type <span className="font-mono text-red-400">{requiredText}</span> to confirm
          </label>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={requiredText}
            className="w-full bg-gray-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-800 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={confirmText !== requiredText}
            className="flex-1 px-4 py-3 bg-red-600 rounded-full text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-80 disabled:cursor-not-allowed"
          >
            {isAccount ? "Delete Forever" : "Confirm Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RequestStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-yellow-500/20 text-yellow-400",
    processing: "bg-blue-500/20 text-blue-400",
    completed: "bg-green-500/20 text-green-400",
    failed: "bg-red-500/20 text-red-400",
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// Icons
function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
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

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}

function MailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  );
}

function UserXIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6" />
    </svg>
  );
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
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
