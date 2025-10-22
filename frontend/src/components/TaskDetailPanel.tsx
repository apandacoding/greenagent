import ReactMarkdown from 'react-markdown';
import type { TaskDetail } from '../types/evaluation';

interface TaskDetailPanelProps {
  taskDetail: TaskDetail;
}

export default function TaskDetailPanel({ taskDetail }: TaskDetailPanelProps) {
  return (
    <div className="space-y-6">
      {/* Task ID Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
        <span>🆔</span>
        <span>{taskDetail.taskId}</span>
      </div>

      {/* Task Name */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Task Name</h3>
        <div className="text-2xl font-bold text-green-700">{taskDetail.taskName}</div>
      </div>

      {/* Title */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Title</h3>
        <div className="text-xl text-gray-800">{taskDetail.title}</div>
      </div>

      {/* Full Description */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Full Description</h3>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{taskDetail.fullDescription}</ReactMarkdown>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div className="pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Characters:</span>
            <span className="ml-2 font-medium text-gray-900">
              {taskDetail.fullDescription.length}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Words:</span>
            <span className="ml-2 font-medium text-gray-900">
              {taskDetail.fullDescription.split(/\s+/).length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

