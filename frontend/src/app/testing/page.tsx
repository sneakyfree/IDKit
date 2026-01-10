"use client";

import { useState, useEffect } from "react";
import { testing } from "@/lib/api";

type TabType = "active" | "completed" | "draft";
type TestType = "content" | "subject_line" | "send_time" | "audience";
type TestStatus = "draft" | "running" | "completed" | "paused";

interface Variant {
  id: string;
  name: string;
  content: string;
  impressions: number;
  conversions: number;
  conversionRate: number;
  isControl: boolean;
  isWinner?: boolean;
}

interface ABTest {
  id: string;
  name: string;
  description: string;
  testType: TestType;
  status: TestStatus;
  variants: Variant[];
  targetAudience: string;
  trafficSplit: number[];
  startDate: string | null;
  endDate: string | null;
  winningCriteria: string;
  confidenceLevel: number;
  statisticalSignificance: number | null;
  createdAt: string;
}

// Mock data for demonstration
const mockTests: ABTest[] = [
  {
    id: "1",
    name: "Homepage CTA Button Test",
    description: "Testing different CTA button colors and text",
    testType: "content",
    status: "running",
    variants: [
      {
        id: "v1",
        name: "Control - Blue Button",
        content: "Get Started",
        impressions: 5420,
        conversions: 325,
        conversionRate: 6.0,
        isControl: true,
      },
      {
        id: "v2",
        name: "Variant A - Green Button",
        content: "Start Free Trial",
        impressions: 5380,
        conversions: 412,
        conversionRate: 7.66,
        isControl: false,
      },
    ],
    targetAudience: "All visitors",
    trafficSplit: [50, 50],
    startDate: "2024-01-15T10:00:00Z",
    endDate: null,
    winningCriteria: "conversion_rate",
    confidenceLevel: 95,
    statisticalSignificance: 87,
    createdAt: "2024-01-14T08:30:00Z",
  },
  {
    id: "2",
    name: "Email Subject Line Test",
    description: "Testing personalized vs generic subject lines",
    testType: "subject_line",
    status: "completed",
    variants: [
      {
        id: "v1",
        name: "Generic Subject",
        content: "Check out our latest features",
        impressions: 10000,
        conversions: 2100,
        conversionRate: 21.0,
        isControl: true,
      },
      {
        id: "v2",
        name: "Personalized Subject",
        content: "{{name}}, see what's new for you",
        impressions: 10000,
        conversions: 2850,
        conversionRate: 28.5,
        isControl: false,
        isWinner: true,
      },
    ],
    targetAudience: "Newsletter subscribers",
    trafficSplit: [50, 50],
    startDate: "2024-01-01T09:00:00Z",
    endDate: "2024-01-10T09:00:00Z",
    winningCriteria: "open_rate",
    confidenceLevel: 95,
    statisticalSignificance: 99,
    createdAt: "2023-12-28T14:00:00Z",
  },
  {
    id: "3",
    name: "Send Time Optimization",
    description: "Finding the best time to send promotional emails",
    testType: "send_time",
    status: "draft",
    variants: [
      {
        id: "v1",
        name: "Morning (9 AM)",
        content: "09:00",
        impressions: 0,
        conversions: 0,
        conversionRate: 0,
        isControl: true,
      },
      {
        id: "v2",
        name: "Afternoon (2 PM)",
        content: "14:00",
        impressions: 0,
        conversions: 0,
        conversionRate: 0,
        isControl: false,
      },
      {
        id: "v3",
        name: "Evening (7 PM)",
        content: "19:00",
        impressions: 0,
        conversions: 0,
        conversionRate: 0,
        isControl: false,
      },
    ],
    targetAudience: "Active users",
    trafficSplit: [34, 33, 33],
    startDate: null,
    endDate: null,
    winningCriteria: "click_rate",
    confidenceLevel: 95,
    statisticalSignificance: null,
    createdAt: "2024-01-18T11:00:00Z",
  },
];

