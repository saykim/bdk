export interface Template {
  id: string;
  name: string;
  description: string;
  items: InspectionItem[];
  approvalSteps: ApprovalStep[];
  createdAt: Date;
  updatedAt: Date;
}

export interface InspectionItem {
  id: string;
  title: string;
  type: 'checkbox' | 'text' | 'number' | 'select';
  options?: string[];
  required: boolean;
}

export interface ApprovalStep {
  id: string;
  level: number;
  approverRole: string;
  status: 'pending' | 'approved' | 'rejected';
  comment?: string;
  approvedAt?: Date;
}

export interface InspectionLog {
  id: string;
  templateId: string;
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected';
  responses: Record<string, any>;
  approvalHistory: ApprovalStep[];
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}