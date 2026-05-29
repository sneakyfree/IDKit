'use client';

import { useState } from 'react';

interface Question {
    id: string;
    type: string;
    label: string;
    description?: string;
    placeholder?: string;
    required?: boolean;
    options?: string[];
    allow_unsure?: boolean;
    help_text?: string;
    tooltip?: string;
}

interface IntakeQuestionProps {
    question: Question;
    value: any;
    isUnsure: boolean;
    onChange: (value: any, isUnsure: boolean) => void;
}

export function IntakeQuestion({ question, value, isUnsure, onChange }: IntakeQuestionProps) {
    const [showTooltip, setShowTooltip] = useState(false);

    const renderInput = () => {
        switch (question.type) {
            case 'text':
                return (
                    <input
                        type="text"
                        value={value || ''}
                        onChange={(e) => onChange(e.target.value, false)}
                        placeholder={question.placeholder}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    />
                );

            case 'number':
                return (
                    <input
                        type="number"
                        value={value || ''}
                        onChange={(e) => onChange(e.target.valueAsNumber || null, false)}
                        placeholder={question.placeholder || '0'}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    />
                );

            case 'currency':
                return (
                    <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                        <input
                            type="number"
                            value={value || ''}
                            onChange={(e) => onChange(e.target.valueAsNumber || null, false)}
                            placeholder="0"
                            className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                        />
                    </div>
                );

            case 'percent':
                return (
                    <div className="relative">
                        <input
                            type="number"
                            value={value || ''}
                            onChange={(e) => onChange(e.target.valueAsNumber || null, false)}
                            placeholder="0"
                            min={0}
                            max={100}
                            step={0.1}
                            className="w-full pr-10 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">%</span>
                    </div>
                );

            case 'select':
                return (
                    <select aria-label="Filter or select option"
                        value={value || ''}
                        onChange={(e) => onChange(e.target.value, false)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all bg-white"
                    >
                        <option value="">Select an option...</option>
                        {question.options?.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                );

            case 'multi_select':
                return (
                    <div className="space-y-2">
                        {question.options?.map((option) => {
                            const selected = Array.isArray(value) && value.includes(option);
                            return (
                                <label
                                    key={option}
                                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${selected
                                        ? 'border-purple-500 bg-purple-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected}
                                        onChange={() => {
                                            const current = Array.isArray(value) ? value : [];
                                            const updated = selected
                                                ? current.filter((v) => v !== option)
                                                : [...current, option];
                                            onChange(updated, false);
                                        }}
                                        className="sr-only"
                                    />
                                    <span
                                        className={`w-5 h-5 rounded border mr-3 flex items-center justify-center ${selected
                                            ? 'bg-purple-500 border-purple-500'
                                            : 'border-gray-300'
                                            }`}
                                    >
                                        {selected && (
                                            <svg
                                                className="w-3 h-3 text-white"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={3}
                                                    d="M5 13l4 4L19 7"
                                                />
                                            </svg>
                                        )}
                                    </span>
                                    <span className="text-gray-700">{option}</span>
                                </label>
                            );
                        })}
                    </div>
                );

            case 'boolean':
                return (
                    <div className="flex space-x-4">
                        <button
                            type="button"
                            onClick={() => onChange(true, false)}
                            className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${value === true
                                ? 'bg-purple-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Yes
                        </button>
                        <button
                            type="button"
                            onClick={() => onChange(false, false)}
                            className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${value === false
                                ? 'bg-purple-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            No
                        </button>
                    </div>
                );

            case 'oauth_connect':
                return (
                    <div className="space-y-3">
                        {['YouTube', 'Instagram', 'TikTok', 'Twitter'].map((platform) => (
                            <button
                                key={platform}
                                type="button"
                                className="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all"
                            >
                                <span className="font-medium text-gray-700">Connect {platform}</span>
                                <span className="text-purple-600">Connect →</span>
                            </button>
                        ))}
                        <p className="text-sm text-gray-500 text-center mt-2">
                            You can skip this and connect accounts later
                        </p>
                    </div>
                );

            default:
                return (
                    <input
                        type="text"
                        value={value || ''}
                        onChange={(e) => onChange(e.target.value, false)}
                        placeholder={question.placeholder}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    />
                );
        }
    };

    return (
        <div className="space-y-2">
            {/* Label */}
            <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-900">
                    {question.label}
                    {question.required && <span className="text-red-500 ml-1">*</span>}
                </label>

                {question.tooltip && (
                    <button
                        type="button"
                        onMouseEnter={() => setShowTooltip(true)}
                        onMouseLeave={() => setShowTooltip(false)}
                        className="text-gray-600 hover:text-gray-600 relative"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                        {showTooltip && (
                            <div className="absolute right-0 bottom-full mb-2 w-64 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-lg z-10">
                                {question.tooltip}
                                <div className="absolute right-3 top-full w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-gray-900" />
                            </div>
                        )}
                    </button>
                )}
            </div>

            {/* Description */}
            {question.description && (
                <p className="text-sm text-gray-500">{question.description}</p>
            )}

            {/* Input */}
            <div className={isUnsure ? 'opacity-80' : ''}>
                {renderInput()}
            </div>

            {/* Help Text */}
            {question.help_text && (
                <p className="text-sm text-gray-600">{question.help_text}</p>
            )}

            {/* I'm Not Sure Option */}
            {question.allow_unsure !== false && (
                <label className="flex items-center mt-2 text-sm text-gray-600 cursor-pointer group">
                    <input
                        type="checkbox"
                        checked={isUnsure}
                        onChange={(e) => onChange(value, e.target.checked)}
                        className="mr-2 rounded border-gray-300 text-purple-500 focus:ring-purple-500"
                    />
                    <span className="group-hover:text-gray-900 transition-colors">
                        I&apos;m not sure about this
                    </span>
                </label>
            )}
        </div>
    );
}
