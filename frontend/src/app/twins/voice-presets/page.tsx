"use client";

import { useState, useRef, useEffect } from "react";
import { Play, Pause, Volume2, Mic, Loader2, Plus, Trash2, Check, Star, Wand2 } from "lucide-react";

/**
 * Voice Presets UI
 * 
 * Pre-configured voice styles for AI Twin speech synthesis
 */

interface VoicePreset {
    id: string;
    name: string;
    description: string;
    category: "professional" | "casual" | "character" | "custom";
    settings: VoiceSettings;
    isDefault?: boolean;
    isFavorite?: boolean;
    sampleUrl?: string;
}

interface VoiceSettings {
    pitch: number;        // -50 to 50
    speed: number;        // 0.5 to 2.0
    stability: number;    // 0 to 100
    clarity: number;      // 0 to 100
    expressiveness: number; // 0 to 100
}

const DEFAULT_SETTINGS: VoiceSettings = {
    pitch: 0,
    speed: 1.0,
    stability: 75,
    clarity: 75,
    expressiveness: 50,
};

const PRESET_LIBRARY: VoicePreset[] = [
    {
        id: "professional",
        name: "Professional",
        description: "Clear, authoritative voice for business content",
        category: "professional",
        settings: { pitch: 0, speed: 0.95, stability: 85, clarity: 90, expressiveness: 40 },
        isDefault: true,
    },
    {
        id: "friendly",
        name: "Friendly",
        description: "Warm, approachable tone for casual content",
        category: "casual",
        settings: { pitch: 5, speed: 1.0, stability: 70, clarity: 75, expressiveness: 65 },
    },
    {
        id: "energetic",
        name: "Energetic",
        description: "High-energy voice for promotional content",
        category: "casual",
        settings: { pitch: 10, speed: 1.15, stability: 65, clarity: 80, expressiveness: 85 },
    },
    {
        id: "calm",
        name: "Calm & Soothing",
        description: "Relaxed voice for meditation or educational content",
        category: "professional",
        settings: { pitch: -5, speed: 0.85, stability: 90, clarity: 70, expressiveness: 30 },
    },
    {
        id: "storyteller",
        name: "Storyteller",
        description: "Engaging voice with dramatic flair",
        category: "character",
        settings: { pitch: 0, speed: 0.9, stability: 60, clarity: 80, expressiveness: 90 },
    },
    {
        id: "news-anchor",
        name: "News Anchor",
        description: "Formal, neutral delivery for informative content",
        category: "professional",
        settings: { pitch: -3, speed: 1.0, stability: 95, clarity: 95, expressiveness: 25 },
    },
];

