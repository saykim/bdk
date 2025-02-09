import { InspectionLog, Template } from '../types';

export function exportToExcel(logs: InspectionLog[], templates: Template[]) {
  // CSV 형식으로 데이터 변환
  const rows = [
    // 헤더
    [
      '점검일',
      '템플릿명',
      '작성자',
      '상태',
      '승인단계',
      '항목수',
      '최종수정일',
    ].join(','),
    // 데이터 행
    ...logs.map(log => {
      const template = templates.find(t => t.id === log.templateId);
      const approvedSteps = log.approvalHistory.filter(step => step.status === 'approved').length;
      const totalSteps = log.approvalHistory.length;
      
      return [
        new Date(log.createdAt).toLocaleDateString(),
        template?.name || '',
        log.createdBy,
        log.status,
        `${approvedSteps}/${totalSteps}`,
        Object.keys(log.responses).length,
        new Date(log.updatedAt).toLocaleDateString(),
      ].join(',');
    }),
  ].join('\n');

  // CSV 파일 생성 및 다운로드
  const blob = new Blob(['\ufeff' + rows], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `inspection_logs_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
} 