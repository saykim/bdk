import React from 'react';
import { Template } from '../../types';
import { FileText, Trash2 } from 'lucide-react';

interface TemplateListProps {
  templates: Template[];
  onDelete: (id: string) => void;
  onSelect: (template: Template) => void;
}

export function TemplateList({ templates, onDelete, onSelect }: TemplateListProps) {
  if (templates.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No templates created yet
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {templates.map((template) => (
        <div
          key={template.id}
          className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-indigo-600" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                <p className="text-sm text-gray-500">{template.description}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => onSelect(template)}
                className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
              >
                View Details
              </button>
              <button
                onClick={() => onDelete(template.id)}
                className="text-red-500 hover:text-red-700"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-sm text-gray-600">
              {template.items.length} items • Created {new Date(template.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
} 