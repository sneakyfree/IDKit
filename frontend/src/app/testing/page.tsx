"use client";

import { useState, useEffect } from "react";
import { Plus, BarChart3, CheckCircle, XCircle, Loader2, TrendingUp, Users, Percent } from "lucide-react";
import { testing } from "@/lib/api";

/**
 * TASK 5.1.3: A/B Testing UI
 * 
 * Create and manage A/B tests for content variations
 */

interface ABTest {
  id: string;
  name: string;
  metric: "clicks" | "conversions" | "engagement" | "views";
  status: "draft" | "running" | "completed" | "paused";
  variations: Variation[];
  trafficSplit: number[];
  startedAt?: string;
  endedAt?: string;
  winner?: string;
  confidence?: number;
}

interface Variation {
  id: string;
  name: string;
  content: string;
  metrics: {
    impressions: number;
    clicks: number;
    conversions: number;
    rate: number;
  };
}


export default function ABTestingPage() {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [filter, setFilter] = useState<"all" | "running" | "completed" | "draft">("all");
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    async function fetchTests() {
      try {
        const response = await testing.list();
        const items = Array.isArray(response) ? response : [];
        setTests(items.map((t) => ({
          id: t.id,
          name: t.name,
          metric: (t.winner_criteria || 'clicks') as ABTest['metric'],
          status: (t.status || 'draft') as ABTest['status'],
          variations: Array.isArray(t.variants) ? t.variants.map((v) => ({
            id: v.id,
            name: v.name,
            content: JSON.stringify(v.content || ''),
            metrics: {
              impressions: 0,
              clicks: 0,
              conversions: 0,
              rate: 0,
            },
          })) : [],
          trafficSplit: [50, 50],
          startedAt: t.started_at || undefined,
          endedAt: t.ended_at || undefined,
          winner: t.winner_variant_id || undefined,
          confidence: t.statistical_significance || undefined,
        })));
      } catch {
        setTests([]);
      } finally {
        setLoading(false);
      }
    }
    fetchTests();
  }, []);

  const filteredTests = tests.filter(t => filter === "all" || t.status === filter);

  return (
    <main className="min-h-screen bg-black text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">A/B Testing</h1>
            <p className="text-gray-400">Test content variations to optimize performance</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
          >
            <Plus className="w-5 h-5" />
            Create Test
          </button>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={<BarChart3 />} label="Active Tests" value={tests.filter(t => t.status === "running").length} />
          <StatCard icon={<CheckCircle />} label="Completed" value={tests.filter(t => t.status === "completed").length} />
          <StatCard icon={<TrendingUp />} label="Avg Lift" value="23%" />
          <StatCard icon={<Users />} label="Total Participants" value="45.2K" />
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          {(["all", "running", "completed", "draft"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm ${filter === f ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredTests.length === 0 && (
          <div className="bg-gray-900 rounded-2xl p-12 text-center">
            <BarChart3 className="w-16 h-16 mx-auto text-gray-600 mb-4" />
            <h3 className="text-lg font-medium mb-2">No tests yet</h3>
            <p className="text-gray-500 mb-6">Create your first A/B test to start optimizing.</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
            >
              <Plus className="w-5 h-5" />
              Create Test
            </button>
          </div>
        )}

        {/* Test List */}
        {!loading && filteredTests.length > 0 && (
          <div className="space-y-6">
            {filteredTests.map((test) => (
              <TestCard key={test.id} test={test} />
            ))}
          </div>
        )}

        {/* Create Modal */}
        {showCreateModal && (
          <CreateTestModal onClose={() => setShowCreateModal(false)} onCreate={(test) => {
            setTests(prev => [...prev, test]);
            setShowCreateModal(false);
          }} />
        )}
      </div>
    </main>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="text-purple-400">{icon}</div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

function TestCard({ test }: { test: ABTest }) {
  const statusColors = {
    draft: "bg-gray-600",
    running: "bg-green-600",
    completed: "bg-blue-600",
    paused: "bg-yellow-600",
  };

  const winningVariation = test.winner ? test.variations.find(v => v.id === test.winner) : null;
  const maxRate = Math.max(...test.variations.map(v => v.metrics.rate));

  return (
    <div className="bg-gray-900 rounded-2xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">{test.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[test.status]}`}>
              {test.status}
            </span>
          </div>
          <p className="text-sm text-gray-500">Measuring: {test.metric}</p>
        </div>
        {test.confidence && (
          <div className="text-right">
            <p className="text-sm text-gray-400">Confidence</p>
            <p className={`text-xl font-bold ${test.confidence >= 95 ? "text-green-400" : "text-yellow-400"}`}>
              {test.confidence}%
            </p>
          </div>
        )}
      </div>

      {/* Variations */}
      <div className="space-y-3">
        {test.variations.map((variation) => (
          <div
            key={variation.id}
            className={`p-4 rounded-xl border ${test.winner === variation.id
              ? "border-green-500 bg-green-500/10"
              : "border-gray-800 bg-gray-800/50"
              }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">{variation.name}</span>
                {test.winner === variation.id && (
                  <span className="text-xs bg-green-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> Winner
                  </span>
                )}
              </div>
              <span className="text-sm text-gray-400">{variation.content}</span>
            </div>

            {/* Progress bar */}
            <div className="relative h-8 bg-gray-700 rounded-lg overflow-hidden">
              <div
                className={`h-full ${test.winner === variation.id ? "bg-green-500" : "bg-purple-500"}`}
                style={{ width: `${(variation.metrics.rate / maxRate) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center justify-between px-3 text-sm">
                <span>{variation.metrics.rate}% rate</span>
                <span className="text-gray-400">
                  {variation.metrics.clicks.toLocaleString()} / {variation.metrics.impressions.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-4">
        {test.status === "running" && (
          <>
            <button className="px-4 py-2 bg-gray-800 rounded-lg text-sm hover:bg-gray-700">Pause</button>
            <button className="px-4 py-2 bg-purple-600 rounded-lg text-sm hover:bg-purple-700">End Test</button>
          </>
        )}
        {test.status === "completed" && winningVariation && (
          <button className="px-4 py-2 bg-green-600 rounded-lg text-sm hover:bg-green-700">
            Apply Winner
          </button>
        )}
        <button className="px-4 py-2 bg-gray-800 rounded-lg text-sm hover:bg-gray-700 ml-auto">
          View Details
        </button>
      </div>
    </div>
  );
}

function CreateTestModal({ onClose, onCreate }: { onClose: () => void; onCreate: (test: ABTest) => void }) {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [metric, setMetric] = useState<ABTest["metric"]>("clicks");
  const [variations, setVariations] = useState([
    { id: "a", name: "Variation A", content: "" },
    { id: "b", name: "Variation B", content: "" },
  ]);
  const [trafficSplit, setTrafficSplit] = useState([50, 50]);

  const handleCreate = () => {
    const newTest: ABTest = {
      id: Date.now().toString(),
      name,
      metric,
      status: "draft",
      variations: variations.map(v => ({
        ...v,
        metrics: { impressions: 0, clicks: 0, conversions: 0, rate: 0 },
      })),
      trafficSplit,
    };
    onCreate(newTest);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-2xl max-w-lg w-full p-6">
        <h2 className="text-xl font-bold mb-6">Create A/B Test</h2>

        {/* Step 1: Name & Metric */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Test Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., CTA Button Color Test"
                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Success Metric</label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value as ABTest["metric"])}
                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
              >
                <option value="clicks">Click-through Rate</option>
                <option value="conversions">Conversion Rate</option>
                <option value="engagement">Engagement Rate</option>
                <option value="views">View Rate</option>
              </select>
            </div>
          </div>
        )}

        {/* Step 2: Variations */}
        {step === 2 && (
          <div className="space-y-4">
            {variations.map((v, i) => (
              <div key={v.id}>
                <label className="block text-sm text-gray-400 mb-1">{v.name}</label>
                <textarea
                  value={v.content}
                  onChange={(e) => {
                    const newVars = [...variations];
                    newVars[i].content = e.target.value;
                    setVariations(newVars);
                  }}
                  placeholder="Enter content for this variation..."
                  className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none min-h-[80px]"
                />
              </div>
            ))}
            {variations.length < 5 && (
              <button
                onClick={() => setVariations([...variations, { id: String.fromCharCode(97 + variations.length), name: `Variation ${String.fromCharCode(65 + variations.length)}`, content: "" }])}
                className="text-purple-400 text-sm hover:text-purple-300"
              >
                + Add Variation
              </button>
            )}
          </div>
        )}

        {/* Step 3: Traffic Split */}
        {step === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-400">Set traffic distribution between variations</p>
            {variations.map((v, i) => (
              <div key={v.id} className="flex items-center gap-4">
                <span className="w-24">{v.name}</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={trafficSplit[i]}
                  onChange={(e) => {
                    const newSplit = [...trafficSplit];
                    const newValue = parseInt(e.target.value);
                    const diff = newValue - newSplit[i];
                    newSplit[i] = newValue;
                    // Adjust other values proportionally
                    const otherIndex = i === 0 ? 1 : 0;
                    newSplit[otherIndex] = Math.max(0, Math.min(100, newSplit[otherIndex] - diff));
                    setTrafficSplit(newSplit);
                  }}
                  className="flex-1"
                />
                <span className="w-12 text-right">{trafficSplit[i]}%</span>
              </div>
            ))}
            <p className="text-xs text-gray-500">Total: {trafficSplit.reduce((a, b) => a + b, 0)}%</p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-4 mt-8">
          <button
            onClick={() => step > 1 ? setStep(step - 1) : onClose()}
            className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700"
          >
            {step > 1 ? "Back" : "Cancel"}
          </button>
          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={step === 1 && !name}
              className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleCreate}
              className="flex-1 py-3 bg-green-600 rounded-xl hover:bg-green-700"
            >
              Create Test
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
