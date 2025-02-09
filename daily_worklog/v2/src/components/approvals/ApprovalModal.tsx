import React, { useState } from 'react';
import { X } from 'lucide-react';
import { InspectionLog, Template } from '../../types';
import { useStore } from '../../store';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  log: InspectionLog;
}

export function ApprovalModal({ isOpen, onClose, log }: ApprovalModalProps) {
  const templates = useStore((state) => state.templates);
  const currentUser = useStore((state) => state.currentUser);
  const updateInspectionLog = useStore((state) => state.updateInspectionLog);
  
  const [comment, setComment] = useState('');
  const template = templates.find(t => t.id === log.templateId);
  
  const currentStep = log.approvalHistory.find(
    step => step.status === 'pending' && step.approverRole === currentUser.role
  );

  const handleApprove = () => {
    if (!currentStep) return;

    const updatedHistory = log.approvalHistory.map(step =>
      step.id === currentStep.id
        ? { ...step, status: 'approved', comment, approvedAt: new Date() }
        : step
    );

    const nextStep = log.approvalHistory.find(
      step => step.status === 'pending' && step.level > currentStep.level
    );

    updateInspectionLog(log.id, {
      approvalHistory: updatedHistory,
      status: nextStep ? 'in_review' : 'approved',
    });

    onClose();
  };

  const handleReject = () => {
    if (!currentStep) return;

    const updatedHistory = log.approvalHistory.map(step =>
      step.id === currentStep.id
        ? { ...step, status: 'rejected', comment, approvedAt: new Date() }
        : step
    );

    updateInspectionLog(log.id, {
      approvalHistory: updatedHistory,
      status: 'rejected',
    });

    onClose();
  };

  if (!isOpen || !template || !currentStep) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Review Inspection Log</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium">{template.name}</h3>
            <p className="text-sm text-gray-500">{template.description}</p>
          </div>

          <div className="space-y-4">
            {template.items.map((item) => (
              <div key={item.id} className="border rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700">
                  {item.title}
                  {item.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                <div className="mt-1">
                  {item.type === 'checkbox' ? (
                    <input
                      type="checkbox"
                      checked={log.responses[item.id] || false}
                      disabled
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                  ) : item.type === 'select' ? (
                    <div className="text-gray-700">{log.responses[item.id]}</div>
                  ) : (
                    <div className="text-gray-700">{log.responses[item.id]}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Approval History</h3>
            <div className="space-y-2">
              {log.approvalHistory.map((step) => (
                <div
                  key={step.id}
                  className={`p-2 rounded ${
                    step.status === 'approved'
                      ? 'bg-green-50'
                      : step.status === 'rejected'
                      ? 'bg-red-50'
                      : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Level {step.level}: {step.approverRole}</span>
                    <span
                      className={`text-sm ${
                        step.status === 'approved'
                          ? 'text-green-600'
                          : step.status === 'rejected'
                          ? 'text-red-600'
                          : 'text-gray-500'
                      }`}
                    >
                      {step.status.toUpperCase()}
                    </span>
                  </div>
                  {step.comment && (
                    <p className="text-sm text-gray-600 mt-1">{step.comment}</p>
                  )}
                  {step.approvedAt && (
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(step.approvedAt).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comment
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              rows={3}
              placeholder="Add your review comments here..."
            />
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleReject}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Reject
            </button>
            <button
              type="button"
              onClick={handleApprove}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Approve
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 