import React from 'react';
import { Download, Calendar } from 'lucide-react';
import { useStore } from '../../store';
import { exportToExcel } from '../../utils/excel';

export function AnalyticsView() {
  const {
    inspectionLogs,
    templates,
    dateRange,
    setDateRange,
  } = useStore();

  const filteredLogs = inspectionLogs.filter(log => {
    if (!dateRange.startDate && !dateRange.endDate) return true;
    
    const logDate = new Date(log.createdAt).getTime();
    const start = dateRange.startDate ? new Date(dateRange.startDate).getTime() : -Infinity;
    const end = dateRange.endDate ? new Date(dateRange.endDate).getTime() : Infinity;
    
    return logDate >= start && logDate <= end;
  });

  // 템플릿별 통계
  const templateStats = templates.map(template => {
    const templateLogs = filteredLogs.filter(log => log.templateId === template.id);
    const approved = templateLogs.filter(log => log.status === 'approved').length;
    const rejected = templateLogs.filter(log => log.status === 'rejected').length;
    const pending = templateLogs.filter(log => 
      log.status === 'submitted' || log.status === 'in_review'
    ).length;

    return {
      template,
      total: templateLogs.length,
      approved,
      rejected,
      pending,
    };
  });

  // 일별 통계
  const dailyStats = filteredLogs.reduce((acc, log) => {
    const date = new Date(log.createdAt).toLocaleDateString();
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-8">
      {/* 기간 필터 */}
      <div className="flex items-center space-x-4">
        <Calendar className="w-5 h-5 text-gray-500" />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">시작일</label>
            <input
              type="date"
              value={dateRange.startDate || ''}
              onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">종료일</label>
            <input
              type="date"
              value={dateRange.endDate || ''}
              onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
        </div>
        <button
          onClick={() => setDateRange({ startDate: null, endDate: null })}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          초기화
        </button>
        <button
          onClick={() => exportToExcel(filteredLogs, templates)}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          <Download className="w-4 h-4" />
          <span>엑셀 다운로드</span>
        </button>
      </div>

      {/* 요약 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900">전체 점검</h3>
          <p className="text-3xl font-bold text-indigo-600 mt-2">
            {filteredLogs.length}
          </p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900">승인 완료</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {filteredLogs.filter(log => log.status === 'approved').length}
          </p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900">승인 대기</h3>
          <p className="text-3xl font-bold text-yellow-600 mt-2">
            {filteredLogs.filter(log => 
              log.status === 'submitted' || log.status === 'in_review'
            ).length}
          </p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900">반려</h3>
          <p className="text-3xl font-bold text-red-600 mt-2">
            {filteredLogs.filter(log => log.status === 'rejected').length}
          </p>
        </div>
      </div>

      {/* 템플릿별 통계 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">템플릿별 통계</h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  템플릿명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  전체
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  승인
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  대기
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  반려
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {templateStats.map(({ template, total, approved, rejected, pending }) => (
                <tr key={template.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {template.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {total}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                    {approved}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600">
                    {pending}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                    {rejected}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 일별 통계 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">일별 점검 현황</h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  날짜
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  점검 수
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(dailyStats)
                .sort((a, b) => new Date(b[0]).getTime() - new Date(a[0]).getTime())
                .map(([date, count]) => (
                  <tr key={date}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {count}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 