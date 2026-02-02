'use client';

interface VerificationTask {
    task_id: string;
    question_id: string;
    question_label: string;
    current_value: any;
    verification_method: string;
    instructions: string;
    priority: string;
}

interface VerificationChecklistProps {
    tasks: VerificationTask[];
    onComplete?: (taskId: string) => void;
}

export function VerificationChecklist({ tasks, onComplete }: VerificationChecklistProps) {
    if (tasks.length === 0) return null;

    const highPriority = tasks.filter(t => t.priority === 'high');
    const otherTasks = tasks.filter(t => t.priority !== 'high');

    const getMethodIcon = (method: string) => {
        switch (method) {
            case 'oauth_connect':
                return (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                );
            case 'document_upload':
                return (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                );
            default:
                return (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                );
        }
    };

    const getMethodLabel = (method: string) => {
        switch (method) {
            case 'oauth_connect':
                return 'Connect Account';
            case 'document_upload':
                return 'Upload Document';
            case 'manual_confirm':
                return 'Confirm';
            default:
                return 'Verify';
        }
    };

    const renderTask = (task: VerificationTask) => (
        <div
            key={task.task_id}
            className={`p-4 rounded-lg border ${task.priority === 'high'
                    ? 'border-red-200 bg-red-50'
                    : 'border-gray-200 bg-white'
                }`}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{task.question_label}</h4>
                        {task.priority === 'high' && (
                            <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                                High Priority
                            </span>
                        )}
                    </div>

                    <p className="text-sm text-gray-600 mt-1">{task.instructions}</p>

                    {task.current_value && (
                        <p className="text-sm text-gray-500 mt-2">
                            Current value: <span className="font-medium">{formatValue(task.current_value)}</span>
                        </p>
                    )}
                </div>

                <button
                    onClick={() => onComplete?.(task.task_id)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${task.priority === 'high'
                            ? 'bg-red-600 text-white hover:bg-red-700'
                            : 'bg-purple-600 text-white hover:bg-purple-700'
                        }`}
                >
                    {getMethodIcon(task.verification_method)}
                    <span>{getMethodLabel(task.verification_method)}</span>
                </button>
            </div>
        </div>
    );

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mt-6">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                        Verification Checklist
                    </h3>
                    <p className="text-sm text-gray-600">
                        Complete these to improve your profile accuracy
                    </p>
                </div>
                <span className="text-sm px-3 py-1 bg-purple-100 text-purple-700 rounded-full">
                    {tasks.length} pending
                </span>
            </div>

            <div className="space-y-3">
                {/* High priority tasks first */}
                {highPriority.length > 0 && (
                    <div className="space-y-3">
                        {highPriority.map(renderTask)}
                    </div>
                )}

                {/* Other tasks */}
                {otherTasks.length > 0 && (
                    <div className="space-y-3">
                        {highPriority.length > 0 && otherTasks.length > 0 && (
                            <div className="border-t border-gray-100 my-4" />
                        )}
                        {otherTasks.map(renderTask)}
                    </div>
                )}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 text-center">
                    Verifying your information helps us provide more accurate recommendations
                </p>
            </div>
        </div>
    );
}

function formatValue(value: any): string {
    if (value === null || value === undefined) return 'Not set';
    if (typeof value === 'number') {
        return value.toLocaleString();
    }
    if (Array.isArray(value)) {
        return value.join(', ');
    }
    return String(value);
}
