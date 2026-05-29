'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { IntakeQuestion } from './IntakeQuestion';
import { ContradictionBanner } from './ContradictionBanner';
import { VerificationChecklist } from './VerificationChecklist';

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

interface Section {
    id: string;
    title: string;
    description?: string;
    icon?: string;
    questions: Question[];
}

interface IntakeFlow {
    flow_id: string;
    title: string;
    description?: string;
    sections: Section[];
    estimated_minutes: number;
}

interface Answer {
    question_id: string;
    value: any;
    is_unsure: boolean;
    confidence: number;
    source: string;
}

interface IntakeWizardProps {
    flowId?: string;
    onComplete?: () => void;
}

export function IntakeWizard({ flowId = 'creator_onboarding_v1', onComplete }: IntakeWizardProps) {
    const router = useRouter();
    const [flow, setFlow] = useState<IntakeFlow | null>(null);
    const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, Answer>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [contradictions, setContradictions] = useState<any[]>([]);
    const [completedSections, setCompletedSections] = useState<string[]>([]);

    // Fetch intake flow on mount
    useEffect(() => {
        fetchFlow();
    }, [flowId]);

    const fetchFlow = async () => {
        try {
            setIsLoading(true);
            const response = await fetch(`/api/v1/intake/flow?flow_id=${flowId}`, {
                headers: { Authorization: 'Bearer ' + (typeof localStorage !== 'undefined' ? (localStorage.getItem('access_token') || '') : '') },
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to load onboarding flow');
            }

            const data = await response.json();
            setFlow(data.flow);

            if (data.progress) {
                setCompletedSections(data.progress.completed_sections || []);
                // Find current section index
                const sectionIndex = data.flow.sections.findIndex(
                    (s: Section) => s.id === data.progress.current_section
                );
                if (sectionIndex >= 0) {
                    setCurrentSectionIndex(sectionIndex);
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load');
        } finally {
            setIsLoading(false);
        }
    };

    const currentSection = flow?.sections[currentSectionIndex];
    const isFirstSection = currentSectionIndex === 0;
    const isLastSection = currentSectionIndex === (flow?.sections.length ?? 1) - 1;
    const progress = flow ? ((currentSectionIndex + 1) / flow.sections.length) * 100 : 0;

    const handleAnswerChange = (questionId: string, value: any, isUnsure: boolean = false) => {
        setAnswers(prev => ({
            ...prev,
            [questionId]: {
                question_id: questionId,
                value,
                is_unsure: isUnsure,
                confidence: isUnsure ? 0.5 : 1.0,
                source: 'user_input',
            },
        }));
    };

    const handleNext = async () => {
        if (!currentSection) return;

        setIsSubmitting(true);
        setError(null);

        try {
            // Prepare answers for current section
            const sectionAnswers = currentSection.questions
                .map(q => answers[q.id])
                .filter(Boolean);

            // Submit to API
            const response = await fetch('/api/v1/intake/response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    section_id: currentSection.id,
                    answers: sectionAnswers,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save answers');
            }

            const result = await response.json();

            // Update contradictions if any
            if (result.contradictions_detected > 0) {
                fetchContradictions();
            }

            // Move to next section or complete
            if (isLastSection) {
                await completeIntake();
            } else {
                setCompletedSections(prev => [...prev, currentSection.id]);
                setCurrentSectionIndex(prev => prev + 1);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleBack = () => {
        if (!isFirstSection) {
            setCurrentSectionIndex(prev => prev - 1);
        }
    };

    const fetchContradictions = async () => {
        try {
            const response = await fetch('/api/v1/intake/contradictions', {
                credentials: 'include',
            });
            if (response.ok) {
                const data = await response.json();
                setContradictions(data.contradictions);
            }
        } catch (err) {
            console.error('Failed to fetch contradictions:', err);
        }
    };

    const completeIntake = async () => {
        try {
            const response = await fetch('/api/v1/intake/complete', {
                method: 'POST',
                credentials: 'include',
            });

            if (response.ok) {
                onComplete?.();
                router.push('/');
            }
        } catch (err) {
            setError('Failed to complete onboarding');
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (!flow || !currentSection) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <h2 className="text-xl font-semibold text-gray-900">Unable to load onboarding</h2>
                    <p className="text-gray-200 mt-2">{error || 'Please try again later'}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
            <div className="max-w-2xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                        {flow.title}
                    </h1>
                    {flow.description && (
                        <p className="text-gray-200 mt-2">{flow.description}</p>
                    )}
                    <p className="text-sm text-gray-300 mt-1">
                        ~{flow.estimated_minutes} minutes
                    </p>
                </div>

                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex justify-between text-sm text-gray-200 mb-2">
                        <span>Step {currentSectionIndex + 1} of {flow.sections.length}</span>
                        <span>{Math.round(progress)}% complete</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                {/* Contradiction Banner */}
                {contradictions.length > 0 && (
                    <ContradictionBanner
                        contradictions={contradictions}
                        onResolve={() => fetchContradictions()}
                    />
                )}

                {/* Section Card */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
                    {/* Section Header */}
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-gray-900">
                            {currentSection.title}
                        </h2>
                        {currentSection.description && (
                            <p className="text-gray-200 mt-1">{currentSection.description}</p>
                        )}
                    </div>

                    {/* Questions */}
                    <div className="space-y-6">
                        {currentSection.questions.map(question => (
                            <IntakeQuestion
                                key={question.id}
                                question={question}
                                value={answers[question.id]?.value}
                                isUnsure={answers[question.id]?.is_unsure || false}
                                onChange={(value, isUnsure) => handleAnswerChange(question.id, value, isUnsure)}
                            />
                        ))}
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
                        <button
                            onClick={handleBack}
                            disabled={isFirstSection}
                            className={`px-6 py-3 rounded-lg font-medium transition-colors ${isFirstSection
                                    ? 'text-gray-200 cursor-not-allowed'
                                    : 'text-gray-700 hover:bg-gray-100'
                                }`}
                        >
                            Back
                        </button>

                        <button
                            onClick={handleNext}
                            disabled={isSubmitting}
                            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-80 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? (
                                <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Saving...
                                </span>
                            ) : isLastSection ? (
                                'Complete Setup'
                            ) : (
                                'Continue'
                            )}
                        </button>
                    </div>
                </div>

                {/* Section Navigation Dots */}
                <div className="flex justify-center mt-6 space-x-2">
                    {flow.sections.map((section, index) => (
                        <button
                            key={section.id}
                            onClick={() => completedSections.includes(section.id) && setCurrentSectionIndex(index)}
                            className={`w-3 h-3 rounded-full transition-colors ${index === currentSectionIndex
                                    ? 'bg-purple-600'
                                    : completedSections.includes(section.id)
                                        ? 'bg-purple-300 hover:bg-purple-400 cursor-pointer'
                                        : 'bg-gray-300'
                                }`}
                            title={section.title}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
