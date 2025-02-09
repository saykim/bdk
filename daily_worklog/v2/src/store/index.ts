import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Template, InspectionLog } from '../types';

interface Store {
  // Templates
  templates: Template[];
  addTemplate: (template: Template) => void;
  updateTemplate: (id: string, template: Partial<Template>) => void;
  deleteTemplate: (id: string) => void;
  
  // Inspection Logs
  inspectionLogs: InspectionLog[];
  addInspectionLog: (log: InspectionLog) => void;
  updateInspectionLog: (id: string, log: Partial<InspectionLog>) => void;
  deleteInspectionLog: (id: string) => void;
  
  // Current User (임시)
  currentUser: {
    id: string;
    name: string;
    role: string;
  };

  // Filters
  dateRange: {
    startDate: string | null;
    endDate: string | null;
  };
  setDateRange: (range: { startDate: string | null; endDate: string | null }) => void;
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      // Templates
      templates: [],
      addTemplate: (template) =>
        set((state) => ({ templates: [...state.templates, template] })),
      updateTemplate: (id, template) =>
        set((state) => ({
          templates: state.templates.map((t) =>
            t.id === id ? { ...t, ...template, updatedAt: new Date() } : t
          ),
        })),
      deleteTemplate: (id) =>
        set((state) => ({
          templates: state.templates.filter((t) => t.id !== id),
        })),

      // Inspection Logs
      inspectionLogs: [],
      addInspectionLog: (log) =>
        set((state) => ({ inspectionLogs: [...state.inspectionLogs, log] })),
      updateInspectionLog: (id, log) =>
        set((state) => ({
          inspectionLogs: state.inspectionLogs.map((l) =>
            l.id === id ? { ...l, ...log, updatedAt: new Date() } : l
          ),
        })),
      deleteInspectionLog: (id) =>
        set((state) => ({
          inspectionLogs: state.inspectionLogs.filter((l) => l.id !== id),
        })),

      // Current User (임시 데이터)
      currentUser: {
        id: 'user1',
        name: '홍길동',
        role: 'inspector',
      },

      // Filters
      dateRange: {
        startDate: null,
        endDate: null,
      },
      setDateRange: (range) => set({ dateRange: range }),
    }),
    {
      name: 'inspection-storage',
    }
  )
); 