function TestTypeIcon({ type }: { type: TestType }) {
  const icons: Record<TestType, string> = {
    content: "📝",
    subject_line: "✉️",
    send_time: "⏰",
    audience: "👥",
  };
  return <span className="text-lg">{icons[type]}</span>;
}

function StatusBadge({ status }: { status: TestStatus }) {
  const styles: Record<TestStatus, string> = {
    draft: "bg-gray-700 text-gray-300",
    running: "bg-green-900 text-green-300",
    completed: "bg-blue-900 text-blue-300",
    paused: "bg-yellow-900 text-yellow-300",
  };

  const labels: Record<TestStatus, string> = {
    draft: "Draft",
    running: "Running",
    completed: "Completed",
    paused: "Paused",
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number | null }) {
  if (value === null) return <span className="text-gray-500 text-sm">Not started</span>;

  const getColor = (v: number) => {
    if (v >= 95) return "bg-green-500";
    if (v >= 80) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor(value)} transition-all duration-300`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-sm text-gray-400 w-12">{value}%</span>
    </div>
  );
}

function VariantComparison({ variants }: { variants: Variant[] }) {
  const maxConversionRate = Math.max(...variants.map((v) => v.conversionRate));

  return (
    <div className="space-y-3">
      {variants.map((variant) => (
        <div key={variant.id} className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-300">{variant.name}</span>
              {variant.isControl && (
                <span className="px-1.5 py-0.5 bg-gray-700 text-gray-400 text-xs rounded">
                  Control
                </span>
              )}
              {variant.isWinner && (
                <span className="px-1.5 py-0.5 bg-green-900 text-green-300 text-xs rounded">
                  Winner
                </span>
              )}
            </div>
            <span className="text-sm font-medium text-white">
              {variant.conversionRate.toFixed(2)}%
            </span>
          </div>
          <div className="h-6 bg-gray-700 rounded overflow-hidden relative">
            <div
              className={`h-full transition-all duration-500 ${
                variant.isWinner
                  ? "bg-green-500"
                  : variant.isControl
                  ? "bg-blue-500"
                  : "bg-purple-500"
              }`}
              style={{
                width: maxConversionRate > 0
                  ? `${(variant.conversionRate / maxConversionRate) * 100}%`
                  : "0%",
              }}
            />
            <div className="absolute inset-0 flex items-center justify-between px-2 text-xs">
              <span className="text-white/80">
                {variant.impressions.toLocaleString()} impressions
              </span>
              <span className="text-white/80">
                {variant.conversions.toLocaleString()} conversions
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function TestCard({
  test,
  onView,
  onStart,
  onEnd,
}: {
  test: ABTest;
  onView: () => void;
  onStart: () => void;
  onEnd: () => void;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-gray-700 rounded-lg">
            <TestTypeIcon type={test.testType} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{test.name}</h3>
            <p className="text-sm text-gray-400">{test.description}</p>
          </div>
        </div>
        <StatusBadge status={test.status} />
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Target Audience</span>
          <p className="text-gray-300">{test.targetAudience}</p>
        </div>
        <div>
          <span className="text-gray-500">Winning Criteria</span>
          <p className="text-gray-300 capitalize">
            {test.winningCriteria.replace("_", " ")}
          </p>
        </div>
        <div>
          <span className="text-gray-500">Traffic Split</span>
          <p className="text-gray-300">{test.trafficSplit.join(" / ")}%</p>
        </div>
      </div>

      {test.status !== "draft" && (
        <>
          <div>
            <span className="text-sm text-gray-500">Statistical Significance</span>
            <ConfidenceBar value={test.statisticalSignificance} />
          </div>

          <VariantComparison variants={test.variants} />
        </>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-gray-700">
        <div className="text-xs text-gray-500">
          {test.startDate ? (
            <>
              Started: {new Date(test.startDate).toLocaleDateString()}
              {test.endDate && (
                <> · Ended: {new Date(test.endDate).toLocaleDateString()}</>
              )}
            </>
          ) : (
            <>Created: {new Date(test.createdAt).toLocaleDateString()}</>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={onView}
            className="px-3 py-1.5 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
          >
            View Details
          </button>
          {test.status === "draft" && (
            <button
              onClick={onStart}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Start Test
            </button>
          )}
          {test.status === "running" && (
            <button
              onClick={onEnd}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              End & Analyze
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function CreateTestModal({
  isOpen,
  onClose,
  onCreate,
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (test: Partial<ABTest>) => void;
}) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    testType: "content" as TestType,
    targetAudience: "",
    winningCriteria: "conversion_rate",
    confidenceLevel: 95,
    variants: [
      { name: "Control", content: "", isControl: true },
      { name: "Variant A", content: "", isControl: false },
    ],
  });

  if (!isOpen) return null;

  const handleAddVariant = () => {
    const variantLetter = String.fromCharCode(65 + formData.variants.length - 1);
    setFormData({
      ...formData,
      variants: [
        ...formData.variants,
        { name: `Variant ${variantLetter}`, content: "", isControl: false },
      ],
    });
  };

  const handleRemoveVariant = (index: number) => {
    if (formData.variants.length <= 2) return;
    setFormData({
      ...formData,
      variants: formData.variants.filter((_, i) => i !== index),
    });
  };

  const handleSubmit = () => {
    onCreate({
      name: formData.name,
      description: formData.description,
      testType: formData.testType,
      targetAudience: formData.targetAudience,
      winningCriteria: formData.winningCriteria,
      confidenceLevel: formData.confidenceLevel,
      status: "draft",
    });
    onClose();
    setStep(1);
    setFormData({
      name: "",
      description: "",
      testType: "content",
      targetAudience: "",
      winningCriteria: "conversion_rate",
      confidenceLevel: 95,
      variants: [
        { name: "Control", content: "", isControl: true },
        { name: "Variant A", content: "", isControl: false },
      ],
    });
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Create A/B Test</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
          <div className="flex gap-2 mt-4">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`flex-1 h-1 rounded-full ${
                  s <= step ? "bg-purple-500" : "bg-gray-700"
                }`}
              />
            ))}
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Basic Info</span>
            <span>Variants</span>
            <span>Settings</span>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Test Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Homepage CTA Button Test"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="What are you testing and why?"
                  rows={3}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Test Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {(
                    [
                      { value: "content", label: "Content", icon: "📝" },
                      { value: "subject_line", label: "Subject Line", icon: "✉️" },
                      { value: "send_time", label: "Send Time", icon: "⏰" },
                      { value: "audience", label: "Audience", icon: "👥" },
                    ] as const
                  ).map((type) => (
                    <button
                      key={type.value}
                      onClick={() =>
                        setFormData({ ...formData, testType: type.value })
                      }
                      className={`p-3 rounded-lg border text-left flex items-center gap-2 transition-colors ${
                        formData.testType === type.value
                          ? "border-purple-500 bg-purple-500/20"
                          : "border-gray-600 hover:border-gray-500"
                      }`}
                    >
                      <span className="text-xl">{type.icon}</span>
                      <span className="text-white">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="space-y-3">
                {formData.variants.map((variant, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-700 rounded-lg space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={variant.name}
                          onChange={(e) => {
                            const newVariants = [...formData.variants];
                            newVariants[index].name = e.target.value;
                            setFormData({ ...formData, variants: newVariants });
                          }}
                          className="px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        />
                        {variant.isControl && (
                          <span className="px-2 py-0.5 bg-blue-900 text-blue-300 text-xs rounded">
                            Control
                          </span>
                        )}
                      </div>
                      {!variant.isControl && formData.variants.length > 2 && (
                        <button
                          onClick={() => handleRemoveVariant(index)}
                          className="text-gray-400 hover:text-red-400 transition-colors"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                    <textarea
                      value={variant.content}
                      onChange={(e) => {
                        const newVariants = [...formData.variants];
                        newVariants[index].content = e.target.value;
                        setFormData({ ...formData, variants: newVariants });
                      }}
                      placeholder={`Enter ${variant.name.toLowerCase()} content...`}
                      rows={2}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 resize-none text-sm"
                    />
                  </div>
                ))}
              </div>
              {formData.variants.length < 4 && (
                <button
                  onClick={handleAddVariant}
                  className="w-full py-2 border-2 border-dashed border-gray-600 rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
                >
                  + Add Variant
                </button>
              )}
            </>
          )}

          {step === 3 && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Target Audience
                </label>
                <input
                  type="text"
                  value={formData.targetAudience}
                  onChange={(e) =>
                    setFormData({ ...formData, targetAudience: e.target.value })
                  }
                  placeholder="e.g., All visitors, Newsletter subscribers"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Winning Criteria
                </label>
                <select
                  value={formData.winningCriteria}
                  onChange={(e) =>
                    setFormData({ ...formData, winningCriteria: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="conversion_rate">Conversion Rate</option>
                  <option value="click_rate">Click Rate</option>
                  <option value="open_rate">Open Rate</option>
                  <option value="engagement">Engagement Score</option>
                  <option value="revenue">Revenue per User</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Confidence Level: {formData.confidenceLevel}%
                </label>
                <input
                  type="range"
                  min="80"
                  max="99"
                  value={formData.confidenceLevel}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      confidenceLevel: parseInt(e.target.value),
                    })
                  }
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>80%</span>
                  <span>90%</span>
                  <span>95%</span>
                  <span>99%</span>
                </div>
              </div>
              <div className="p-4 bg-gray-700/50 rounded-lg">
                <h4 className="text-sm font-medium text-white mb-2">
                  Test Summary
                </h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500">Name:</span>{" "}
                    <span className="text-gray-300">{formData.name || "—"}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Type:</span>{" "}
                    <span className="text-gray-300 capitalize">
                      {formData.testType.replace("_", " ")}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Variants:</span>{" "}
                    <span className="text-gray-300">
                      {formData.variants.length}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Audience:</span>{" "}
                    <span className="text-gray-300">
                      {formData.targetAudience || "—"}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="p-6 border-t border-gray-700 flex justify-between">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Back
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          )}
          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={step === 1 && !formData.name}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!formData.name || !formData.targetAudience}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Create Test
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function TestDetailModal({
  test,
  isOpen,
  onClose,
}: {
  test: ABTest | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!isOpen || !test) return null;

  const totalImpressions = test.variants.reduce((sum, v) => sum + v.impressions, 0);
  const totalConversions = test.variants.reduce((sum, v) => sum + v.conversions, 0);
  const overallConversionRate = totalImpressions > 0
    ? ((totalConversions / totalImpressions) * 100).toFixed(2)
    : "0.00";

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gray-700 rounded-lg">
                <TestTypeIcon type={test.testType} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">{test.name}</h2>
                <p className="text-sm text-gray-400">{test.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {totalImpressions.toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">Total Impressions</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {totalConversions.toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">Total Conversions</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {overallConversionRate}%
              </div>
              <div className="text-sm text-gray-400">Overall Conv. Rate</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {test.statisticalSignificance !== null
                  ? `${test.statisticalSignificance}%`
                  : "—"}
              </div>
              <div className="text-sm text-gray-400">Significance</div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-white mb-4">
              Variant Performance
            </h3>
            <VariantComparison variants={test.variants} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">
                Test Configuration
              </h4>
              <div className="bg-gray-700 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Test Type</span>
                  <span className="text-white capitalize">
                    {test.testType.replace("_", " ")}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Target Audience</span>
                  <span className="text-white">{test.targetAudience}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Winning Criteria</span>
                  <span className="text-white capitalize">
                    {test.winningCriteria.replace("_", " ")}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Confidence Level</span>
                  <span className="text-white">{test.confidenceLevel}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Traffic Split</span>
                  <span className="text-white">
                    {test.trafficSplit.join(" / ")}%
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Timeline</h4>
              <div className="bg-gray-700 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Created</span>
                  <span className="text-white">
                    {new Date(test.createdAt).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Started</span>
                  <span className="text-white">
                    {test.startDate
                      ? new Date(test.startDate).toLocaleString()
                      : "Not started"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Ended</span>
                  <span className="text-white">
                    {test.endDate
                      ? new Date(test.endDate).toLocaleString()
                      : test.status === "running"
                      ? "In progress"
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status</span>
                  <StatusBadge status={test.status} />
                </div>
              </div>
            </div>
          </div>

          {test.status === "completed" && (
            <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
              <h4 className="text-green-300 font-medium mb-2">Test Result</h4>
              {test.variants.find((v) => v.isWinner) ? (
                <p className="text-gray-300">
                  <span className="font-semibold text-green-300">
                    {test.variants.find((v) => v.isWinner)?.name}
                  </span>{" "}
                  is the winner with a conversion rate of{" "}
                  <span className="font-semibold text-green-300">
                    {test.variants.find((v) => v.isWinner)?.conversionRate}%
                  </span>
                  , outperforming the control by{" "}
                  <span className="font-semibold text-green-300">
                    {(
                      ((test.variants.find((v) => v.isWinner)?.conversionRate || 0) /
                        (test.variants.find((v) => v.isControl)?.conversionRate || 1) -
                        1) *
                      100
                    ).toFixed(1)}
                    %
                  </span>
                  .
                </p>
              ) : (
                <p className="text-gray-300">
                  No statistically significant winner was determined.
                </p>
              )}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TestingPage() {
  const [activeTab, setActiveTab] = useState<TabType>("active");
  const [tests, setTests] = useState<ABTest[]>(mockTests);
  const [testTypeFilter, setTestTypeFilter] = useState<TestType | "all">("all");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTest, setSelectedTest] = useState<ABTest | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const filteredTests = tests.filter((test) => {
    const statusMatch =
      (activeTab === "active" && test.status === "running") ||
      (activeTab === "completed" && test.status === "completed") ||
      (activeTab === "draft" && test.status === "draft");

    const typeMatch =
      testTypeFilter === "all" || test.testType === testTypeFilter;

    return statusMatch && typeMatch;
  });

  const handleCreateTest = (testData: Partial<ABTest>) => {
    const newTest: ABTest = {
      id: `test-${Date.now()}`,
      name: testData.name || "New Test",
      description: testData.description || "",
      testType: testData.testType || "content",
      status: "draft",
      variants: [
        {
          id: "v1",
          name: "Control",
          content: "",
          impressions: 0,
          conversions: 0,
          conversionRate: 0,
          isControl: true,
        },
        {
          id: "v2",
          name: "Variant A",
          content: "",
          impressions: 0,
          conversions: 0,
          conversionRate: 0,
          isControl: false,
        },
      ],
      targetAudience: testData.targetAudience || "",
      trafficSplit: [50, 50],
      startDate: null,
      endDate: null,
      winningCriteria: testData.winningCriteria || "conversion_rate",
      confidenceLevel: testData.confidenceLevel || 95,
      statisticalSignificance: null,
      createdAt: new Date().toISOString(),
    };

    setTests([newTest, ...tests]);
    setActiveTab("draft");
  };

  const handleStartTest = (testId: string) => {
    setTests(
      tests.map((t) =>
        t.id === testId
          ? { ...t, status: "running" as TestStatus, startDate: new Date().toISOString() }
          : t
      )
    );
  };

  const handleEndTest = (testId: string) => {
    setTests(
      tests.map((t) => {
        if (t.id !== testId) return t;

        // Simulate determining a winner
        const updatedVariants = t.variants.map((v) => ({
          ...v,
          isWinner:
            v.conversionRate === Math.max(...t.variants.map((x) => x.conversionRate)),
        }));

        return {
          ...t,
          status: "completed" as TestStatus,
          endDate: new Date().toISOString(),
          variants: updatedVariants,
          statisticalSignificance: 95 + Math.floor(Math.random() * 5),
        };
      })
    );
  };

  const handleViewTest = (test: ABTest) => {
    setSelectedTest(test);
    setIsDetailModalOpen(true);
  };

  const tabs: { key: TabType; label: string; count: number }[] = [
    {
      key: "active",
      label: "Active Tests",
      count: tests.filter((t) => t.status === "running").length,
    },
    {
      key: "completed",
      label: "Completed",
      count: tests.filter((t) => t.status === "completed").length,
    },
    {
      key: "draft",
      label: "Drafts",
      count: tests.filter((t) => t.status === "draft").length,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">A/B Testing</h1>
              <p className="text-sm text-gray-400">
                Create and analyze experiments to optimize your content
              </p>
            </div>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
            >
              <span>+</span>
              <span>Create Test</span>
            </button>
          </div>
        </div>
      </header>

      {/* Tabs & Filters */}
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === tab.key
                    ? "bg-gray-700 text-white"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {tab.label}
                <span
                  className={`px-1.5 py-0.5 rounded text-xs ${
                    activeTab === tab.key ? "bg-gray-600" : "bg-gray-700"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          <select
            value={testTypeFilter}
            onChange={(e) =>
              setTestTypeFilter(e.target.value as TestType | "all")
            }
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Types</option>
            <option value="content">Content</option>
            <option value="subject_line">Subject Line</option>
            <option value="send_time">Send Time</option>
            <option value="audience">Audience</option>
          </select>
        </div>

        {/* Stats Summary */}
        {activeTab === "active" && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Active Tests</div>
              <div className="text-2xl font-bold text-white">
                {tests.filter((t) => t.status === "running").length}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Total Impressions</div>
              <div className="text-2xl font-bold text-white">
                {tests
                  .filter((t) => t.status === "running")
                  .reduce(
                    (sum, t) =>
                      sum + t.variants.reduce((s, v) => s + v.impressions, 0),
                    0
                  )
                  .toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Avg. Conversion Rate</div>
              <div className="text-2xl font-bold text-white">
                {(
                  tests
                    .filter((t) => t.status === "running")
                    .reduce(
                      (sum, t) =>
                        sum +
                        t.variants.reduce((s, v) => s + v.conversionRate, 0) /
                          t.variants.length,
                      0
                    ) / Math.max(tests.filter((t) => t.status === "running").length, 1)
                ).toFixed(2)}
                %
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400">Tests Reaching 95%</div>
              <div className="text-2xl font-bold text-white">
                {
                  tests.filter(
                    (t) =>
                      t.status === "running" &&
                      t.statisticalSignificance !== null &&
                      t.statisticalSignificance >= 95
                  ).length
                }
              </div>
            </div>
          </div>
        )}

        {/* Test List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          </div>
        ) : filteredTests.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🧪</div>
            <h3 className="text-lg font-medium text-gray-300">No tests found</h3>
            <p className="text-gray-500 mt-1">
              {activeTab === "draft"
                ? "Create a new test to get started"
                : activeTab === "active"
                ? "No active tests running"
                : "No completed tests yet"}
            </p>
            {activeTab === "draft" && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Create Your First Test
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTests.map((test) => (
              <TestCard
                key={test.id}
                test={test}
                onView={() => handleViewTest(test)}
                onStart={() => handleStartTest(test.id)}
                onEnd={() => handleEndTest(test.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Test Modal */}
      <CreateTestModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreateTest}
      />

      {/* Test Detail Modal */}
      <TestDetailModal
        test={selectedTest}
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedTest(null);
        }}
      />
    </div>
  );
}
