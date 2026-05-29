'use client';

/**
 * 90-Day Transformation Roadmap
 * 
 * Visual roadmap with milestones and progress tracking.
 */

import { useState } from 'react';
import { Map, CheckCircle2, Circle, ChevronRight, Target, Flame, Trophy, Calendar } from 'lucide-react';

interface Milestone {
    id: string;
    week: number;
    title: string;
    description: string;
    status: 'completed' | 'current' | 'upcoming';
    tasks: {
        id: string;
        title: string;
        completed: boolean;
    }[];
}

interface TransformationRoadmapProps {
    goal: string;
    startDate: string;
    milestones: Milestone[];
    currentWeek: number;
    onTaskToggle?: (milestoneId: string, taskId: string) => void;
    className?: string;
}

export function TransformationRoadmap({
    goal,
    startDate,
    milestones,
    currentWeek,
    onTaskToggle,
    className = '',
}: TransformationRoadmapProps) {
    const [expandedMilestone, setExpandedMilestone] = useState<string | null>(
        milestones.find(m => m.status === 'current')?.id || null
    );

    const totalWeeks = 13; // 90 days ≈ 13 weeks
    const progressPercent = Math.min((currentWeek / totalWeeks) * 100, 100);
    const completedMilestones = milestones.filter(m => m.status === 'completed').length;

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="p-6 border-b dark:border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <Map className="h-6 w-6 text-indigo-500" />
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                90-Day Transformation
                            </h2>
                            <p className="text-sm text-gray-300">{goal}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-indigo-600">Week {currentWeek}</div>
                        <div className="text-sm text-gray-300">of {totalWeeks}</div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="relative">
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                            style={{ width: `${progressPercent}%` }}
                        />
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-gray-300">
                        <span>{new Date(startDate).toLocaleDateString()}</span>
                        <span>{completedMilestones} of {milestones.length} milestones</span>
                        <span>
                            {new Date(new Date(startDate).getTime() + 90 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                        </span>
                    </div>
                </div>
            </div>

            {/* Timeline */}
            <div className="p-6">
                <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

                    {/* Milestones */}
                    <div className="space-y-4">
                        {milestones.map((milestone, index) => (
                            <div key={milestone.id} className="relative">
                                {/* Milestone marker */}
                                <div className={`
                  absolute left-0 w-10 h-10 rounded-full flex items-center justify-center
                  ${milestone.status === 'completed'
                                        ? 'bg-green-500'
                                        : milestone.status === 'current'
                                            ? 'bg-indigo-500 ring-4 ring-indigo-100 dark:ring-indigo-900'
                                            : 'bg-gray-300 dark:bg-gray-600'
                                    }
                `}>
                                    {milestone.status === 'completed' ? (
                                        <CheckCircle2 className="h-5 w-5 text-white" />
                                    ) : milestone.status === 'current' ? (
                                        <Flame className="h-5 w-5 text-white" />
                                    ) : (
                                        <Circle className="h-5 w-5 text-gray-300" />
                                    )}
                                </div>

                                {/* Milestone content */}
                                <div className="ml-14">
                                    <button
                                        onClick={() => setExpandedMilestone(
                                            expandedMilestone === milestone.id ? null : milestone.id
                                        )}
                                        className={`
                      w-full text-left p-4 rounded-lg transition-colors
                      ${milestone.status === 'current'
                                                ? 'bg-indigo-50 dark:bg-indigo-900/20'
                                                : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                                            }
                    `}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-300">Week {milestone.week}</span>
                                                    {milestone.status === 'current' && (
                                                        <span className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 text-xs rounded-full">
                                                            Current
                                                        </span>
                                                    )}
                                                </div>
                                                <h3 className={`font-medium mt-1 ${milestone.status === 'completed'
                                                        ? 'text-gray-300 line-through'
                                                        : 'text-gray-900 dark:text-white'
                                                    }`}>
                                                    {milestone.title}
                                                </h3>
                                                <p className="text-sm text-gray-300 mt-1">{milestone.description}</p>
                                            </div>
                                            <ChevronRight className={`h-5 w-5 text-gray-200 transition-transform ${expandedMilestone === milestone.id ? 'rotate-90' : ''
                                                }`} />
                                        </div>

                                        {/* Task progress */}
                                        <div className="flex items-center gap-2 mt-2">
                                            <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-green-500 rounded-full"
                                                    style={{
                                                        width: `${(milestone.tasks.filter(t => t.completed).length / milestone.tasks.length) * 100}%`
                                                    }}
                                                />
                                            </div>
                                            <span className="text-xs text-gray-300">
                                                {milestone.tasks.filter(t => t.completed).length}/{milestone.tasks.length}
                                            </span>
                                        </div>
                                    </button>

                                    {/* Expanded tasks */}
                                    {expandedMilestone === milestone.id && (
                                        <div className="mt-2 ml-4 space-y-2">
                                            {milestone.tasks.map((task) => (
                                                <label
                                                    key={task.id}
                                                    className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={task.completed}
                                                        onChange={() => onTaskToggle?.(milestone.id, task.id)}
                                                        className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className={`text-sm ${task.completed
                                                            ? 'text-gray-300 line-through'
                                                            : 'text-gray-700 dark:text-gray-300'
                                                        }`}>
                                                        {task.title}
                                                    </span>
                                                </label>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Motivational Footer */}
            {currentWeek <= totalWeeks && (
                <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-b-xl">
                    <div className="flex items-center justify-between text-white">
                        <div className="flex items-center gap-2">
                            <Trophy className="h-5 w-5" />
                            <span className="font-medium">
                                {totalWeeks - currentWeek} weeks to go!
                            </span>
                        </div>
                        <Target className="h-5 w-5 opacity-75" />
                    </div>
                </div>
            )}
        </div>
    );
}

export default TransformationRoadmap;
