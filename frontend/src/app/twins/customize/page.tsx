"use client";

import { useState, useRef } from "react";
import { User, Palette, Shirt, Scissors, Eye, Sparkles, Loader2, ChevronLeft, ChevronRight, Check, RotateCcw } from "lucide-react";

/**
 * Avatar Customization UI
 * 
 * Advanced editing for AI Twin appearance: hair, clothes, accessories, style
 */

interface AvatarCustomization {
    skinTone: string;
    hairStyle: string;
    hairColor: string;
    eyeColor: string;
    outfit: string;
    accessory: string;
    background: string;
    style: string;
}

const SKIN_TONES = ["#FFDBB4", "#EDB98A", "#D08B5B", "#AE5D29", "#694633", "#3D2314"];
const HAIR_STYLES = ["short", "medium", "long", "curly", "wavy", "braided", "bald", "ponytail"];
const HAIR_COLORS = ["#090806", "#2C222B", "#71635A", "#B7A69E", "#D6C4C2", "#CABFAD", "#DA680F", "#FCEF95"];
const EYE_COLORS = ["#634E34", "#2E536F", "#3D671D", "#497665", "#8B4513", "#000000"];
const OUTFITS = ["casual", "business", "formal", "sporty", "creative", "minimalist"];
const ACCESSORIES = ["none", "glasses", "earrings", "necklace", "hat", "scarf"];
const BACKGROUNDS = ["studio", "office", "outdoor", "abstract", "gradient", "transparent"];
const STYLES = ["realistic", "artistic", "cartoon", "3d-render", "vintage", "minimalist"];

const DEFAULT_CUSTOMIZATION: AvatarCustomization = {
    skinTone: SKIN_TONES[0],
    hairStyle: HAIR_STYLES[0],
    hairColor: HAIR_COLORS[0],
    eyeColor: EYE_COLORS[0],
    outfit: OUTFITS[0],
    accessory: ACCESSORIES[0],
    background: BACKGROUNDS[0],
    style: STYLES[0],
};