export default function VoicePresetsPage() {
    const [presets, setPresets] = useState<VoicePreset[]>(PRESET_LIBRARY);
    const [selectedPreset, setSelectedPreset] = useState<VoicePreset | null>(null);
    const [customSettings, setCustomSettings] = useState<VoiceSettings>(DEFAULT_SETTINGS);
    const [playing, setPlaying] = useState<string | null>(null);
    const [filter, setFilter] = useState<"all" | VoicePreset["category"]>("all");
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [generating, setGenerating] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);

    const filteredPresets = presets.filter(p => filter === "all" || p.category === filter);

    const handlePlaySample = async (preset: VoicePreset) => {
        if (playing === preset.id) {
            audioRef.current?.pause();
            setPlaying(null);
            return;
        }

        setPlaying(preset.id);
        setGenerating(true);

        try {
            // Simulate generating sample audio
            await new Promise(resolve => setTimeout(resolve, 1500));
            // In production, this would fetch actual audio
            setGenerating(false);
            // Auto-stop after a few seconds (simulating playback)
            setTimeout(() => setPlaying(null), 3000);
        } catch (err) {
            setPlaying(null);
            setGenerating(false);
        }
    };

    const handleSelectPreset = (preset: VoicePreset) => {
        setSelectedPreset(preset);
        setCustomSettings(preset.settings);
    };

    const handleToggleFavorite = (presetId: string) => {
        setPresets(prev => prev.map(p =>
            p.id === presetId ? { ...p, isFavorite: !p.isFavorite } : p
        ));
    };

    const handleApplyPreset = async () => {
        if (!selectedPreset) return;

        setGenerating(true);
        try {
            await fetch("/api/v1/twins/voice-preset", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    presetId: selectedPreset.id,
                    settings: customSettings,
                }),
            });
            alert("Voice preset applied!");
        } catch (err) {
            alert("Failed to apply preset");
        } finally {
            setGenerating(false);
        }
    };

    const handleCreateCustom = (name: string) => {
        const newPreset: VoicePreset = {
            id: `custom-${Date.now()}`,
            name,
            description: "Custom voice preset",
            category: "custom",
            settings: customSettings,
        };
        setPresets(prev => [...prev, newPreset]);
        setShowCreateModal(false);
        setSelectedPreset(newPreset);
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Voice Presets</h1>
                        <p className="text-gray-400">Choose or customize your AI Twin's voice</p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        Create Custom
                    </button>
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {(["all", "professional", "casual", "character", "custom"] as const).map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap ${filter === f ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                    {/* Preset List */}
                    <div className="md:col-span-2 space-y-4">
                        {filteredPresets.length === 0 ? (
                            <div className="bg-gray-900 rounded-xl p-8 text-center">
                                <Mic className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                                <p className="text-gray-500">No presets in this category</p>
                            </div>
                        ) : (
                            filteredPresets.map((preset) => (
                                <div
                                    key={preset.id}
                                    onClick={() => handleSelectPreset(preset)}
                                    className={`bg-gray-900 rounded-xl p-5 cursor-pointer transition-all ${selectedPreset?.id === preset.id
                                            ? "ring-2 ring-purple-500"
                                            : "hover:bg-gray-800/50"
                                        }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${preset.category === "professional" ? "bg-blue-600/20 text-blue-400" :
                                                    preset.category === "casual" ? "bg-green-600/20 text-green-400" :
                                                        preset.category === "character" ? "bg-purple-600/20 text-purple-400" :
                                                            "bg-gray-600/20 text-gray-400"
                                                }`}>
                                                <Mic className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <h3 className="font-semibold">{preset.name}</h3>
                                                    {preset.isDefault && (
                                                        <span className="text-xs bg-purple-600 px-2 py-0.5 rounded">Default</span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-400">{preset.description}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleToggleFavorite(preset.id); }}
                                                className={`p-2 rounded-lg ${preset.isFavorite ? "text-yellow-400" : "text-gray-500 hover:text-gray-300"}`}
                                            >
                                                <Star className={`w-5 h-5 ${preset.isFavorite ? "fill-current" : ""}`} />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handlePlaySample(preset); }}
                                                disabled={generating && playing === preset.id}
                                                className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                                            >
                                                {generating && playing === preset.id ? (
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                ) : playing === preset.id ? (
                                                    <Pause className="w-5 h-5" />
                                                ) : (
                                                    <Play className="w-5 h-5" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Settings Panel */}
                    <div className="bg-gray-900 rounded-2xl p-6">
                        <h2 className="text-lg font-semibold mb-4">
                            {selectedPreset ? `Customize: ${selectedPreset.name}` : "Select a Preset"}
                        </h2>

                        {selectedPreset ? (
                            <>
                                {/* Sliders */}
                                <div className="space-y-5">
                                    <SliderControl
                                        label="Pitch"
                                        value={customSettings.pitch}
                                        min={-50}
                                        max={50}
                                        onChange={(v) => setCustomSettings(prev => ({ ...prev, pitch: v }))}
                                        unit=""
                                    />
                                    <SliderControl
                                        label="Speed"
                                        value={customSettings.speed}
                                        min={0.5}
                                        max={2}
                                        step={0.05}
                                        onChange={(v) => setCustomSettings(prev => ({ ...prev, speed: v }))}
                                        unit="x"
                                    />
                                    <SliderControl
                                        label="Stability"
                                        value={customSettings.stability}
                                        min={0}
                                        max={100}
                                        onChange={(v) => setCustomSettings(prev => ({ ...prev, stability: v }))}
                                        unit="%"
                                    />
                                    <SliderControl
                                        label="Clarity"
                                        value={customSettings.clarity}
                                        min={0}
                                        max={100}
                                        onChange={(v) => setCustomSettings(prev => ({ ...prev, clarity: v }))}
                                        unit="%"
                                    />
                                    <SliderControl
                                        label="Expressiveness"
                                        value={customSettings.expressiveness}
                                        min={0}
                                        max={100}
                                        onChange={(v) => setCustomSettings(prev => ({ ...prev, expressiveness: v }))}
                                        unit="%"
                                    />
                                </div>

                                {/* Actions */}
                                <div className="flex gap-3 mt-6">
                                    <button
                                        onClick={() => setCustomSettings(selectedPreset.settings)}
                                        className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700"
                                    >
                                        Reset
                                    </button>
                                    <button
                                        onClick={handleApplyPreset}
                                        disabled={generating}
                                        className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                                        Apply
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="text-center py-8">
                                <Wand2 className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                                <p className="text-gray-500">Select a preset to customize</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Create Custom Modal */}
                {showCreateModal && (
                    <CreatePresetModal
                        onClose={() => setShowCreateModal(false)}
                        onCreate={handleCreateCustom}
                    />
                )}

                <audio ref={audioRef} />
            </div>
        </main>
    );
}

function SliderControl({
    label,
    value,
    min,
    max,
    step = 1,
    unit,
    onChange,
}: {
    label: string;
    value: number;
    min: number;
    max: number;
    step?: number;
    unit: string;
    onChange: (value: number) => void;
}) {
    return (
        <div>
            <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">{label}</span>
                <span>{value.toFixed(step < 1 ? 2 : 0)}{unit}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
            />
        </div>
    );
}

function CreatePresetModal({ onClose, onCreate }: { onClose: () => void; onCreate: (name: string) => void }) {
    const [name, setName] = useState("");

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-4">Create Custom Preset</h2>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Preset name"
                    className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none mb-4"
                    autoFocus
                />
                <div className="flex gap-4">
                    <button onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                        Cancel
                    </button>
                    <button
                        onClick={() => onCreate(name)}
                        disabled={!name}
                        className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50"
                    >
                        Create
                    </button>
                </div>
            </div>
        </div>
    );
}
