import React, { useState } from 'react';
import { FileText, ClipboardList, CheckSquare, BarChart3 } from 'lucide-react';
import { CreateTemplateModal } from './components/templates/CreateTemplateModal';
import { EditTemplateModal } from './components/templates/EditTemplateModal';
import { TemplateList } from './components/templates/TemplateList';
import { CreateInspectionLog } from './components/logs/CreateInspectionLog';
import { InspectionLogList } from './components/logs/InspectionLogList';
import { ApprovalModal } from './components/approvals/ApprovalModal';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { Template, InspectionLog } from './types';
import { useStore } from './store';

function App() {
  const [activeTab, setActiveTab] = useState('templates');
  const [isCreateTemplateModalOpen, setIsCreateTemplateModalOpen] = useState(false);
  const [isEditTemplateModalOpen, setIsEditTemplateModalOpen] = useState(false);
  const [isCreateLogModalOpen, setIsCreateLogModalOpen] = useState(false);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [selectedLog, setSelectedLog] = useState<InspectionLog | null>(null);

  // Zustand store hooks
  const {
    templates,
    addTemplate,
    updateTemplate,
    deleteTemplate,
    inspectionLogs,
    addInspectionLog,
    deleteInspectionLog,
    currentUser,
  } = useStore();

  const handleCreateTemplate = (templateData: Omit<Template, 'id' | 'createdAt' | 'updatedAt' | 'approvalSteps'>) => {
    const newTemplate: Template = {
      ...templateData,
      id: crypto.randomUUID(),
      approvalSteps: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    addTemplate(newTemplate);
  };

  const handleEditTemplate = (templateData: Partial<Template>) => {
    if (!selectedTemplate) return;
    updateTemplate(selectedTemplate.id, templateData);
    setSelectedTemplate(null);
  };

  const handleCreateLog = (logData: Omit<InspectionLog, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newLog: InspectionLog = {
      ...logData,
      id: crypto.randomUUID(),
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    addInspectionLog(newLog);
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
    setIsEditTemplateModalOpen(true);
  };

  const handleLogSelect = (log: InspectionLog) => {
    setSelectedLog(log);
    setIsApprovalModalOpen(true);
  };

  const pendingApprovals = inspectionLogs.filter(log => {
    if (log.status !== 'submitted' && log.status !== 'in_review') return false;
    return log.approvalHistory.some(
      step => step.status === 'pending' && step.approverRole === currentUser.role
    );
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-2xl font-bold text-gray-900">Daily Inspection System</h1>
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('templates')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'templates'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <FileText className="w-5 h-5" />
                <span>Templates</span>
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'logs'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <ClipboardList className="w-5 h-5" />
                <span>Inspection Logs</span>
              </button>
              <button
                onClick={() => setActiveTab('approvals')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'approvals'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <CheckSquare className="w-5 h-5" />
                <span>Approvals</span>
                {pendingApprovals.length > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-xs">
                    {pendingApprovals.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('analytics')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'analytics'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <BarChart3 className="w-5 h-5" />
                <span>Analytics</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'templates' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Inspection Templates</h2>
                <button 
                  onClick={() => setIsCreateTemplateModalOpen(true)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  Create Template
                </button>
              </div>
              <TemplateList
                templates={templates}
                onDelete={deleteTemplate}
                onSelect={handleTemplateSelect}
              />
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Inspection Logs</h2>
                <button 
                  onClick={() => setIsCreateLogModalOpen(true)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  New Inspection
                </button>
              </div>
              <InspectionLogList
                logs={inspectionLogs}
                onDelete={deleteInspectionLog}
                onView={handleLogSelect}
              />
            </div>
          )}

          {activeTab === 'approvals' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Pending Approvals</h2>
              <InspectionLogList
                logs={pendingApprovals}
                onDelete={deleteInspectionLog}
                onView={handleLogSelect}
              />
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Analytics & Reports</h2>
              <AnalyticsView />
            </div>
          )}
        </div>
      </main>

      <CreateTemplateModal
        isOpen={isCreateTemplateModalOpen}
        onClose={() => setIsCreateTemplateModalOpen(false)}
        onSubmit={handleCreateTemplate}
      />

      {selectedTemplate && (
        <EditTemplateModal
          isOpen={isEditTemplateModalOpen}
          onClose={() => {
            setIsEditTemplateModalOpen(false);
            setSelectedTemplate(null);
          }}
          onSubmit={handleEditTemplate}
          template={selectedTemplate}
        />
      )}

      <CreateInspectionLog
        isOpen={isCreateLogModalOpen}
        onClose={() => setIsCreateLogModalOpen(false)}
        onSubmit={handleCreateLog}
      />

      {selectedLog && (
        <ApprovalModal
          isOpen={isApprovalModalOpen}
          onClose={() => {
            setIsApprovalModalOpen(false);
            setSelectedLog(null);
          }}
          log={selectedLog}
        />
      )}
    </div>
  );
}

export default App;