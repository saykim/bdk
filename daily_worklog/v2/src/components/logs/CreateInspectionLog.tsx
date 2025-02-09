import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Template, InspectionItem, InspectionLog } from '../../types';
import { useStore } from '../../store';

interface CreateInspectionLogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (log: Omit<InspectionLog, 'id' | 'createdAt' | 'updatedAt'>) => void;
}

export function CreateInspectionLog({ isOpen, onClose, onSubmit }: CreateInspectionLogProps) {
  const templates = useStore((state) => state.templates);
  const currentUser = useStore((state) => state.currentUser);
  
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [responses, setResponses] = useState<Record<string, any>>({});
  const [isDraft, setIsDraft] = useState(false);

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find((t) => t.id === templateId);
    if (template) {
      setSelectedTemplate(template);
      // 초기 응답 객체 생성
      const initialResponses: Record<string, any> = {};
      template.items.forEach((item) => {
        initialResponses[item.id] = item.type === 'checkbox' ? false : '';
      });
      setResponses(initialResponses);
    }
  };

  const handleResponseChange = (itemId: string, value: any) => {
    setResponses((prev) => ({
      ...prev,
      [itemId]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate) return;

    const log: Omit<InspectionLog, 'id' | 'createdAt' | 'updatedAt'> = {
      templateId: selectedTemplate.id,
      status: isDraft ? 'draft' : 'submitted',
      responses,
      approvalHistory: selectedTemplate.approvalSteps.map((step) => ({
        ...step,
        status: 'pending',
      })),
      createdBy: currentUser.id,
    };

    onSubmit(log);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">New Inspection Log</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!selectedTemplate ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Template
              </label>
              <select
                onChange={(e) => handleTemplateSelect(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="">Select a template...</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">{selectedTemplate.name}</h3>
                <button
                  type="button"
                  onClick={() => setSelectedTemplate(null)}
                  className="text-sm text-indigo-600 hover:text-indigo-700"
                >
                  Change Template
                </button>
              </div>

              <div className="space-y-4">
                {selectedTemplate.items.map((item) => (
                  <div key={item.id} className="border rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {item.title}
                      {item.required && <span className="text-red-500 ml-1">*</span>}
                    </label>

                    {item.type === 'checkbox' && (
                      <input
                        type="checkbox"
                        checked={responses[item.id] || false}
                        onChange={(e) => handleResponseChange(item.id, e.target.checked)}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        required={item.required}
                      />
                    )}

                    {item.type === 'text' && (
                      <input
                        type="text"
                        value={responses[item.id] || ''}
                        onChange={(e) => handleResponseChange(item.id, e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        required={item.required}
                      />
                    )}

                    {item.type === 'number' && (
                      <input
                        type="number"
                        value={responses[item.id] || ''}
                        onChange={(e) => handleResponseChange(item.id, e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        required={item.required}
                      />
                    )}

                    {item.type === 'select' && item.options && (
                      <select
                        value={responses[item.id] || ''}
                        onChange={(e) => handleResponseChange(item.id, e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        required={item.required}
                      >
                        <option value="">Select an option...</option>
                        {item.options.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            {selectedTemplate && (
              <>
                <button
                  type="submit"
                  onClick={() => setIsDraft(true)}
                  className="px-4 py-2 border border-indigo-300 text-indigo-700 rounded-md hover:bg-indigo-50"
                >
                  Save as Draft
                </button>
                <button
                  type="submit"
                  onClick={() => setIsDraft(false)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Submit
                </button>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
} 