export default function AvatarCustomizationPage() {
    const [customization, setCustomization] = useState<AvatarCustomization>(DEFAULT_CUSTOMIZATION);
    const [activeTab, setActiveTab] = useState<keyof AvatarCustomization>("skinTone");
    const [generating, setGenerating] = useState(false);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [history, setHistory] = useState<AvatarCustomization[]>([]);
    const historyIndex = useRef(0);

    const tabs: { key: keyof AvatarCustomization; label: string; icon: React.ReactNode }[] = [
        { key: "skinTone", label: "Skin", icon: <User className="w-4 h-4" /> },
        { key: "hairStyle", label: "Hair", icon: <Scissors className="w-4 h-4" /> },
        { key: "hairColor", label: "Hair Color", icon: <Palette className="w-4 h-4" /> },
        { key: "eyeColor", label: "Eyes", icon: <Eye className="w-4 h-4" /> },
        { key: "outfit", label: "Outfit", icon: <Shirt className="w-4 h-4" /> },
        { key: "accessory", label: "Accessory", icon: <Sparkles className="w-4 h-4" /> },
        { key: "background", label: "Background", icon: <Palette className="w-4 h-4" /> },
        { key: "style", label: "Style", icon: <Sparkles className="w-4 h-4" /> },
    ];

    const updateCustomization = (key: keyof AvatarCustomization, value: string) => {
        const newCustomization = { ...customization, [key]: value };
        setCustomization(newCustomization);
        // Add to history
        setHistory(prev => [...prev.slice(0, historyIndex.current + 1), newCustomization]);
        historyIndex.current++;
    };

    const handleUndo = () => {
        if (historyIndex.current > 0) {
            historyIndex.current--;
            setCustomization(history[historyIndex.current]);
        }
    };

    const handleReset = () => {
        setCustomization(DEFAULT_CUSTOMIZATION);
        setHistory([DEFAULT_CUSTOMIZATION]);
        historyIndex.current = 0;
    };

    const handleGeneratePreview = async () => {
        setGenerating(true);
        try {
            // Simulate API call for preview generation
            await new Promise(resolve => setTimeout(resolve, 2500));
            setPreviewUrl("/api/placeholder/400/400");
        } catch (err) {
            console.error("Preview generation failed");
        } finally {
            setGenerating(false);
        }
    };

    const handleSave = async () => {
        setGenerating(true);
        try {
            const response = await fetch("/api/v1/twins/customize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({ customization }),
            });
            if (response.ok) {
                alert("Avatar customization saved!");
            }
        } catch (err) {
            alert("Failed to save customization");
        } finally {
            setGenerating(false);
        }
    };

    const getOptionsForTab = (tab: keyof AvatarCustomization) => {
        switch (tab) {
            case "skinTone": return SKIN_TONES;
            case "hairStyle": return HAIR_STYLES;
            case "hairColor": return HAIR_COLORS;
            case "eyeColor": return EYE_COLORS;
            case "outfit": return OUTFITS;
            case "accessory": return ACCESSORIES;
            case "background": return BACKGROUNDS;
            case "style": return STYLES;
            default: return [];
        }
    };

    const isColorOption = (tab: keyof AvatarCustomization) =>
        ["skinTone", "hairColor", "eyeColor"].includes(tab);

    return (
        <main className="min-h-screen bg-black text-white">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800 px-4 py-4">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">Avatar Customization</h1>
                        <p className="text-sm text-gray-400">Personalize your AI Twin&apos;s appearance</p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={handleUndo}
                            disabled={historyIndex.current === 0}
                            className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 disabled:opacity-50"
                            aria-label="Undo"
                        >
                            <RotateCcw className="w-5 h-5" />
                        </button>
                        <button
                            onClick={handleReset}
                            className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                        >
                            Reset
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={generating}
                            className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                        >
                            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                            Save
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-4">
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Preview Panel */}
                    <div className="bg-gray-900 rounded-2xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Preview</h2>
                        <div className="aspect-square bg-gray-800 rounded-xl flex items-center justify-center overflow-hidden">
                            {previewUrl ? (
                                <img src={previewUrl} alt="Avatar preview" className="w-full h-full object-cover" />
                            ) : (
                                <div className="text-center p-8">
                                    <User className="w-24 h-24 mx-auto text-gray-600 mb-4" />
                                    <p className="text-gray-500 mb-4">No preview generated yet</p>
                                    <button
                                        onClick={handleGeneratePreview}
                                        disabled={generating}
                                        className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 mx-auto"
                                    >
                                        {generating ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <Sparkles className="w-4 h-4" />
                                        )}
                                        Generate Preview
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Current Settings Summary */}
                        <div className="mt-4 p-4 bg-gray-800 rounded-xl">
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Current Settings</h3>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex items-center gap-2">
                                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: customization.skinTone }} />
                                    <span>Skin</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: customization.hairColor }} />
                                    <span>{customization.hairStyle}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: customization.eyeColor }} />
                                    <span>Eyes</span>
                                </div>
                                <div className="capitalize">{customization.outfit}</div>
                                <div className="capitalize">{customization.accessory}</div>
                                <div className="capitalize">{customization.style}</div>
                            </div>
                        </div>
                    </div>

                    {/* Customization Panel */}
                    <div className="bg-gray-900 rounded-2xl p-6">
                        {/* Tabs */}
                        <div className="flex gap-1 mb-6 overflow-x-auto pb-2 scrollbar-hide">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.key}
                                    onClick={() => setActiveTab(tab.key)}
                                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${activeTab === tab.key
                                        ? "bg-purple-600 text-white"
                                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                                        }`}
                                >
                                    {tab.icon}
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Options Grid */}
                        <div className="mb-6">
                            <h3 className="font-medium mb-4 capitalize">{activeTab.replace(/([A-Z])/g, ' $1').trim()}</h3>

                            {isColorOption(activeTab) ? (
                                <div className="flex flex-wrap gap-3">
                                    {getOptionsForTab(activeTab).map((option) => (
                                        <button
                                            key={option}
                                            onClick={() => updateCustomization(activeTab, option)}
                                            className={`w-12 h-12 rounded-full transition-all ${customization[activeTab] === option
                                                ? "ring-4 ring-purple-500 ring-offset-2 ring-offset-gray-900 scale-110"
                                                : "hover:scale-105"
                                                }`}
                                            style={{ backgroundColor: option }}
                                            aria-label={`Select color ${option}`}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 gap-3">
                                    {getOptionsForTab(activeTab).map((option) => (
                                        <button
                                            key={option}
                                            onClick={() => updateCustomization(activeTab, option)}
                                            className={`p-4 rounded-xl text-left transition-all ${customization[activeTab] === option
                                                ? "bg-purple-600 ring-2 ring-purple-400"
                                                : "bg-gray-800 hover:bg-gray-700"
                                                }`}
                                        >
                                            <span className="capitalize">{option}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Navigation */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={() => {
                                    const currentIndex = tabs.findIndex(t => t.key === activeTab);
                                    if (currentIndex > 0) setActiveTab(tabs[currentIndex - 1].key);
                                }}
                                disabled={activeTab === tabs[0].key}
                                className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 disabled:opacity-50"
                            >
                                <ChevronLeft className="w-4 h-4" />
                                Previous
                            </button>
                            <button
                                onClick={() => {
                                    const currentIndex = tabs.findIndex(t => t.key === activeTab);
                                    if (currentIndex < tabs.length - 1) setActiveTab(tabs[currentIndex + 1].key);
                                }}
                                disabled={activeTab === tabs[tabs.length - 1].key}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50"
                            >
                                Next
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
