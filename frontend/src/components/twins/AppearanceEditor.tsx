"use client";

import { useState } from "react";
import {
    Sun,
    Moon,
    Camera,
    Smile,
    Shirt,
    Palette,
    RotateCcw,
    Save,
    Loader2,
    Sparkles,
} from "lucide-react";

/**
 * Avatar Appearance Editor
 *
 * Visual controls for lighting, background, clothing, expression, and camera angle.
 * Closes Helix Scan gap T08-2.
 */

const LIGHTING_PRESETS = [
    { id: "studio", label: "Studio", desc: "Balanced, professional" },
    { id: "natural", label: "Natural", desc: "Soft daylight" },
    { id: "dramatic", label: "Dramatic", desc: "High contrast" },
    { id: "warm", label: "Warm", desc: "Golden hour glow" },
    { id: "cool", label: "Cool", desc: "Blue-toned" },
    { id: "neon", label: "Neon", desc: "Cyberpunk vibes" },
];

const BACKGROUNDS = [
    { id: "gradient_purple", label: "Purple Gradient", color: "from-purple-900 to-indigo-900" },
    { id: "gradient_blue", label: "Blue Gradient", color: "from-blue-900 to-cyan-900" },
    { id: "gradient_green", label: "Green Gradient", color: "from-emerald-900 to-teal-900" },
    { id: "solid_black", label: "Black", color: "from-black to-gray-900" },
    { id: "solid_white", label: "White", color: "from-gray-100 to-white" },
    { id: "office", label: "Office", color: "from-amber-900 to-orange-900" },
];

const EXPRESSIONS = [
    { id: "neutral", emoji: "😐", label: "Neutral" },
    { id: "smile", emoji: "😊", label: "Smile" },
    { id: "confident", emoji: "😎", label: "Confident" },
    { id: "thoughtful", emoji: "🤔", label: "Thoughtful" },
    { id: "excited", emoji: "🤩", label: "Excited" },
    { id: "serious", emoji: "😐", label: "Serious" },
];

