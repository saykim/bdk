import React from 'react';
import { ClipboardList, Eye, Trash2 } from 'lucide-react';
import { InspectionLog, Template } from '../../types';
import { useStore } from '../../store';

interface InspectionLogListProps {
  logs: InspectionLog[];
  onDelete: (id: string) => void;
  onView: (log: InspectionLog) => void;
}

export function InspectionLogList({ logs, onDelete, onView }: InspectionLogListProps) {
  const templates = useStore((state) => state.templates);

  const getTemplateName = (templateId: string) => {
    const template = templates.find((t) => t.id === templateId);
    return template?.name || 'Unknown Template';
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'submitted':
        return 'bg-blue-100 text-blue-800';
      case 'in_review':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (logs.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No inspection logs available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {logs.map((log) => (
        <div
          key={log.id}
          className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ClipboardList className="w-5 h-5 text-indigo-600" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {getTemplateName(log.templateId)}
                </h3>
                <p className="text-sm text-gray-500">
                  Created by {log.createdBy} • {new Date(log.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(log.status)}`}>
                {log.status.replace('_', ' ').toUpperCase()}
              </span>
              <button
                onClick={() => onView(log)}
                className="text-indigo-600 hover:text-indigo-700"
              >
                <Eye className="w-5 h-5" />
              </button>
              <button
                onClick={() => onDelete(log.id)}
                className="text-red-500 hover:text-red-700"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-sm text-gray-600">
              {Object.keys(log.responses).length} responses • 
              {log.approvalHistory.filter((step) => step.status === 'approved').length} of {log.approvalHistory.length} approvals
            </p>
          </div>
        </div>
      ))}
    </div>
  );
} 