const CLOTHING = [
    { id: "business", label: "Business" },
    { id: "casual", label: "Casual" },
    { id: "streetwear", label: "Streetwear" },
    { id: "formal", label: "Formal" },
    { id: "creative", label: "Creative" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AppearanceEditorProps {
    twinId: string;
}

export default function AppearanceEditor({ twinId }: AppearanceEditorProps) {
    const [lighting, setLighting] = useState("studio");
    const [background, setBackground] = useState("gradient_purple");
    const [expression, setExpression] = useState("neutral");
    const [clothing, setClothing] = useState("casual");
    const [cameraAngle, setCameraAngle] = useState(0); // -30 to 30
    const [zoom, setZoom] = useState(50); // 0 to 100
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        try {
            await fetch(`${API_BASE}/api/v1/twins/${twinId}/appearance`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    lighting,
                    background,
                    expression_preset: expression,
                    clothing_style: clothing,
                    camera_angle: cameraAngle,
                    zoom_level: zoom,
                }),
            });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch {
            // silent
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        setLighting("studio");
        setBackground("gradient_purple");
        setExpression("neutral");
        setClothing("casual");
        setCameraAngle(0);
        setZoom(50);
    };

    const bgPreset = BACKGROUNDS.find((b) => b.id === background);

    return (
        <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
            {/* Preview Area */}
            <div className={`relative h-64 bg-gradient-to-br ${bgPreset?.color || "from-purple-900 to-indigo-900"} flex items-center justify-center`}>
                <div className="w-32 h-32 rounded-full bg-gray-800/50 border-2 border-white/20 flex items-center justify-center text-5xl"
                    style={{ transform: `rotateY(${cameraAngle}deg) scale(${0.8 + zoom / 250})` }}
                >
                    {EXPRESSIONS.find((e) => e.id === expression)?.emoji || "😐"}
                </div>
                <div className="absolute bottom-3 left-3 flex items-center gap-1.5 px-2 py-1 bg-black/40 rounded text-xs text-white/70">
                    <Camera className="w-3 h-3" />
                    {lighting} · {cameraAngle}°
                </div>
            </div>

            {/* Controls */}
            <div className="p-5 space-y-5">
                {/* Lighting */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                        <Sun className="w-4 h-4 text-yellow-400" /> Lighting
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                        {LIGHTING_PRESETS.map((l) => (
                            <button
                                key={l.id}
                                onClick={() => setLighting(l.id)}
                                className={`p-2 rounded-lg border text-left text-xs transition-colors ${lighting === l.id
                                        ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                        : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                                    }`}
                            >
                                <p className="font-medium">{l.label}</p>
                                <p className="text-gray-500 mt-0.5">{l.desc}</p>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Background */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                        <Palette className="w-4 h-4 text-blue-400" /> Background
                    </label>
                    <div className="flex gap-2">
                        {BACKGROUNDS.map((b) => (
                            <button
                                key={b.id}
                                onClick={() => setBackground(b.id)}
                                className={`w-10 h-10 rounded-full bg-gradient-to-br ${b.color} border-2 transition-all ${background === b.id ? "border-white scale-110" : "border-transparent hover:border-gray-600"
                                    }`}
                                title={b.label}
                            />
                        ))}
                    </div>
                </div>

                {/* Expression */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                        <Smile className="w-4 h-4 text-green-400" /> Expression
                    </label>
                    <div className="flex gap-2">
                        {EXPRESSIONS.map((e) => (
                            <button
                                key={e.id}
                                onClick={() => setExpression(e.id)}
                                className={`w-12 h-12 rounded-xl border text-xl flex items-center justify-center transition-all ${expression === e.id
                                        ? "border-purple-500 bg-purple-500/10 scale-110"
                                        : "border-gray-700 bg-gray-800 hover:border-gray-600"
                                    }`}
                                title={e.label}
                            >
                                {e.emoji}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Clothing */}
                <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                        <Shirt className="w-4 h-4 text-pink-400" /> Clothing Style
                    </label>
                    <div className="flex gap-2 flex-wrap">
                        {CLOTHING.map((c) => (
                            <button
                                key={c.id}
                                onClick={() => setClothing(c.id)}
                                className={`px-3 py-1.5 rounded-lg border text-sm transition-colors ${clothing === c.id
                                        ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                        : "border-gray-700 bg-gray-800 text-gray-400"
                                    }`}
                            >
                                {c.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Camera Angle & Zoom Sliders */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                            <Camera className="w-4 h-4 text-orange-400" /> Camera Angle
                        </label>
                        <input
                            type="range"
                            min={-30}
                            max={30}
                            value={cameraAngle}
                            onChange={(e) => setCameraAngle(parseInt(e.target.value))}
                            className="w-full accent-purple-500"
                        />
                        <div className="flex justify-between text-xs text-gray-600">
                            <span>-30°</span>
                            <span>{cameraAngle}°</span>
                            <span>30°</span>
                        </div>
                    </div>
                    <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                            <Sparkles className="w-4 h-4 text-cyan-400" /> Zoom
                        </label>
                        <input
                            type="range"
                            min={0}
                            max={100}
                            value={zoom}
                            onChange={(e) => setZoom(parseInt(e.target.value))}
                            className="w-full accent-purple-500"
                        />
                        <div className="flex justify-between text-xs text-gray-600">
                            <span>Wide</span>
                            <span>{zoom}%</span>
                            <span>Close</span>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-2">
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 text-sm"
                    >
                        <RotateCcw className="w-4 h-4" /> Reset
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50 text-sm"
                    >
                        {saving ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : saved ? (
                            <><Sparkles className="w-4 h-4" /> Saved!</>
                        ) : (
                            <><Save className="w-4 h-4" /> Save Appearance</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
